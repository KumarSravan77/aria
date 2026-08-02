from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RecoveryPlanner:
    """Builds HA/DR recovery plans for a service without executing infrastructure changes.

    This planner is intentionally advisory. Real recovery execution must still go through
    ReBAC, policy validation, approval workflows, and audited automation.
    """

    def plan(self, service: str, failure_type: str = "unknown", environment: str = "prod") -> dict[str, Any]:
        failure = (failure_type or "unknown").lower()
        steps = [
            "Confirm blast radius and affected dependencies",
            "Check service health, endpoints, and recent deployments",
            "Validate replicas, PDB, topology spread, and node distribution",
            "Verify alerts, SLO burn, and customer impact",
        ]

        if failure in {"pod_failure", "pod-delete", "pod"}:
            steps += [
                "Confirm replacement pods are scheduled and ready",
                "Validate PodDisruptionBudget was respected",
                "Check anti-affinity/topology spread across nodes and zones",
            ]
            strategy = "multi-replica pod recovery"
        elif failure in {"node_failure", "node-drain", "node"}:
            steps += [
                "Validate pods rescheduled to healthy nodes",
                "Check Karpenter/Cluster Autoscaler provisioning events",
                "Confirm topology spread across zones after reschedule",
            ]
            strategy = "node-level failover"
        elif failure in {"database_failure", "postgres", "db"}:
            steps += [
                "Check database primary/replica status",
                "Validate latest backup and point-in-time recovery options",
                "Restore to standby if primary is unrecoverable",
                "Run application smoke tests after DB recovery",
            ]
            strategy = "database restore/failover"
        elif failure in {"cluster_failure", "region_failure", "regional-dr"}:
            steps += [
                "Activate GitOps recovery plan in standby cluster",
                "Restore namespace/application data from Velero backup",
                "Shift traffic using DNS/Gateway/Istio failover",
                "Validate RTO/RPO and customer-facing health checks",
            ]
            strategy = "regional disaster recovery"
        else:
            steps += [
                "Select recovery runbook based on confirmed failed component",
                "Use Velero/GitOps/traffic failover only after scope is confirmed",
            ]
            strategy = "general HA recovery"

        return {
            "service": service,
            "environment": environment,
            "failure_type": failure_type,
            "strategy": strategy,
            "recommended_steps": steps,
            "safety_boundary": "Recovery plans are advisory. Execution requires ReBAC, policy validation, approval, and audit logging.",
        }
