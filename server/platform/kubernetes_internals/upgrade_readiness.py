from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from server.platform.kubernetes_internals.k8s_client import KubernetesInternalsClient

@dataclass
class UpgradeReadinessInspector:
    client: KubernetesInternalsClient = field(default_factory=KubernetesInternalsClient)

    def inspect(self) -> dict[str, Any]:
        loaded = self.client.load()
        if not loaded.get("available"):
            return {"available": False, "degraded": True, "reason": loaded.get("error"), "status": "advisory_only", "checks": self.advisory_checks()}
        try:
            nodes = loaded["core"].list_node()
            versions = sorted({n.status.node_info.kubelet_version for n in nodes.items})
            return {"available": True, "node_count": len(nodes.items), "node_versions": versions, "checks": self.advisory_checks()}
        except Exception as exc:
            return {"available": False, "degraded": True, "reason": str(exc), "checks": self.advisory_checks()}

    def advisory_checks(self) -> list[str]:
        return ["deprecated API usage", "PDB coverage", "node version skew", "admission webhook compatibility", "CRD conversion webhooks", "CNI/CoreDNS compatibility"]
