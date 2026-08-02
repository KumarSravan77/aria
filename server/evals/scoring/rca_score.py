from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RcaScorer:
    def score(self, predicted: str | None, expected: str | None) -> dict:
        if not expected:
            return {"rca_score": None, "reason": "no_expected_rca"}
        predicted = (predicted or "").lower()
        expected = expected.lower()
        score = 1.0 if expected in predicted else 0.0
        if score == 0.0:
            expected_tokens = set(expected.replace("_", " ").split())
            predicted_tokens = set(predicted.replace("_", " ").split())
            overlap = expected_tokens & predicted_tokens
            score = round(len(overlap) / max(len(expected_tokens), 1), 3)
        return {"rca_score": score, "expected": expected, "predicted": predicted}
