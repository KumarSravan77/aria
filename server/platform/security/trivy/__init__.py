from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class TrivyClient:
    """Trivy container and IaC scan results via Trivy Operator or Aqua API."""
    base_url: str = ""
    token: str | None = None
    timeout_seconds: int = 15

    def vulnerability_reports(self, namespace: str = "default") -> dict[str, Any]:
        if not self.base_url:
            try:
                from kubernetes import client, config
                try:
                    config.load_incluster_config()
                except Exception:
                    config.load_kube_config()
                custom = client.CustomObjectsApi()
                reports = custom.list_namespaced_custom_object(
                    group="aquasecurity.github.io", version="v1alpha1",
                    namespace=namespace, plural="vulnerabilityreports",
                )
                critical = sum(
                    r.get("report", {}).get("summary", {}).get("criticalCount", 0)
                    for r in reports.get("items", [])
                )
                return {"available": True, "namespace": namespace,
                        "report_count": len(reports.get("items", [])),
                        "critical_vulns": critical}
            except Exception as exc:
                return {"available": False, "namespace": namespace, "error": str(exc),
                        "message": "Trivy Operator not installed. Deploy trivy-operator for in-cluster scanning."}
        try:
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            r = requests.get(f"{self.base_url.rstrip('/')}/api/v1/vulnerabilities",
                             headers=headers, timeout=self.timeout_seconds)
            r.raise_for_status()
            return {"available": True, "result": r.json()}
        except Exception as exc:
            return {"available": False, "error": str(exc)}
