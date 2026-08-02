from __future__ import annotations
from server.agents.base import BaseAgent, AgentResult

class SlackAgent(BaseAgent):
    name = "chatops"
    def run(self, incident: dict, context: dict | None = None) -> AgentResult:
        channel = incident.get("channel_id") or f"inc-{incident.get('severity','p2').lower()}-{incident.get('service','service')}"
        return AgentResult(
            agent=self.name,
            available=True,
            summary=f"Prepared war-room update for {channel}",
            evidence=[{"type":"chatops", "channel": channel}],
            recommendations=["Post short evidence-based updates and approval prompts into the incident channel"],
        )
