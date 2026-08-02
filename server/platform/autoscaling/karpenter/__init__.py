from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class KarpenterClient:
    """Karpenter node provisioner status and NodePool reader."""

    def nodepools(self) -> dict[str, Any]:
        try:
            from kubernetes import client, config
            try:
                config.load_incluster_config()
            except Exception:
                config.load_kube_config()
            custom = client.CustomObjectsApi()
            pools = custom.list_cluster_custom_object(
                group="karpenter.sh", version="v1", plural="nodepools"
            )
            items = pools.get("items", [])
            return {
                "available": True,
                "nodepools": [
                    {"name": p.get("metadata", {}).get("name"),
                     "ready": p.get("status", {}).get("conditions", [{}])[0].get("status")}
                    for p in items
                ],
            }
        except Exception as exc:
            return {
                "available": False,
                "error": str(exc),
                "message": "Karpenter not installed or cluster unreachable.",
            }
