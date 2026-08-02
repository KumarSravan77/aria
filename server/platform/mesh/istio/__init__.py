from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class IstioClient:
    """Service mesh traffic, mTLS, and telemetry via Istio control plane."""
    istiod_url: str = "http://localhost:15014"
    timeout_seconds: int = 10

    def mesh_status(self) -> dict[str, Any]:
        try:
            r = requests.get(f"{self.istiod_url.rstrip('/')}/debug/syncz",
                             timeout=self.timeout_seconds)
            r.raise_for_status()
            return {"available": True, "synced_proxies": len(r.json())}
        except Exception as exc:
            return {"available": False, "error": str(exc)}

    def traffic_policy(self, service: str, namespace: str = "demo") -> dict[str, Any]:
        return {
            "available": False,
            "service": service,
            "namespace": namespace,
            "message": "Wire to Istio VirtualService/DestinationRule APIs for live traffic policy.",
            "recommended_action": "Use istioctl or kubectl to inspect VirtualService resources.",
        }
