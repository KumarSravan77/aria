from __future__ import annotations
import json
from server.config import settings
from server.utils_time import utc_now

class EventBus:
    def __init__(self, backend: str | None = None):
        self.backend = backend or settings.event_bus_backend
        self._redis = None
        if self.backend == "redis":
            try:
                import redis
                self._redis = redis.from_url(settings.redis_url)
            except Exception:
                self._redis = None

    def publish(self, topic: str, payload: dict) -> dict:
        event = {"topic": topic, "payload": payload, "published_at": utc_now().isoformat()}
        if self.backend == "redis" and self._redis is not None:
            self._redis.publish(topic, json.dumps(event, default=str))
            return {**event, "backend": "redis"}
        print(json.dumps(event, default=str))
        return {**event, "backend": "stdout"}

event_bus = EventBus()
