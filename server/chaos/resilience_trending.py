from __future__ import annotations
from collections import Counter

class ResilienceTrending:
    """Summarizes chaos/recovery outcomes from OperationalMemory records."""
    def trend(self, service: str, memory_result: dict) -> dict:
        items = memory_result.get("items", [])
        scores = []
        outcomes = Counter()
        for item in items:
            outcomes[item.get("outcome", "unknown")] += 1
            meta = item.get("metadata", {}) or {}
            score = meta.get("resilience_score") or meta.get("score")
            if isinstance(score, (int, float)):
                scores.append(float(score))
        avg = round(sum(scores) / len(scores), 2) if scores else None
        return {
            "service": service,
            "records": len(items),
            "average_resilience_score": avg,
            "outcomes": dict(outcomes),
            "trend": "improving" if avg and avg >= 80 else "needs_more_data" if not scores else "watch",
        }
