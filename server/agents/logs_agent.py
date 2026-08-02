from __future__ import annotations
from server.agents.base import BaseAgent, AgentResult
from server.observability.loki_client import LokiClient

class LogsAgent(BaseAgent):
    name = "logs"
    def __init__(self, loki: LokiClient):
        self.loki = loki
    def run(self, incident: dict, context: dict | None = None) -> AgentResult:
        service = incident.get("service", "unknown")
        logs = self.loki.query(f'{{app="{service}"}} |= "error"')
        return AgentResult(
            agent=self.name,
            available=bool(logs.get("available", False)),
            summary="Collected recent error logs" if logs.get("available") else "Loki unavailable; no live log evidence",
            evidence=[{"type":"loki", "service":service, "result":logs}],
            recommendations=["Check for new exception signatures and dependency timeout patterns"],
        )
