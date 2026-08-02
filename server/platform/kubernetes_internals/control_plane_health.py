from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import time
from server.platform.kubernetes_internals.k8s_client import KubernetesInternalsClient

@dataclass
class ControlPlaneHealthInspector:
    client: KubernetesInternalsClient = field(default_factory=KubernetesInternalsClient)

    def inspect(self) -> dict[str, Any]:
        loaded = self.client.load()
        if not loaded.get("available"):
            return {"available": False, "degraded": True, "reason": loaded.get("error"), "checks": self.advisory_checks()}
        try:
            start = time.perf_counter()
            version = loaded["version"].get_code()
            namespaces = loaded["core"].list_namespace(limit=1)
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "available": True,
                "api_server_reachable": True,
                "api_latency_ms": latency_ms,
                "kubernetes_version": getattr(version, "git_version", None),
                "namespace_query_ok": bool(namespaces.items is not None),
                "checks": self.advisory_checks(),
            }
        except Exception as exc:
            return {"available": False, "degraded": True, "reason": str(exc), "checks": self.advisory_checks()}

    def advisory_checks(self) -> list[str]:
        return ["api_server_latency", "api_server_5xx_rate", "scheduler_health", "controller_manager_health", "node_lease_freshness", "etcd_quorum"]
