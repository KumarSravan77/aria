from __future__ import annotations
import time


class NonceStore:
    """Replay-attack prevention via single-use nonces.

    Primary backend: Redis SET nx ex — atomic, cluster-safe, auto-expiring.
    Fallback: in-process dict for unit tests and deployments without Redis.

    TTL is set to 2 × timestamp_tolerance so a nonce near the edge of the
    tolerance window is still tracked until the request would already be
    rejected on timestamp grounds.
    """

    def __init__(self) -> None:
        self._redis = None
        self._memory: dict[str, float] = {}
        try:
            import redis as redis_lib
            from server.config import settings
            client = redis_lib.from_url(settings.redis_url, socket_connect_timeout=2,
                                        socket_timeout=2, decode_responses=True)
            client.ping()
            self._redis = client
        except Exception:
            self._redis = None

    def consume(self, nonce: str, ttl: int = 600) -> bool:
        """Mark nonce as used. Returns True (first use) or False (replay)."""
        if self._redis is not None:
            # SET key 1 NX EX ttl: atomic set-if-not-exists with expiry
            return bool(self._redis.set(f"nonce:{nonce}", 1, nx=True, ex=ttl))
        # In-memory fallback
        now = time.monotonic()
        self._memory = {k: v for k, v in self._memory.items() if v > now}
        if nonce in self._memory:
            return False
        self._memory[nonce] = now + ttl
        return True


# Module-level singleton — persists across requests within one process.
nonce_store = NonceStore()
