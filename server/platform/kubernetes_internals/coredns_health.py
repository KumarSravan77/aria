from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from server.platform.kubernetes_internals.k8s_client import KubernetesInternalsClient

@dataclass
class CoreDnsHealthInspector:
    client: KubernetesInternalsClient = field(default_factory=KubernetesInternalsClient)

    def inspect(self) -> dict[str, Any]:
        loaded = self.client.load()
        if not loaded.get("available"):
            return {"available": False, "degraded": True, "reason": loaded.get("error"), "checks": self.advisory_checks()}
        try:
            pods = loaded["core"].list_namespaced_pod("kube-system", label_selector="k8s-app=kube-dns")
            statuses = []
            for pod in pods.items:
                statuses.append({
                    "name": pod.metadata.name,
                    "phase": pod.status.phase,
                    "ready": all(cs.ready for cs in (pod.status.container_statuses or [])),
                    "restarts": sum(cs.restart_count for cs in (pod.status.container_statuses or [])),
                })
            return {"available": True, "pod_count": len(statuses), "ready_count": sum(1 for s in statuses if s["ready"]), "pods": statuses, "checks": self.advisory_checks()}
        except Exception as exc:
            return {"available": False, "degraded": True, "reason": str(exc), "checks": self.advisory_checks()}

    def advisory_checks(self) -> list[str]:
        return ["CoreDNS readiness", "DNS error rate", "DNS latency", "kube-dns service endpoints"]
