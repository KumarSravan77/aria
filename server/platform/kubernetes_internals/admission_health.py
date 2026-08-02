from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from server.platform.kubernetes_internals.k8s_client import KubernetesInternalsClient

@dataclass
class AdmissionWebhookInspector:
    client: KubernetesInternalsClient = field(default_factory=KubernetesInternalsClient)

    def inspect(self) -> dict[str, Any]:
        loaded = self.client.load()
        if not loaded.get("available"):
            return {"available": False, "degraded": True, "reason": loaded.get("error"), "expected": ["Kyverno", "Gatekeeper"]}
        try:
            validating = loaded["admission"].list_validating_webhook_configuration()
            mutating = loaded["admission"].list_mutating_webhook_configuration()
            return {
                "available": True,
                "validating_count": len(validating.items),
                "mutating_count": len(mutating.items),
                "risk_note": "Admission webhook failures can block deployments or bypass policy depending on failurePolicy",
            }
        except Exception as exc:
            return {"available": False, "degraded": True, "reason": str(exc)}
