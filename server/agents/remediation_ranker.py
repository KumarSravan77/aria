from __future__ import annotations
import math
from typing import Any

from server.agents.base import BaseAgent, AgentResult
from server.healing.policy_validator import PolicyValidator
from server.memory.remediation_scorer import RemediationScorer
from server.memory.rl_optimizer import RLOptimizer

CANDIDATE_ACTIONS = ["scale_deployment", "restart_deployment", "rollback_deployment", "restart_pod"]


class RemediationRankerAgent(BaseAgent):
    """Combines RL UCB scores and memory-based similarity into a ranked remediation list.

    Does not execute actions — recommendation only.
    """

    name = "remediation_ranker"

    def __init__(self, policy: PolicyValidator, scorer: RemediationScorer, rl: RLOptimizer) -> None:
        self.policy = policy
        self.scorer = scorer
        self.rl = rl

    def _user_dict(self, context: dict[str, Any]) -> dict:
        user = context.get("user", {})
        if hasattr(user, "model_dump"):
            return user.model_dump()
        return user if isinstance(user, dict) else {}

    def run(self, incident: dict[str, Any], context: dict[str, Any] | None = None) -> AgentResult:
        ctx = context or {}
        service = incident.get("service", "unknown")
        environment = incident.get("environment", "dev")
        severity = incident.get("severity", "P2")
        probable_cause = (
            incident.get("probable_cause")
            or (incident.get("analysis") or {}).get("probable_cause", "unknown")
        )
        user = self._user_dict(ctx)
        memory_items: list[dict] = ctx.get("memory_items", [])

        # Filter to policy-allowed actions for this user/service/env
        allowed = [
            action for action in CANDIDATE_ACTIONS
            if self.policy.validate({
                "action": action, "target": service, "namespace": "demo",
                "environment": environment, "dry_run": True, "user": user,
            }).get("allowed")
        ]

        similarity_scores = self.scorer.score(incident, memory_items)
        rl_ranked = self.rl.recommend(service, probable_cause, severity, allowed)

        ranked = []
        for item in rl_ranked:
            action = item["action"]
            sim = similarity_scores.get(action, 0.0)
            ucb = item["ucb_score"]
            # Map large UCB values (unexplored) to a moderate exploration bonus
            ucb_norm = ucb / (1.0 + abs(ucb)) if ucb < 90 else 0.5
            combined = round(0.6 * ucb_norm + 0.4 * sim, 3)
            needs_approval = self.policy.validate({
                "action": action, "target": service, "namespace": "demo",
                "environment": environment, "dry_run": True, "user": user,
            }).get("requires_approval", False)
            ranked.append({
                "action": action,
                "confidence": combined,
                "rl_trials": item["trials"],
                "rl_mean_reward": item["mean_reward"],
                "similarity_score": sim,
                "requires_approval": needs_approval,
            })

        ranked.sort(key=lambda x: -x["confidence"])
        top = ranked[0]["action"] if ranked else "none"

        return AgentResult(
            agent=self.name,
            available=True,
            summary=f"Ranked {len(ranked)} remediation(s); top={top}",
            evidence=[{
                "type": "remediation_ranking",
                "ranked": ranked,
                "policy_allowed_count": len(allowed),
                "memory_items_used": len(memory_items),
            }],
            recommendations=[
                f"Top recommendation: {ranked[0]['action']} (confidence={ranked[0]['confidence']})" if ranked
                else "No policy-allowed actions available for this service/environment.",
                "Submit via /heal with dry_run=false; approval required for prod actions.",
            ],
        )
