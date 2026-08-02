from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class GatekeeperClient:
    """OPA Gatekeeper constraint violation reader."""

    def violations(self) -> dict[str, Any]:
        try:
            from kubernetes import client, config
            try:
                config.load_incluster_config()
            except Exception:
                config.load_kube_config()
            custom = client.CustomObjectsApi()
            result = custom.list_cluster_custom_object(
                group="constraints.gatekeeper.sh", version="v1beta1", plural="configs"
            )
            return {"available": True, "constraints": result.get("items", [])}
        except Exception as exc:
            return {
                "available": False,
                "error": str(exc),
                "message": "Gatekeeper not installed. Kyverno is the primary policy-as-code layer in ARIA.",
            }
