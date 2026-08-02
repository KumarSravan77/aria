from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from server.ai_observability.langfuse_client import LangfuseClient


@dataclass
class TraceBuilder:
    client: LangfuseClient

    def investigation_trace(self, incident_id: str, service: str, query: str) -> Any:
        return self.client.start_trace(
            "aria.incident.investigation",
            {"incident_id": incident_id, "service": service, "query": query},
            {"system": "aria", "trace_type": "incident_investigation"},
        )
