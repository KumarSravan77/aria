from __future__ import annotations
from server.agents.base import BaseAgent, AgentResult
from server.rag.lazy_rag_service import LazyRagService as RagService

class RagAgent(BaseAgent):
    name = "rag"
    def __init__(self, rag: RagService):
        self.rag = rag
    def run(self, incident: dict, context: dict | None = None) -> AgentResult:
        service = incident.get("service", "unknown")
        symptoms = ", ".join(incident.get("symptoms", [])) or incident.get("alert_name", "incident")
        user = (context or {}).get("user")
        result = self.rag.answer(f"{service} {symptoms} runbook RCA SOP", user=user)
        sources = result.get("sources", []) or []
        return AgentResult(
            agent=self.name,
            available=result.get("available", True),
            summary=f"Retrieved {len(sources)} authorized knowledge sources",
            evidence=[{"type":"rag", "service":service, "sources":sources, "answer":result.get("answer")}],
            recommendations=["Use retrieved runbook steps as the approved remediation baseline"],
        )
