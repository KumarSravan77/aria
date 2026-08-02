from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentStats:
    successes: int = 0
    failures: int = 0
    total_latency_ms: float = 0.0
    quarantined: bool = False


class AgentHealthTracker:
    """Tracks per-agent latency and failure rates for health scoring.

    Agents with health_score < threshold are quarantined and excluded from
    orchestration runs until they recover (manual reset or auto-recovery
    after a configurable window).
    """

    QUARANTINE_THRESHOLD = 0.3  # health score below this → quarantine
    MIN_SAMPLES = 3              # need at least this many calls before quarantining

    def __init__(self) -> None:
        self._stats: dict[str, AgentStats] = {}

    def _get(self, name: str) -> AgentStats:
        if name not in self._stats:
            self._stats[name] = AgentStats()
        return self._stats[name]

    def record(self, name: str, success: bool, latency_ms: float) -> None:
        s = self._get(name)
        if success:
            s.successes += 1
        else:
            s.failures += 1
        s.total_latency_ms += latency_ms
        total = s.successes + s.failures
        if total >= self.MIN_SAMPLES and self.health_score(name) < self.QUARANTINE_THRESHOLD:
            s.quarantined = True

    def health_score(self, name: str) -> float:
        """0.0 (all failures) to 1.0 (all successes). Returns 1.0 for unseen agents."""
        s = self._stats.get(name)
        if not s:
            return 1.0
        total = s.successes + s.failures
        return round(s.successes / total, 3) if total > 0 else 1.0

    def avg_latency_ms(self, name: str) -> float:
        s = self._stats.get(name)
        if not s:
            return 0.0
        total = s.successes + s.failures
        return round(s.total_latency_ms / total, 1) if total > 0 else 0.0

    def is_healthy(self, name: str, threshold: float | None = None) -> bool:
        s = self._stats.get(name)
        if s and s.quarantined:
            return False
        return self.health_score(name) >= (threshold or self.QUARANTINE_THRESHOLD)

    def reset(self, name: str) -> None:
        if name in self._stats:
            self._stats[name].quarantined = False
            self._stats[name].failures = 0
            self._stats[name].successes = 0

    def summary(self) -> dict[str, Any]:
        return {
            name: {
                "health_score": self.health_score(name),
                "avg_latency_ms": self.avg_latency_ms(name),
                "quarantined": s.quarantined,
                "successes": s.successes,
                "failures": s.failures,
            }
            for name, s in self._stats.items()
        }
