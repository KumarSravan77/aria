from __future__ import annotations

from typing import Any
from server.healing.kubernetes_actions import KubernetesActions
from server.gitops.argocd_client import ArgoCDClient
from server.config import settings


class ActionExecutor:
    """Deterministic executor for approved actions.

    The LLM can recommend actions, but only this executor can perform mutations
    after policy, ReBAC, approval, and queueing have already succeeded.
    """

    def __init__(self, k8s: KubernetesActions | None = None, argocd: ArgoCDClient | None = None):
        self.k8s = k8s or KubernetesActions()
        self.argocd = argocd or ArgoCDClient(base_url=settings.argocd_api_url or "http://localhost:8082", token=settings.argocd_token)

    def execute(self, action: str, namespace: str, target: str, replicas: int | None = None, **kwargs: Any) -> dict[str, Any]:
        if action in {"scale_deployment", "restart_deployment"}:
            return self.k8s.execute(action, namespace, target, replicas=replicas)
        if action == "argocd_sync":
            return self.argocd.sync_app(target, revision=kwargs.get("revision"), dry_run=False)
        return {"status": "unsupported", "action": action, "target": target, "namespace": namespace}
