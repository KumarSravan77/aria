from __future__ import annotations

from typing import Any


class KedaClient:
    """Boundary for event-driven autoscaling recommendations."""

    def recommend_scaled_object(self, service: str, namespace: str, trigger_type: str = "prometheus") -> dict[str, Any]:
        return {
            "service": service,
            "namespace": namespace,
            "recommendation": "create_or_tune_scaledobject",
            "trigger_type": trigger_type,
            "note": "Use KEDA for event-driven scaling; keep changes GitOps-reviewed before production rollout.",
        }
