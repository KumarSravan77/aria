from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RouteScorer:
    def score(self, actual_route: list[str], expected_nodes: list[str]) -> dict:
        actual = set(actual_route)
        expected = set(expected_nodes)
        if not expected:
            return {"route_score": 1.0, "missing_nodes": [], "extra_nodes": sorted(actual)}
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        score = round((len(expected) - len(missing)) / len(expected), 3)
        return {"route_score": score, "missing_nodes": missing, "extra_nodes": extra}
