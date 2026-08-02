from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from server.investigation.kubernetes_troubleshooter.istio_checks import IstioDiagnosticClient


@dataclass
class IstioAgent:
    """Service mesh investigation agent. Evidence only; no mutation."""

    client: IstioDiagnosticClient = field(default_factory=IstioDiagnosticClient)

    def run(self, incident: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        service = incident.get("service") or incident.get("target") or context.get("service") or "unknown"
        namespace = incident.get("namespace") or context.get("namespace") or "default"
        pod = incident.get("pod") or incident.get("pod_name") or context.get("pod")
        evidence = self.client.infer_mesh_signals(service=service, pod=pod, namespace=namespace)
        return {
            "agent": "istio",
            "evidence": evidence,
            "summary": "Istio service mesh diagnostics completed",
            "available": evidence.get("mesh_status", {}).get("available", False) or evidence.get("proxy_config", {}).get("available", False),
        }
