from __future__ import annotations

from typing import Any


class RolloutService:
    """Argo Rollouts orchestration boundary.

    This demo exposes dry-run recommendations only. Real promote/abort needs a
    Kubernetes custom-resource client and must be wrapped in policy, ReBAC, and
    approval before it mutates rollout state.
    """

    def promote(self, rollout: str, namespace: str, dry_run: bool = True) -> dict[str, Any]:
        if not dry_run:
            return {
                "available": False,
                "implemented": False,
                "action": "rollout_promote",
                "rollout": rollout,
                "namespace": namespace,
                "dry_run": False,
                "reason": "Real Argo Rollouts promote is not implemented in this demo. Use dry_run=true or add a policy-gated Rollouts executor.",
            }
        return {"available": True, "implemented": True, "action": "rollout_promote", "rollout": rollout, "namespace": namespace, "dry_run": True}

    def abort(self, rollout: str, namespace: str, dry_run: bool = True) -> dict[str, Any]:
        if not dry_run:
            return {
                "available": False,
                "implemented": False,
                "action": "rollout_abort",
                "rollout": rollout,
                "namespace": namespace,
                "dry_run": False,
                "reason": "Real Argo Rollouts abort is not implemented in this demo. Use dry_run=true or add a policy-gated Rollouts executor.",
            }
        return {"available": True, "implemented": True, "action": "rollout_abort", "rollout": rollout, "namespace": namespace, "dry_run": True}
