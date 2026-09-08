from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid

import requests


@dataclass
class EnvoyAIGatewayClient:
    """OpenAI-compatible client for Envoy AI Gateway.

    ARIA deliberately speaks only the gateway's downstream API. Provider
    credentials and provider-specific request transformations belong at the
    gateway, not in the application process.
    """

    base_url: str = "http://localhost:1975"
    model: str = "aria-reasoning"
    timeout_seconds: int = 90
    api_key: str | None = None
    tenant_id: str = "aria"
    agent_id: str = "incident-reasoner"
    extra_headers: dict[str, str] = field(default_factory=dict)

    def generate(self, prompt: str, *, system: str | None = None) -> dict[str, Any]:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        request_id = str(uuid.uuid4())
        headers = {
            "Content-Type": "application/json",
            "x-aria-request-id": request_id,
            "x-tenant-id": self.tenant_id,
            "x-aria-agent-id": self.agent_id,
            # Envoy AI Gateway uses this header for AIGatewayRoute model matching.
            "x-ai-eg-model": self.model,
            **self.extra_headers,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        try:
            response = requests.post(
                f"{self.base_url.rstrip('/')}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices") or []
            content = ""
            if choices:
                content = ((choices[0].get("message") or {}).get("content") or "")
            return {
                "available": True,
                "provider": "envoy-ai-gateway",
                "model": data.get("model") or self.model,
                "requested_model": self.model,
                "response": content,
                "request_id": request_id,
                "usage": data.get("usage") or {},
                "raw": data,
            }
        except Exception as exc:  # pragma: no cover - exercised in integration runs
            return {
                "available": False,
                "provider": "envoy-ai-gateway",
                "model": self.model,
                "requested_model": self.model,
                "response": "Envoy AI Gateway is unavailable. Falling back to deterministic analysis and retrieved runbooks.",
                "request_id": request_id,
                "error": str(exc),
            }
