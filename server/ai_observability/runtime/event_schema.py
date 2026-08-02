from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import time
import uuid


@dataclass
class RuntimeEvent:
    session_id: str
    event_type: str
    incident_id: str | None = None
    node: str | None = None
    tool: str | None = None
    status: str = "success"
    duration_ms: float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__
