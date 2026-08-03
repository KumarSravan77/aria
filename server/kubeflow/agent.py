from __future__ import annotations

from urllib.parse import quote

from server.agents.base import AgentResult
from server.kubeflow.analyzer import KubeflowIncidentAnalyzer
from server.kubeflow.client import KubeflowEvidenceClient


class KubeflowOperationsAgent:
    name = "kubeflow_operations"

    def __init__(
        self,
        client: KubeflowEvidenceClient | None = None,
        analyzer: KubeflowIncidentAnalyzer | None = None,
        headlamp_base_url: str = "",
    ):
        self.client = client or KubeflowEvidenceClient()
        self.analyzer = analyzer or KubeflowIncidentAnalyzer()
        self.headlamp_base_url = headlamp_base_url.rstrip("/")

    def run(self, incident: dict, context: dict | None = None) -> AgentResult:
        kind = str(incident.get("kind") or incident.get("resource_kind") or "TrainJob")
        name = str(incident.get("name") or incident.get("resource_name") or incident.get("target") or "")
        namespace = str(incident.get("namespace") or "default")
        if not name:
            return AgentResult(
                agent=self.name,
                available=False,
                summary="Kubeflow resource name is required",
                error="resource_name_required",
            )
        evidence = self.client.get(kind, name, namespace)
        analysis = self.analyzer.analyze(evidence, incident)
        headlamp_url = self._headlamp_url(kind, name, namespace)
        return AgentResult(
            agent=self.name,
            available=analysis["available"],
            summary=f"{kind} {namespace}/{name}: {analysis['failure_mode']}",
            evidence=[
                {"type": "kubeflow_resource", "payload": evidence},
                {"type": "kubeflow_analysis", "payload": analysis},
                {"type": "headlamp_link", "url": headlamp_url} if headlamp_url else {"type": "headlamp_link", "available": False},
            ],
            recommendations=analysis["recommendations"],
            error=evidence.get("error") if not evidence.get("available") else None,
        )

    def _headlamp_url(self, kind: str, name: str, namespace: str) -> str | None:
        if not self.headlamp_base_url:
            return None
        return (
            f"{self.headlamp_base_url}/c/main/{quote(namespace, safe='')}/"
            f"kubeflow/{quote(kind.lower(), safe='')}/{quote(name, safe='')}"
        )

