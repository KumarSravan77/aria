from __future__ import annotations
from dataclasses import dataclass
from server.chaos.experiment_catalog import list_experiments

@dataclass
class ChaosScheduler:
    """Creates recurring chaos drill plans. Execution remains explicit/dry-run by default."""
    default_day: str = "FRI"
    default_hour_utc: int = 15

    def plan_weekly(self, service: str, namespace: str = "demo", experiments: list[str] | None = None) -> dict:
        catalog = {item["name"] for item in list_experiments()}
        selected = experiments or ["pod-delete", "cpu-hog"]
        invalid = [name for name in selected if name not in catalog]
        return {
            "service": service,
            "namespace": namespace,
            "enabled": False,
            "schedule": f"RRULE:FREQ=WEEKLY;BYDAY={self.default_day};BYHOUR={self.default_hour_utc};BYMINUTE=0;BYSECOND=0",
            "experiments": selected,
            "invalid_experiments": invalid,
            "safety": "Schedule is a plan only. Enable through Celery beat or external scheduler after approval.",
        }
