from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from server.utils_time import utc_now


@dataclass
class ChaosValidationEngine:
    """Validates whether a chaos experiment produced the expected operational signals."""

    def validate(self, *, service: str, experiment: str, incident_created: bool = False, alert_fired: bool = False, healing_succeeded: bool = False, rag_sources: int = 0, mttr_seconds: int | None = None, slo_burn_observed: bool = False) -> dict[str, Any]:
        checks = {
            "incident_created": incident_created,
            "alert_fired": alert_fired,
            "rag_context_found": rag_sources > 0,
            "healing_succeeded": healing_succeeded,
            "mttr_recorded": mttr_seconds is not None,
            "slo_signal_observed": slo_burn_observed,
        }
        passed = sum(1 for value in checks.values() if value)
        total = len(checks)
        score = int(round((passed / total) * 100))
        if mttr_seconds is not None:
            if mttr_seconds <= 60:
                score = min(100, score + 5)
            elif mttr_seconds > 300:
                score = max(0, score - 10)
        return {
            "service": service,
            "experiment": experiment,
            "validated_at": utc_now().isoformat(),
            "checks": checks,
            "passed_checks": passed,
            "total_checks": total,
            "resilience_score": score,
            "status": "passed" if score >= 70 else "needs_improvement",
            "recommendations": self._recommend(checks, mttr_seconds),
        }

    def _recommend(self, checks: dict[str, bool], mttr_seconds: int | None) -> list[str]:
        recs = []
        if not checks["alert_fired"]:
            recs.append("Add or tune Prometheus/Alertmanager rule for this failure mode.")
        if not checks["incident_created"]:
            recs.append("Verify webhook routing from Alertmanager/Falco into the incident intake API.")
        if not checks["rag_context_found"]:
            recs.append("Add or tag runbook/RCA documents for this service and chaos scenario.")
        if not checks["healing_succeeded"]:
            recs.append("Review policy, ReBAC, approval flow, and executor permissions for remediation.")
        if mttr_seconds is not None and mttr_seconds > 300:
            recs.append("MTTR exceeded 5 minutes; consider automation or better runbook guidance.")
        return recs or ["Chaos validation passed. Continue scheduled resilience testing."]
