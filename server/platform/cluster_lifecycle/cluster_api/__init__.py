from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class ClusterAPIClient:
    """Cluster API declarative cluster lifecycle reader."""

    def clusters(self, namespace: str = "default") -> dict[str, Any]:
        try:
            from kubernetes import client, config
            try:
                config.load_incluster_config()
            except Exception:
                config.load_kube_config()
            custom = client.CustomObjectsApi()
            result = custom.list_namespaced_custom_object(
                group="cluster.x-k8s.io", version="v1beta1",
                namespace=namespace, plural="clusters",
            )
            items = result.get("items", [])
            return {
                "available": True,
                "clusters": [
                    {"name": c.get("metadata", {}).get("name"),
                     "phase": c.get("status", {}).get("phase", "unknown")}
                    for c in items
                ],
            }
        except Exception as exc:
            return {
                "available": False,
                "error": str(exc),
                "message": "Cluster API not installed. Deploy cluster-api for declarative cluster lifecycle management.",
            }
