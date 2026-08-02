from __future__ import annotations
from typing import Any


class IncidentForecaster:
    """Predicts incident likelihood from SLO burn rate, memory patterns, and cluster pressure.

    All inputs are plain dicts — no external services required.
    Confidence is a weighted sum of three independent signals.
    """

    def forecast(self, service: str, slo_result: dict[str, Any],
                 memory_items: list[dict[str, Any]],
                 cluster_size: int = 0) -> dict[str, Any]:
        burn_rate = float(slo_result.get("burn_rate", 0.0))
        budget_remaining = float(slo_result.get("error_budget_remaining", 100.0))

        # Signal 1: SLO burn (max weight 0.75; critical alone is sufficient for high prediction)
        if burn_rate >= 10.0:
            burn_score, burn_label = 0.75, "critical"
        elif burn_rate >= 2.0:
            burn_score, burn_label = 0.4, "warning"
        elif burn_rate >= 1.0:
            burn_score, burn_label = 0.2, "watch"
        else:
            burn_score, burn_label = 0.0, "healthy"

        # Signal 2: recurrence pressure from memory (max weight 0.3)
        recent_bad = sum(
            1 for item in memory_items
            if any(w in item.get("outcome", "").lower() for w in ("escalat", "unresolved", "paged"))
        )
        recurrence_score = min(0.3, recent_bad * 0.1)

        # Signal 3: temporal cluster pressure (max weight 0.2)
        cluster_score = min(0.2, cluster_size * 0.07)

        confidence = round(min(1.0, burn_score + recurrence_score + cluster_score), 3)

        if confidence >= 0.7:
            prediction, action = "high", "Proactively scale or rollback before the next alert fires."
        elif confidence >= 0.4:
            prediction, action = "medium", "Increase monitoring cadence; prepare remediation playbook."
        elif confidence >= 0.2:
            prediction, action = "low", "Monitor SLO burn trend; no immediate action required."
        else:
            prediction, action = "none", "Service appears healthy."

        return {
            "service": service,
            "prediction": prediction,
            "confidence": confidence,
            "factors": {
                "burn_rate": burn_rate,
                "burn_label": burn_label,
                "budget_remaining_pct": budget_remaining,
                "memory_item_count": len(memory_items),
                "recent_escalations": recent_bad,
                "cluster_size": cluster_size,
            },
            "recommended_action": action,
        }
