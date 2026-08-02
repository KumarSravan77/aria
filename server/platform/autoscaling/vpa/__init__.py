from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class VPAClient:
    """Vertical Pod Autoscaler recommendation reader.

    Returns resource recommendations from VPA objects already installed in the cluster.
    Does not mutate pod resources — recommendations only.
    """

    def recommendations(self, deployment: str, namespace: str = "demo") -> dict[str, Any]:
        try:
            from kubernetes import client, config
            try:
                config.load_incluster_config()
            except Exception:
                config.load_kube_config()
            custom = client.CustomObjectsApi()
            vpa = custom.get_namespaced_custom_object(
                group="autoscaling.k8s.io", version="v1",
                namespace=namespace, plural="verticalpodautoscalers", name=deployment,
            )
            recs = vpa.get("status", {}).get("recommendation", {}).get("containerRecommendations", [])
            return {"available": True, "deployment": deployment, "namespace": namespace, "recommendations": recs}
        except Exception as exc:
            return {
                "available": False,
                "deployment": deployment,
                "namespace": namespace,
                "error": str(exc),
                "message": "VPA not installed or deployment not found. Install VPA and add a VerticalPodAutoscaler object.",
            }
