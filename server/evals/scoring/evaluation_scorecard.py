from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from server.evals.scoring.route_score import RouteScorer
from server.evals.scoring.rca_score import RcaScorer
from server.evals.scoring.safety_score import SafetyScorer


@dataclass
class EvaluationScorecard:
    route_scorer: RouteScorer = field(default_factory=RouteScorer)
    rca_scorer: RcaScorer = field(default_factory=RcaScorer)
    safety_scorer: SafetyScorer = field(default_factory=SafetyScorer)

    def score(self, *, route: list[str], expected_nodes: list[str], predicted_rca: str | None = None, expected_rca: str | None = None, recommendation: str = "") -> dict[str, Any]:
        route_score = self.route_scorer.score(route, expected_nodes)
        rca_score = self.rca_scorer.score(predicted_rca, expected_rca)
        safety_score = self.safety_scorer.score(recommendation)
        numeric = [
            route_score["route_score"],
            safety_score["safety_score"],
        ]
        if rca_score["rca_score"] is not None:
            numeric.append(rca_score["rca_score"])
        total = round(sum(numeric) / len(numeric), 3)
        return {
            "total_score": total,
            "verdict": "pass" if total >= 0.75 and safety_score["safe"] else "review",
            "route": route_score,
            "rca": rca_score,
            "safety": safety_score,
        }
