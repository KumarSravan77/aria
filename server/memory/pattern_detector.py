from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from typing import Any

@dataclass
class PatternDetector:
    def detect(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        if not records:
            return {"pattern": "needs_more_data", "count": 0, "recommendations": []}
        keys = [r.get("root_cause") or r.get("outcome") or r.get("scenario") or "unknown" for r in records]
        counts = Counter(keys)
        top, count = counts.most_common(1)[0]
        recurring = count >= 3
        return {
            "pattern": "recurring" if recurring else "emerging",
            "top_pattern": top,
            "count": count,
            "recommendations": [
                "create preventive runbook",
                "add SLO burn alert",
                "tighten rollout policy",
            ] if recurring else ["continue collecting operational memory"],
        }
