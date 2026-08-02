from __future__ import annotations

from dataclasses import dataclass, field
from server.safety.mutation_guard import MutationGuard


@dataclass
class SafetyScorer:
    guard: MutationGuard = field(default_factory=MutationGuard)

    def score(self, recommendation: str) -> dict:
        scan = self.guard.scan_text(recommendation)
        return {
            "safety_score": 1.0 if scan["safe"] else 0.0,
            "safe": scan["safe"],
            "dangerous_terms": scan["dangerous_terms"],
        }
