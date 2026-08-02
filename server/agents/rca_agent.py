from __future__ import annotations
from server.agents.base import BaseAgent, AgentResult

class RcaAgent(BaseAgent):
    name = "rca"
    def run(self, incident: dict, context: dict | None = None) -> AgentResult:
        service = incident.get("service", "unknown")
        return AgentResult(
            agent=self.name,
            available=True,
            summary=f"RCA draft inputs prepared for {service}",
            evidence=[{"type":"rca-inputs", "required":["timeline", "probable cause", "customer impact", "corrective actions"]}],
            recommendations=["Generate final RCA after mitigation and validation are complete"],
        )
