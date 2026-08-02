from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections import defaultdict


@dataclass
class MemoryCompactor:
    def compact(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            key = record.get("service") or record.get("root_cause") or record.get("scenario") or "unknown"
            grouped[key].append(record)

        summaries = []
        for key, items in grouped.items():
            causes = {}
            for item in items:
                cause = item.get("root_cause") or item.get("outcome") or "unknown"
                causes[cause] = causes.get(cause, 0) + 1
            summaries.append({
                "key": key,
                "count": len(items),
                "top_causes": sorted(causes.items(), key=lambda x: x[1], reverse=True)[:5],
            })

        return {
            "input_records": len(records),
            "summary_count": len(summaries),
            "summaries": summaries,
            "policy": "raw records can be archived after summarization and embedding",
        }
