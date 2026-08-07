from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RecoveryObservation:
    service: str
    failure_type: str
    environment: str
    desired_replicas: int
    ready_replicas: int
    available_zones: int
    traffic_healthy: bool
    data_healthy: bool
    alerts_resolved: bool


class AutoRecoveryCoordinator:
    """Deterministically selects a recovery lane without executing mutations."""

    def coordinate(self, observation: RecoveryObservation) -> dict[str, Any]:
        required_zones = min(2, observation.desired_replicas)
        if observation.ready_replicas >= observation.desired_replicas and all(
            [observation.traffic_healthy, observation.data_healthy, observation.alerts_resolved]
        ) and observation.available_zones >= required_zones:
            return self._result("healthy", "none", False, [])

        if observation.available_zones < required_zones:
            return self._result(
                "degraded",
                "zone-capacity-restoration",
                False,
                [
                    "Restore replicas in an additional availability zone",
                    "Verify topology spread constraints and available EKS capacity",
                ],
            )

        if observation.failure_type in {"pod", "pod_failure", "pod-delete"}:
            return self._result(
                "recovering",
                "kubernetes-controller",
                False,
                [
                    "Observe Deployment replacement pod scheduling",
                    "Verify readiness and traffic before resolving the incident",
                ],
            )

        if observation.failure_type in {"node", "node_failure", "node-drain"}:
            return self._result(
                "degraded",
                "eks-capacity-and-rescheduling",
                False,
                [
                    "Verify pods reschedule across healthy zones",
                    "Inspect managed node group or Karpenter provisioning events",
                    "Page the platform owner if capacity is not restored",
                ],
            )

        if observation.failure_type in {"database_failure", "postgres", "db"}:
            return self._result(
                "approval_required",
                "database-failover",
                True,
                [
                    "Confirm replica health and recovery point",
                    "Request incident-commander approval for database failover",
                    "Validate application reads and writes after promotion",
                ],
            )

        if observation.failure_type in {"cluster_failure", "region_failure", "regional-dr"}:
            return self._result(
                "approval_required",
                "regional-failover",
                True,
                [
                    "Confirm regional failure using independent health signals",
                    "Request incident-commander approval for traffic shift",
                    "Activate GitOps in the warm standby cluster",
                    "Validate RTO, RPO, data integrity, and customer traffic",
                ],
            )

        return self._result(
            "human_investigation",
            "unclassified",
            True,
            ["Collect additional evidence before selecting a recovery action"],
        )

    @staticmethod
    def _result(
        state: str, lane: str, approval_required: bool, actions: list[str]
    ) -> dict[str, Any]:
        return {
            "state": state,
            "recovery_lane": lane,
            "approval_required": approval_required,
            "recommended_actions": actions,
            "execution": "not_started",
            "safety_boundary": (
                "Kubernetes may replace failed pods automatically. Database, cluster, regional, "
                "and traffic failover require policy, approval, audit, and recovery validation."
            ),
        }
