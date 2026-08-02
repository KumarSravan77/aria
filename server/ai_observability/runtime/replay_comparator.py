from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ReplayComparator:
    def compare(self, before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
        before_route = before.get("route") or before.get("summary", {}).get("route", [])
        after_route = after.get("route") or after.get("summary", {}).get("route", [])
        return {
            "route_changed": before_route != after_route,
            "before_route": before_route,
            "after_route": after_route,
            "added_nodes": sorted(set(after_route) - set(before_route)),
            "removed_nodes": sorted(set(before_route) - set(after_route)),
            "before_score": before.get("score"),
            "after_score": after.get("score"),
        }
