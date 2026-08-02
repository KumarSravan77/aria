from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class KubernetesInternalsClient:
    """Read-only Kubernetes internals client with graceful degradation."""

    def load(self) -> dict[str, Any]:
        try:
            from kubernetes import client, config
            try:
                config.load_incluster_config()
                mode = "in_cluster"
            except Exception:
                config.load_kube_config()
                mode = "kubeconfig"
            return {
                "available": True,
                "mode": mode,
                "core": client.CoreV1Api(),
                "apps": client.AppsV1Api(),
                "admission": client.AdmissionregistrationV1Api(),
                "version": client.VersionApi(),
            }
        except Exception as exc:
            return {"available": False, "error": str(exc), "summary": "Kubernetes client unavailable"}
