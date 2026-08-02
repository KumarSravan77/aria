from __future__ import annotations

from typing import Any
from server.llm.ollama_client import OllamaClient
from server.llm.prompt_templates import INCIDENT_REASONING_SYSTEM, INCIDENT_REASONING_TEMPLATE


class IncidentReasoner:
    """Hybrid AI reasoner: deterministic evidence + RAG + local LLM summary."""

    def __init__(self, client: OllamaClient | None = None):
        self.client = client or OllamaClient()

    def reason(self, incident: dict[str, Any], analysis: dict[str, Any], rag_context: dict[str, Any]) -> dict[str, Any]:
        prompt = INCIDENT_REASONING_TEMPLATE.format(
            incident=incident,
            analysis=analysis,
            rag_context=rag_context,
        )
        result = self.client.generate(prompt, system=INCIDENT_REASONING_SYSTEM)
        return {
            "mode": "ollama-local" if result.get("available") else "deterministic-fallback",
            "model": result.get("model"),
            "summary": result.get("response"),
            "safety_boundary": "LLM recommends only; ReBAC, policy, approval, and executor own actions.",
            "raw": result,
        }
