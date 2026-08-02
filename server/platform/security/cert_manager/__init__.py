from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class CertManagerClient:
    """cert-manager certificate status reader via Kubernetes API."""

    def certificates(self, namespace: str | None = None) -> dict[str, Any]:
        try:
            from kubernetes import client, config
            try:
                config.load_incluster_config()
            except Exception:
                config.load_kube_config()
            custom = client.CustomObjectsApi()
            if namespace:
                certs = custom.list_namespaced_custom_object(
                    group="cert-manager.io", version="v1",
                    namespace=namespace, plural="certificates",
                )
            else:
                certs = custom.list_cluster_custom_object(
                    group="cert-manager.io", version="v1", plural="certificates"
                )
            items = certs.get("items", [])
            expired = [
                c.get("metadata", {}).get("name")
                for c in items
                if any(cond.get("type") == "Ready" and cond.get("status") != "True"
                       for cond in c.get("status", {}).get("conditions", []))
            ]
            return {"available": True, "total": len(items), "not_ready": expired}
        except Exception as exc:
            return {
                "available": False,
                "error": str(exc),
                "message": "cert-manager not installed or cluster unreachable.",
            }
