from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from server.platform.kubernetes_internals.k8s_client import KubernetesInternalsClient

@dataclass
class CniHealthInspector:
    client: KubernetesInternalsClient = field(default_factory=KubernetesInternalsClient)

    def inspect(self) -> dict[str, Any]:
        loaded = self.client.load()
        if not loaded.get("available"):
            return {"available": False, "degraded": True, "reason": loaded.get("error"), "checks": self.advisory_checks()}
        try:
            nodes = loaded["core"].list_node()
            status = []
            for node in nodes.items:
                conditions = {c.type: c.status for c in (node.status.conditions or [])}
                status.append({"name": node.metadata.name, "ready": conditions.get("Ready"), "network_unavailable": conditions.get("NetworkUnavailable"), "pod_cidr": getattr(node.spec, "pod_cidr", None)})
            return {"available": True, "node_count": len(status), "nodes": status, "checks": self.advisory_checks()}
        except Exception as exc:
            return {"available": False, "degraded": True, "reason": str(exc), "checks": self.advisory_checks()}

    def advisory_checks(self) -> list[str]:
        return ["NetworkUnavailable condition", "pod CIDR assignment", "CNI daemonset health", "network policy enforcement"]
