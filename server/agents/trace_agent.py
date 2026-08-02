from __future__ import annotations
from server.agents.base import BaseAgent, AgentResult
from server.observability.tempo_client import TempoClient

class TraceAgent(BaseAgent):
    name = "traces"
    def __init__(self, tempo: TempoClient):
        self.tempo = tempo
    def run(self, incident: dict, context: dict | None = None) -> AgentResult:
        service = incident.get("service", "unknown")
        traces = self.tempo.search_service_traces(service)
        return AgentResult(
            agent=self.name,
            available=bool(traces.get("available", False)),
            summary="Collected trace evidence" if traces.get("available") else "Tempo unavailable; no live trace evidence",
            evidence=[{"type":"tempo", "service":service, "result":traces}],
            recommendations=["Inspect slowest spans and downstream latency before choosing rollback or scale"],
        )
