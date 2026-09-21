from __future__ import annotations

import time
from typing import Any
from server.healing.kubernetes_actions import KubernetesActions
from server.gitops.argocd_client import ArgoCDClient
from server.config import settings


class ActionExecutor:
    """Deterministic executor for approved actions.

    The LLM can recommend actions, but only this executor can perform mutations
    after policy, ReBAC, approval, and queueing have already succeeded.
    """

    def __init__(self, k8s: KubernetesActions | None = None, argocd: ArgoCDClient | None = None,
                 verification_attempts: int = 6, verification_interval_seconds: float = 5.0):
        self.k8s = k8s or KubernetesActions()
        self.argocd = argocd or ArgoCDClient(base_url=settings.argocd_api_url or "http://localhost:8082", token=settings.argocd_token)
        self.verification_attempts = max(1, verification_attempts)
        self.verification_interval_seconds = max(0, verification_interval_seconds)

    def execute(self, action: str, namespace: str, target: str, replicas: int | None = None, **kwargs: Any) -> dict[str, Any]:
        if action in {"scale_deployment", "restart_deployment"}:
            before = self.k8s.deployment_state(namespace, target)
            mutation = self.k8s.execute(action, namespace, target, replicas=replicas)
            if mutation.get("status") != "ok":
                return {**mutation, "before": before, "verification": {"healthy": False, "reason": "mutation_failed"}}
            verification = self._verify(namespace, target)
            result = {**mutation, "before": before, "verification": verification}
            if verification.get("healthy"):
                return result
            rollback_declared = bool(kwargs.get("rollback"))
            if action == "scale_deployment" and rollback_declared and before.get("available"):
                rollback = self.k8s.scale_deployment(namespace, target, int(before["desired_replicas"]))
                rollback_verification = self._verify(namespace, target)
                return {**result, "status": "rolled_back", "rollback": rollback,
                        "rollback_verification": rollback_verification}
            return {**result, "status": "verification_failed", "requires_escalation": True}
        if action == "argocd_sync":
            return self.argocd.sync_app(target, revision=kwargs.get("revision"), dry_run=False)
        return {"status": "unsupported", "action": action, "target": target, "namespace": namespace}

    def _verify(self, namespace: str, target: str) -> dict[str, Any]:
        latest: dict[str, Any] = {"healthy": False, "reason": "verification_not_run"}
        for attempt in range(1, self.verification_attempts + 1):
            latest = self.k8s.deployment_state(namespace, target)
            latest = {**latest, "attempt": attempt, "attempts_allowed": self.verification_attempts}
            if latest.get("healthy"):
                return latest
            if attempt < self.verification_attempts and self.verification_interval_seconds:
                time.sleep(self.verification_interval_seconds)
        return latest
