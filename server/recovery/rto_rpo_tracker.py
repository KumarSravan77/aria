from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RtoRpoTracker:
    """Evaluates recovery objectives against observed recovery metrics."""

    def evaluate(
        self,
        service: str,
        rto_target_minutes: int = 30,
        rpo_target_minutes: int = 15,
        actual_recovery_minutes: int = 0,
        actual_data_loss_minutes: int = 0,
    ) -> dict:
        rto_met = actual_recovery_minutes <= rto_target_minutes
        rpo_met = actual_data_loss_minutes <= rpo_target_minutes
        return {
            "service": service,
            "rto": {
                "target_minutes": rto_target_minutes,
                "actual_minutes": actual_recovery_minutes,
                "met": rto_met,
                "variance_minutes": actual_recovery_minutes - rto_target_minutes,
            },
            "rpo": {
                "target_minutes": rpo_target_minutes,
                "actual_minutes": actual_data_loss_minutes,
                "met": rpo_met,
                "variance_minutes": actual_data_loss_minutes - rpo_target_minutes,
            },
            "status": "PASS" if rto_met and rpo_met else "FAIL",
        }
