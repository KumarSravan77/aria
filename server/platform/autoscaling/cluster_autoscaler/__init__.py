from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class ClusterAutoscalerClient:
    """Cluster Autoscaler status via its metrics/health endpoint."""
    base_url: str = "http://localhost:8085"
    timeout_seconds: int = 5

    def status(self) -> dict[str, Any]:
        try:
            r = requests.get(f"{self.base_url.rstrip('/')}/health-check",
                             timeout=self.timeout_seconds)
            r.raise_for_status()
            return {"available": True, "healthy": True}
        except Exception as exc:
            return {
                "available": False,
                "error": str(exc),
                "message": "Cluster Autoscaler not reachable. Consider Karpenter for modern node autoscaling.",
            }
