from __future__ import annotations

from server.config import Settings
from server.llm.envoy_ai_gateway_client import EnvoyAIGatewayClient
from server.llm.ollama_client import OllamaClient


def build_llm_client(settings: Settings):
    """Build ARIA's reasoning client without leaking provider details upstream."""
    provider = settings.llm_provider.strip().lower()
    if provider == "envoy-ai-gateway":
        return EnvoyAIGatewayClient(
            base_url=settings.ai_gateway_base_url,
            model=settings.ai_gateway_model,
            timeout_seconds=settings.llm_timeout_seconds,
            api_key=settings.ai_gateway_api_key,
            tenant_id=settings.ai_gateway_tenant_id,
            agent_id="incident-reasoner",
        )
    if provider == "ollama":
        return OllamaClient(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    raise ValueError(f"Unsupported LLM_PROVIDER={settings.llm_provider!r}")


def effective_model(settings: Settings) -> str:
    if settings.llm_provider.strip().lower() == "envoy-ai-gateway":
        return settings.ai_gateway_model
    return settings.ollama_model
