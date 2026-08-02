from __future__ import annotations
from typing import Any


class BackpressureController:
    """In-process concurrency limiter and queue depth tracker.

    Prevents threadpool exhaustion and Redis contention during alert floods.
    Uses acquire/release semantics; callers must release() in a finally block.
    """

    def __init__(self, max_concurrent: int = 50) -> None:
        self._max = max_concurrent
        self._active = 0
        self._total = 0
        self._rejected = 0

    def acquire(self) -> bool:
        """Returns True if a slot is available, False if at capacity."""
        if self._active >= self._max:
            self._rejected += 1
            return False
        self._active += 1
        self._total += 1
        return True

    def release(self) -> None:
        self._active = max(0, self._active - 1)

    def set_limit(self, limit: int) -> None:
        self._max = limit

    def metrics(self) -> dict[str, Any]:
        return {
            "active": self._active,
            "max_concurrent": self._max,
            "total_processed": self._total,
            "rejected": self._rejected,
            "utilisation_pct": round(100 * self._active / max(1, self._max), 1),
        }
