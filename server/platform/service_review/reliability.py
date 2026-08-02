from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from server.platform.spec_harness.models import Evidence, Finding, Score


def _grade(numeric: float) -> str:
    if numeric >= 90:
        return "A"
    if numeric >= 75:
        return "B"
    if numeric >= 60:
        return "C"
    if numeric >= 45:
        return "D"
    return "F"


@dataclass
class ReliabilityReview:
    score: Score
    findings: List[Finding]
    error_budget_remaining_percent: float
    burn_rate: float


class ReliabilityAgent:
    """Deterministic reliability intelligence used by the service-review harness.

    It evaluates SLO compliance, error budget risk, burn rate, latency, and
    saturation from a service telemetry snapshot. The class is intentionally
    provider-neutral so fixtures can represent Dynatrace, Prometheus, Datadog,
    Honeycomb, or mocked platform data.
    """

    name = "reliability-agent"

    def review(self, slo_config: Dict[str, Any], telemetry_snapshot: Dict[str, Any]) -> ReliabilityReview:
        findings: List[Finding] = []

        availability_target = float(slo_config.get("availability_target_percent", 99.9))
        current_availability = float(telemetry_snapshot.get("availability_percent", 100.0))
        error_budget_remaining = float(telemetry_snapshot.get("error_budget_remaining_percent", 100.0))
        burn_rate = float(telemetry_snapshot.get("burn_rate", 0.0))
        p95_target_ms = float(slo_config.get("latency_p95_ms", 500))
        p95_actual_ms = float(telemetry_snapshot.get("latency_p95_ms", 0))

        numeric = 100.0
        blockers: List[str] = []

        if current_availability < availability_target:
            numeric -= 25
            blockers.append("availability_slo_breached")
            findings.append(Finding(
                id="rel-slo-availability-breached",
                title="SLO breached: availability below target",
                category="reliability",
                severity="P1",
                evidence=[Evidence(
                    source="telemetry_snapshot",
                    path="availability_percent",
                    observed=str(current_availability),
                    expected=f">= {availability_target}",
                    collector="reliability-agent",
                )],
                impact={
                    "user_impact": "Users may experience failed or unavailable requests.",
                    "business_impact": "Tiered SLO commitment is not being met.",
                    "technical_impact": "Service reliability is below the configured availability objective.",
                },
                recommendation={
                    "summary": "Investigate recent deployments, upstream dependency errors, pod restarts, and ingress/service-mesh error patterns.",
                    "remediation_type": "approval_required",
                },
                confidence={"score": 0.94, "explanation": "Availability is directly below the configured SLO target."},
            ))

        if error_budget_remaining <= 10:
            numeric -= 20
            blockers.append("error_budget_low")
            sev = "P0" if error_budget_remaining <= 0 else "P1"
            findings.append(Finding(
                id="rel-error-budget-risk",
                title="Error budget risk: remaining budget is critically low",
                category="reliability",
                severity=sev,
                evidence=[Evidence(
                    source="telemetry_snapshot",
                    path="error_budget_remaining_percent",
                    observed=str(error_budget_remaining),
                    expected="> 10",
                    collector="reliability-agent",
                )],
                impact={
                    "user_impact": "Further failures may cause visible reliability impact.",
                    "business_impact": "Release velocity may need to pause until reliability is restored.",
                    "technical_impact": "The service has little or no error budget left.",
                },
                recommendation={
                    "summary": "Freeze risky releases, prioritize reliability fixes, and require approval for production mutations.",
                    "remediation_type": "approval_required",
                },
                confidence={"score": 0.92, "explanation": "Error budget remaining is below the platform threshold."},
            ))

        if burn_rate >= 2:
            numeric -= 15
            blockers.append("burn_rate_elevated")
            findings.append(Finding(
                id="rel-burn-rate-elevated",
                title="Burn rate elevated: service is consuming error budget too quickly",
                category="reliability",
                severity="P1" if burn_rate >= 5 else "P2",
                evidence=[Evidence(
                    source="telemetry_snapshot",
                    path="burn_rate",
                    observed=str(burn_rate),
                    expected="< 2",
                    collector="reliability-agent",
                )],
                impact={
                    "user_impact": "Reliability may degrade quickly if the trend continues.",
                    "business_impact": "Error budget may be exhausted before the review window ends.",
                    "technical_impact": "Fast or medium burn pattern detected.",
                },
                recommendation={
                    "summary": "Correlate burn rate with deployments, dependency failures, retry storms, and capacity saturation.",
                    "remediation_type": "manual",
                },
                confidence={"score": 0.9, "explanation": "Burn rate is above the fast-burn threshold used by the harness."},
            ))

        if p95_actual_ms > p95_target_ms:
            numeric -= 10
            findings.append(Finding(
                id="rel-latency-p95-breach",
                title="Latency SLI breached: p95 latency above target",
                category="reliability",
                severity="P2",
                evidence=[Evidence(
                    source="telemetry_snapshot",
                    path="latency_p95_ms",
                    observed=str(p95_actual_ms),
                    expected=f"<= {p95_target_ms}",
                    collector="reliability-agent",
                )],
                impact={
                    "user_impact": "Users may experience slow responses.",
                    "business_impact": "Transaction completion or conversion may be reduced.",
                    "technical_impact": "Latency objective is not being met.",
                },
                recommendation={
                    "summary": "Review service saturation, downstream latency, database query time, and retry behavior.",
                    "remediation_type": "manual",
                },
                confidence={"score": 0.88, "explanation": "p95 latency is above the configured SLO."},
            ))

        numeric = max(0.0, min(100.0, numeric))
        return ReliabilityReview(
            score=Score(
                name="reliability",
                grade=_grade(numeric),
                numeric_score=numeric,
                rationale="Reliability score derived from SLO status, error budget, burn rate, and latency.",
                blockers=blockers,
            ),
            findings=findings,
            error_budget_remaining_percent=error_budget_remaining,
            burn_rate=burn_rate,
        )
