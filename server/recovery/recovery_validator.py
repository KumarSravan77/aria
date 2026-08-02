from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RecoveryValidator:
    """Scores whether HA/DR recovery controls worked after an incident or chaos test."""

    def validate(
        self,
        service: str,
        replicas_ready: bool = True,
        traffic_restored: bool = True,
        data_restored: bool = True,
        alerts_resolved: bool = True,
        rto_met: bool = True,
        rpo_met: bool = True,
    ) -> dict:
        checks = {
            "replicas_ready": replicas_ready,
            "traffic_restored": traffic_restored,
            "data_restored": data_restored,
            "alerts_resolved": alerts_resolved,
            "rto_met": rto_met,
            "rpo_met": rpo_met,
        }
        passed = sum(1 for ok in checks.values() if ok)
        score = round((passed / len(checks)) * 100)
        return {
            "service": service,
            "checks": checks,
            "score": score,
            "status": "PASS" if score >= 90 else "DEGRADED" if score >= 60 else "FAIL",
            "recommendation": "Recovery validated" if score >= 90 else "Review failed recovery controls and update HA/DR runbooks",
        }
