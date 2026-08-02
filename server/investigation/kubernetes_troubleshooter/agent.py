from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from server.investigation.kubernetes_troubleshooter.client import KubernetesDiagnosticClient
from server.investigation.kubernetes_troubleshooter.rules import KubernetesTroubleshootingRules

@dataclass
class KubernetesTroubleshooterAgent:
    """Deep read-only Kubernetes troubleshooting agent. Returns evidence only."""
    client: KubernetesDiagnosticClient = field(default_factory=KubernetesDiagnosticClient)
    rules: KubernetesTroubleshootingRules = field(default_factory=KubernetesTroubleshootingRules)

    def run(self, incident: dict[str, Any]) -> dict[str, Any]:
        mode = self.rules.classify(incident)
        pod = incident.get("pod") or incident.get("pod_name") or incident.get("target")
        namespace = incident.get("namespace") or "default"
        diagnostics: dict[str, Any] = {}
        if pod:
            diagnostics["pod"] = self.client.describe_pod(str(pod), namespace)
            diagnostics["events"] = self.client.pod_events(str(pod), namespace)
            if mode in {"CrashLoopBackOff", "OOMKilled"}:
                diagnostics["previous_logs"] = self.client.previous_logs(str(pod), namespace)
        return {
            "node": "kubernetes_troubleshooter",
            "type": "kubernetes_diagnostic_evidence",
            "failure_mode": mode,
            "service": incident.get("service") or incident.get("target"),
            "namespace": namespace,
            "pod": pod,
            "checklist": self.rules.checklist(mode),
            "diagnostics": diagnostics,
            "available": True,
            "safety_boundary": "read-only diagnostics; no cluster mutation",
        }
