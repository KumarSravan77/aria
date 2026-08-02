from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class KyvernoClient:
    """Kyverno policy compliance reader via Kubernetes API."""

    def policy_reports(self, namespace: str = "default") -> dict[str, Any]:
        try:
            from kubernetes import client, config
            try:
                config.load_incluster_config()
            except Exception:
                config.load_kube_config()
            custom = client.CustomObjectsApi()
            reports = custom.list_namespaced_custom_object(
                group="wgpolicyk8s.io", version="v1alpha2",
                namespace=namespace, plural="policyreports",
            )
            items = reports.get("items", [])
            summary = {"pass": 0, "fail": 0, "warn": 0, "error": 0, "skip": 0}
            for item in items:
                for k, v in item.get("summary", {}).items():
                    if k in summary:
                        summary[k] += v
            return {"available": True, "namespace": namespace,
                    "report_count": len(items), "summary": summary}
        except Exception as exc:
            return {
                "available": False,
                "namespace": namespace,
                "error": str(exc),
                "message": "Kyverno not installed or PolicyReport CRD not found.",
            }
