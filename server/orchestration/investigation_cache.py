from __future__ import annotations
import time
from typing import Any


class InvestigationCache:
    """Short-TTL cache for repeated investigation results on identical incidents.

    Keyed by (service, probable_cause) — common in alert storms where the same
    root cause fires across multiple pods. Reduces LLM/RAG calls significantly.
    """

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl = ttl_seconds
        self._store: dict[str, tuple[Any, float]] = {}
        self._hits = 0
        self._misses = 0

    def _key(self, service: str, probable_cause: str) -> str:
        return f"{service.lower()}:{probable_cause.lower()}"

    def get(self, service: str, probable_cause: str) -> Any | None:
        key = self._key(service, probable_cause)
        entry = self._store.get(key)
        if entry:
            value, ts = entry
            if time.monotonic() - ts < self.ttl:
                self._hits += 1
                return value
            del self._store[key]
        self._misses += 1
        return None

    def set(self, service: str, probable_cause: str, result: Any) -> None:
        self._store[self._key(service, probable_cause)] = (result, time.monotonic())

    def invalidate(self, service: str) -> int:
        keys_removed = [k for k in list(self._store) if k.startswith(f"{service.lower()}:")]
        for k in keys_removed:
            del self._store[k]
        return len(keys_removed)

    def metrics(self) -> dict[str, Any]:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 3) if total else 0.0,
            "cached_entries": len(self._store),
            "ttl_seconds": self.ttl,
        }
