from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class OllamaClient:
    """Small local-first Ollama client.

    The platform treats Ollama as a reasoning/summarization provider only.
    It must never execute remediation actions directly.
    """

    base_url: str = "http://localhost:11434"
    model: str = "llama3.1:8b"
    timeout_seconds: int = 60

    def generate(self, prompt: str, *, system: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        try:
            response = requests.post(
                f"{self.base_url.rstrip('/')}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "available": True,
                "model": self.model,
                "response": data.get("response", ""),
                "raw": data,
            }
        except Exception as exc:  # pragma: no cover - exercised in integration runs
            return {
                "available": False,
                "model": self.model,
                "response": "Ollama is unavailable. Falling back to deterministic analysis and retrieved runbooks.",
                "error": str(exc),
            }
