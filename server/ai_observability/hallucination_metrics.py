from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class HallucinationMetrics:
    """Grounding-oriented hallucination scoring.

    This is intentionally deterministic. It does not claim semantic truth; it
    checks whether operational claims are backed by retrieved evidence.
    """

    def score(self, answer: str, sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        sources = sources or []
        if not answer.strip():
            return {"groundedness": 0.0, "verdict": "empty", "needs_sources": True}

        source_titles = " ".join(str(s.get("title", "")) for s in sources).lower()
        answer_lower = answer.lower()
        operational_terms = ["rollback", "scale", "latency", "error", "deployment", "database", "pod", "node"]
        claims = [t for t in operational_terms if t in answer_lower]
        supported = [t for t in claims if t in source_titles or any(t in str(s).lower() for s in sources)]

        if not claims:
            groundedness = 0.75 if sources else 0.25
        else:
            groundedness = len(supported) / max(len(claims), 1)

        verdict = "allowed" if groundedness >= 0.6 and sources else "needs_sources"
        return {
            "groundedness": round(groundedness, 3),
            "verdict": verdict,
            "claims_checked": claims,
            "supported_claims": supported,
            "needs_sources": verdict != "allowed",
        }
