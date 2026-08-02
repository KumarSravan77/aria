from __future__ import annotations
from typing import Any

# Estimated token cost per agent invocation (prompt + response heuristics).
# RAG and RCA agents consume significantly more because they process documents.
AGENT_TOKEN_COST: dict[str, int] = {
    "rag":                 1500,
    "rca":                 1000,
    "remediation_ranker":   500,
    "healing":              300,
    "metrics":              100,
    "logs":                 100,
    "traces":               100,
    "k8s":                  100,
    "slack":                 50,
}
DEFAULT_AGENT_COST = 200

# Cost per 1k tokens by model. Local Ollama = $0.
MODEL_COST_PER_1K: dict[str, float] = {
    "llama3.1:8b":  0.0,
    "llama3:8b":    0.0,
    "gpt-4o":       0.005,
    "gpt-4":        0.03,
    "claude-3-5":   0.003,
}


class TokenBudgetEnforcer:
    """Estimates and enforces token consumption per investigation run."""

    def __init__(self, default_budget: int = 5000, model: str = "llama3.1:8b") -> None:
        self.default_budget = default_budget
        self.model = model
        self._total_tokens_used: int = 0

    def estimate(self, agents: list) -> int:
        return sum(AGENT_TOKEN_COST.get(getattr(a, "name", ""), DEFAULT_AGENT_COST) for a in agents)

    def trim_to_budget(self, agents: list, budget: int | None = None) -> tuple[list, int]:
        """Remove lowest-value agents until estimated cost fits within budget.
        Returns (trimmed_agents, estimated_tokens).
        """
        limit = budget or self.default_budget
        # Sort by cost descending so we cut expensive agents first if over budget
        by_cost = sorted(agents, key=lambda a: AGENT_TOKEN_COST.get(getattr(a, "name", ""), DEFAULT_AGENT_COST))
        result = []
        used = 0
        for agent in by_cost:
            cost = AGENT_TOKEN_COST.get(getattr(agent, "name", ""), DEFAULT_AGENT_COST)
            if used + cost <= limit:
                result.append(agent)
                used += cost
        return result, used

    def record_usage(self, tokens: int) -> None:
        self._total_tokens_used += tokens

    def estimate_cost_usd(self, tokens: int) -> float:
        return round((tokens / 1000) * MODEL_COST_PER_1K.get(self.model, 0.01), 6)

    def session_summary(self) -> dict[str, Any]:
        return {
            "total_tokens_used": self._total_tokens_used,
            "estimated_cost_usd": self.estimate_cost_usd(self._total_tokens_used),
            "model": self.model,
            "default_budget_per_run": self.default_budget,
        }
