from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChaosBeatSchedule:
    def weekly_plan(self, service: str = "checkout-api") -> dict:
        return {
            "enabled": False,
            "service": service,
            "schedule": "RRULE:FREQ=WEEKLY;BYDAY=FR;BYHOUR=10;BYMINUTE=0",
            "tasks": [
                {"experiment": "pod-delete", "dry_run": True},
                {"experiment": "network-latency", "dry_run": True},
            ],
            "safety": "disabled by default; enable only in sandbox clusters",
        }
