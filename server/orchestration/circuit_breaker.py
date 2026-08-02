from __future__ import annotations
import time
from enum import Enum
from typing import Any


class CircuitState(str, Enum):
    CLOSED    = "closed"     # normal — requests pass through
    OPEN      = "open"       # tripped — requests blocked immediately
    HALF_OPEN = "half_open"  # testing recovery — one request allowed


class CircuitBreaker:
    """Per-dependency circuit breaker.

    CLOSED → OPEN when failures reach threshold.
    OPEN → HALF_OPEN after recovery_timeout seconds.
    HALF_OPEN → CLOSED on success, back to OPEN on failure.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
    ) -> None:
        self.name = name
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._threshold = failure_threshold
        self._recovery_timeout = recovery_timeout_seconds
        self._last_failure_ts: float = 0.0
        self._total_calls = 0
        self._total_blocked = 0

    def can_execute(self) -> bool:
        self._total_calls += 1
        if self._state == CircuitState.CLOSED:
            return True
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_ts > self._recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                return True
            self._total_blocked += 1
            return False
        return True  # HALF_OPEN: let one through

    def record_success(self) -> None:
        self._failures = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self._failures += 1
        self._last_failure_ts = time.monotonic()
        if self._failures >= self._threshold or self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN

    def reset(self) -> None:
        self._state = CircuitState.CLOSED
        self._failures = 0

    @property
    def state(self) -> CircuitState:
        return self._state

    def status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self._state,
            "failures": self._failures,
            "threshold": self._threshold,
            "total_calls": self._total_calls,
            "total_blocked": self._total_blocked,
        }


class CircuitBreakerRegistry:
    """Manages a named set of circuit breakers for all external dependencies."""

    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}

    def get(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 30.0) -> CircuitBreaker:
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, failure_threshold, recovery_timeout)
        return self._breakers[name]

    def all_status(self) -> dict[str, Any]:
        return {name: cb.status() for name, cb in self._breakers.items()}
