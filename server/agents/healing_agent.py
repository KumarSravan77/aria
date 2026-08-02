from __future__ import annotations
from server.agents.base import BaseAgent, AgentResult
from server.healing.policy_validator import PolicyValidator

class HealingAgent(BaseAgent):
    name = "healing"
    def __init__(self, policy: PolicyValidator):
        self.policy = policy
    def run(self, incident: dict, context: dict | None = None) -> AgentResult:
        service = incident.get("service", "unknown")
        environment = incident.get("environment", "dev")
        proposed = {"action":"scale_deployment", "target":service, "namespace":incident.get("namespace", "demo"), "environment":environment, "dry_run":True, "user": (context or {}).get("user", {})}
        decision = self.policy.validate(proposed)
        return AgentResult(
            agent=self.name,
            available=True,
            summary="Generated policy-checked remediation proposal",
            evidence=[{"type":"policy", "proposed_action":proposed, "decision":decision}],
            recommendations=["Do not execute automatically; use approval workflow for live/prod actions"],
        )
