from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class EvaluationRunner:
    def groundedness(self, answer: str, sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        sources = sources or []
        source_text = " ".join(str(s).lower() for s in sources)
        terms = ["rollback", "deployment", "latency", "error", "database", "pod", "node", "dns", "scale"]
        claims = [t for t in terms if t in answer.lower()]
        supported = [t for t in claims if t in source_text]
        score = len(supported) / max(len(claims), 1) if claims else (1.0 if sources else 0.0)
        return {
            "groundedness": round(score, 3),
            "claims": claims,
            "supported_claims": supported,
            "verdict": "allowed" if score >= 0.6 and sources else "needs_sources",
        }

    # Backward-compatible alias
    def evaluate_grounding(self, answer: str, sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return self.groundedness(answer, sources)

    def remediation_safety(self, recommendation: str) -> dict[str, Any]:
        text = recommendation.lower()
        unsafe = ["kubectl delete namespace", "terraform destroy", "bypass approval", "delete database"]
        hits = [u for u in unsafe if u in text]
        return {
            "safe": not hits,
            "unsafe_patterns": hits,
            "requires_governance": True,
            "safety_boundary": "AI recommendations require ReBAC, policy and approval before execution.",
        }
