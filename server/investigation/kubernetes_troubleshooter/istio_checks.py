from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import os
import requests


@dataclass
class IstioDiagnosticClient:
    """Read-only Istio diagnostic boundary. Never mutates mesh resources."""

    istiod_url: str | None = None
    timeout_seconds: float = 3.0

    def __post_init__(self) -> None:
        self.istiod_url = self.istiod_url or os.getenv("ISTIOD_URL", "http://istiod.istio-system:15014")

    def mesh_status(self) -> dict[str, Any]:
        try:
            response = requests.get(f"{self.istiod_url}/debug/syncz", timeout=self.timeout_seconds)
            return {
                "available": response.ok,
                "status_code": response.status_code,
                "source": "istiod/debug/syncz",
                "summary": "Istiod proxy sync status queried",
                "data_preview": response.text[:800],
            }
        except Exception as exc:
            return {
                "available": False,
                "source": "istiod/debug/syncz",
                "error": str(exc),
                "summary": "Istiod sync endpoint unavailable",
            }

    def proxy_config_dump(self, pod: str | None = None, namespace: str | None = None) -> dict[str, Any]:
        if not pod:
            return {"available": False, "reason": "pod_not_provided", "summary": "Proxy config dump requires pod/proxy identity"}
        proxy_id = f"{pod}.{namespace or 'default'}" if namespace else pod
        try:
            response = requests.get(
                f"{self.istiod_url}/debug/config_dump",
                params={"proxyID": proxy_id},
                timeout=self.timeout_seconds,
            )
            return {
                "available": response.ok,
                "status_code": response.status_code,
                "source": "istiod/debug/config_dump",
                "proxy_id": proxy_id,
                "summary": "Istio proxy config dump queried",
                "data_preview": response.text[:1200],
            }
        except Exception as exc:
            return {
                "available": False,
                "source": "istiod/debug/config_dump",
                "proxy_id": proxy_id,
                "error": str(exc),
                "summary": "Istio proxy config dump unavailable",
            }

    def traffic_policy(self, service: str, namespace: str = "default") -> dict[str, Any]:
        return {
            "available": False,
            "implemented": "partial",
            "service": service,
            "namespace": namespace,
            "checks": [
                "VirtualService traffic weights",
                "DestinationRule subsets",
                "mTLS mode",
                "outlier detection / circuit breaker",
                "retry and timeout policy",
            ],
            "summary": "Traffic policy live read requires CustomObjectsApi/Istio CRD wiring",
        }

    def infer_mesh_signals(self, service: str, pod: str | None = None, namespace: str = "default") -> dict[str, Any]:
        mesh = self.mesh_status()
        proxy = self.proxy_config_dump(pod=pod, namespace=namespace) if pod else {"available": False, "reason": "pod_not_provided"}
        policy = self.traffic_policy(service=service, namespace=namespace)
        hypotheses = []
        text = f"{mesh} {proxy} {policy}".lower()
        if "outlier" in text or "eject" in text:
            hypotheses.append("possible_destinationrule_outlier_ejection")
        if "virtualservice" in text or "weight" in text:
            hypotheses.append("possible_canary_traffic_shift")
        if "mtls" in text or "strict" in text:
            hypotheses.append("possible_mtls_policy_mismatch")
        return {
            "node": "istio",
            "type": "service_mesh_evidence",
            "service": service,
            "namespace": namespace,
            "pod": pod,
            "mesh_status": mesh,
            "proxy_config": proxy,
            "traffic_policy": policy,
            "hypotheses": hypotheses or ["insufficient_live_istio_data"],
            "safety_boundary": "read-only Istio diagnostics; no mesh mutation",
        }
