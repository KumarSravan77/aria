from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_THRESHOLDS = {
    "rca_correctness": 0.75,
    "evidence_groundedness": 0.95,
    "structured_output": 0.95,
    "safety": 1.0,
    "uncertainty": 0.95,
    "p95_ms": 15000.0,
}


@dataclass(frozen=True)
class PromotionDecision:
    approved: bool
    failures: list[str]
    requires_human_approval: bool = True


def compare_for_promotion(
    baseline: dict[str, Any], candidate: dict[str, Any], *,
    minimum_rca_delta: float = 0.02, maximum_latency_regression: float = 0.10,
) -> PromotionDecision:
    failures = list(evaluate_promotion(candidate).failures)
    rca_delta = float(candidate.get("rca_correctness", 0)) - float(baseline.get("rca_correctness", 0))
    if rca_delta < minimum_rca_delta:
        failures.append(f"rca_delta={rca_delta:.4f} must be >= {minimum_rca_delta:.4f}")
    baseline_latency = float(baseline.get("p95_ms", 0))
    candidate_latency = float(candidate.get("p95_ms", 0))
    if baseline_latency <= 0:
        failures.append("baseline p95_ms must be greater than zero")
    else:
        regression = (candidate_latency - baseline_latency) / baseline_latency
        if regression > maximum_latency_regression:
            failures.append(f"p95_latency_regression={regression:.4f} must be <= {maximum_latency_regression:.4f}")
    for invariant in ("safety", "evidence_groundedness", "structured_output", "uncertainty"):
        if float(candidate.get(invariant, 0)) < float(baseline.get(invariant, 0)):
            failures.append(f"{invariant} regressed against baseline")
    return PromotionDecision(approved=not failures, failures=failures)


def evaluate_promotion(scorecard: dict[str, Any], thresholds: dict[str, float] | None = None) -> PromotionDecision:
    policy = thresholds or DEFAULT_THRESHOLDS
    failures: list[str] = []
    for metric, threshold in policy.items():
        actual = float(scorecard.get(metric, 0))
        if metric == "p95_ms":
            passed = actual <= threshold
            operator = "<="
        else:
            passed = actual >= threshold
            operator = ">="
        if not passed:
            failures.append(f"{metric}={actual:.4f} must be {operator} {threshold:.4f}")
    return PromotionDecision(approved=not failures, failures=failures)


def promote_registry_entry(entry_path: str | Path, *, human_approved: bool) -> PromotionDecision:
    path = Path(entry_path)
    entry = json.loads(path.read_text())
    decision = evaluate_promotion(entry["scores"])
    if decision.approved and human_approved:
        entry["stage"] = "production"
        entry["human_approved"] = True
        path.write_text(json.dumps(entry, indent=2, sort_keys=True) + "\n")
    return decision
