from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from server.ai_observability.langfuse_client import LangfuseClient, LangfuseTrace


@dataclass
class AgentTraceExporter:
    client: LangfuseClient

    def record_agent(self, trace: LangfuseTrace, agent_name: str, output: dict[str, Any], latency_ms: float | None = None) -> None:
        self.client.add_observation(
            trace,
            f"agent.{agent_name}",
            {"agent": agent_name},
            output,
            {"latency_ms": latency_ms} if latency_ms is not None else {},
        )
