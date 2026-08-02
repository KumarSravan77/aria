from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DegradationContract:
    available: bool
    degraded: bool
    reason: str
    source: str

    def as_dict(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {
            "available": self.available,
            "degraded": self.degraded,
            "reason": self.reason,
            "source": self.source,
        }
        if extra:
            payload.update(extra)
        return payload


def degraded(source: str, reason: str, **extra: Any) -> dict[str, Any]:
    return DegradationContract(False, True, reason, source).as_dict(extra)


def available(source: str, **extra: Any) -> dict[str, Any]:
    return DegradationContract(True, False, "ok", source).as_dict(extra)
