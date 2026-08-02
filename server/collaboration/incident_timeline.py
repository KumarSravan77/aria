from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List


class IncidentTimeline:
    """In-memory incident timeline for local demos.

    Production options: PostgreSQL, Redis Streams, OpenSearch, or an event bus.
    """

    def __init__(self) -> None:
        self._events: Dict[str, List[Dict[str, Any]]] = {}

    def add(self, incident_id: str, event_type: str, message: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "incident_id": incident_id,
            "event_type": event_type,
            "message": message,
            "metadata": metadata or {},
        }
        self._events.setdefault(incident_id, []).append(event)
        return event

    def list(self, incident_id: str) -> List[Dict[str, Any]]:
        return self._events.get(incident_id, [])
