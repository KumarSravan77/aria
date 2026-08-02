from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import os, time, uuid

@dataclass
class AriaAiTrace:
    trace_id: str
    name: str
    input: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    observations: list[dict[str, Any]] = field(default_factory=list)
    scores: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class LangfuseClient:
    """Langfuse-compatible boundary. Falls back to local no-op mode."""
    host: str | None = None
    public_key: str | None = None
    secret_key: str | None = None

    def __post_init__(self) -> None:
        self.host = self.host or os.getenv("LANGFUSE_HOST")
        self.public_key = self.public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = self.secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        self.enabled = bool(self.host and self.public_key and self.secret_key)

    def start_trace(self, name: str, input: dict[str, Any], metadata: dict[str, Any] | None = None) -> AriaAiTrace:
        return AriaAiTrace(str(uuid.uuid4()), name, input, metadata or {})

    def observe(self, trace: AriaAiTrace, name: str, input: Any, output: Any, metadata: dict[str, Any] | None = None) -> None:
        trace.observations.append({
            "name": name, "input": input, "output": output,
            "metadata": metadata or {}, "timestamp": time.time(),
            "exported": self.enabled
        })

    def add_observation(self, trace: AriaAiTrace, name: str, input: Any, output: Any, metadata: dict[str, Any] | None = None) -> None:
        """Backward-compatible helper for older exporter modules."""
        self.observe(trace, name, input, output, metadata)

    def score(self, trace: AriaAiTrace, name: str, value: float, comment: str | None = None) -> None:
        trace.scores.append({
            "name": name, "value": value, "comment": comment,
            "timestamp": time.time(), "exported": self.enabled
        })

    def flush(self, trace: AriaAiTrace) -> dict[str, Any]:
        return {
            "available": self.enabled,
            "mode": "langfuse" if self.enabled else "local_noop",
            "trace_id": trace.trace_id,
            "trace_name": trace.name,
            "observation_count": len(trace.observations),
            "score_count": len(trace.scores),
        }


# Backward-compatible alias used by trace exporters.
LangfuseTrace = AriaAiTrace
