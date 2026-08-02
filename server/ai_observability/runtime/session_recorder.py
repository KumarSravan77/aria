from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json
import uuid
import time

from server.ai_observability.runtime.event_schema import RuntimeEvent


@dataclass
class AiRuntimeSessionRecorder:
    log_path: Path = Path("logs/ai_runtime_debug.jsonl")
    sessions: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def start_session(self, incident_id: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        session_id = str(uuid.uuid4())
        self.record(session_id, "session_started", incident_id=incident_id, metadata=metadata or {})
        return {"session_id": session_id, "incident_id": incident_id}

    def record(self, session_id: str, event_type: str, **kwargs: Any) -> dict[str, Any]:
        event = RuntimeEvent(session_id=session_id, event_type=event_type, **kwargs).as_dict()
        self.sessions.setdefault(session_id, []).append(event)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a") as f:
            f.write(json.dumps(event, default=str) + "\n")
        return event

    def list_events(self, session_id: str) -> list[dict[str, Any]]:
        if session_id in self.sessions:
            return self.sessions[session_id]
        if not self.log_path.exists():
            return []
        events = []
        for line in self.log_path.read_text().splitlines():
            try:
                item = json.loads(line)
                if item.get("session_id") == session_id:
                    events.append(item)
            except Exception:
                continue
        return events

    def summary(self, session_id: str) -> dict[str, Any]:
        events = self.list_events(session_id)
        tokens_in = sum(e.get("input_tokens", 0) for e in events)
        tokens_out = sum(e.get("output_tokens", 0) for e in events)
        cached = sum(e.get("cached_tokens", 0) for e in events)
        errors = [e for e in events if e.get("status") == "error"]
        duration = 0
        timestamps = [e.get("timestamp") for e in events if e.get("timestamp")]
        if timestamps:
            duration = max(timestamps) - min(timestamps)
        return {
            "session_id": session_id,
            "event_count": len(events),
            "error_count": len(errors),
            "input_tokens": tokens_in,
            "output_tokens": tokens_out,
            "cached_tokens": cached,
            "cache_hit_rate": round(cached / max(tokens_in + cached, 1), 4),
            "duration_seconds": round(duration, 3),
        }
