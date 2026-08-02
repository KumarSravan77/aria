from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from server.ai_observability.langfuse_client import LangfuseClient, LangfuseTrace


@dataclass
class RagTraceExporter:
    client: LangfuseClient

    def record_retrieval(self, trace: LangfuseTrace, query: str, sources: list[dict[str, Any]], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {
            "query": query,
            "source_count": len(sources),
            "sources": [
                {
                    "title": s.get("title") or s.get("source") or "unknown",
                    "service": s.get("service"),
                    "doc_type": s.get("doc_type"),
                }
                for s in sources
            ],
        }
        self.client.add_observation(trace, "rag_retrieval", {"query": query}, payload, metadata)
        return payload
