from __future__ import annotations

from unittest.mock import Mock, patch

from server.llm.envoy_ai_gateway_client import EnvoyAIGatewayClient
from server.llm.incident_reasoner import IncidentReasoner


def test_gateway_client_uses_openai_compatible_endpoint_and_correlation_headers():
    client = EnvoyAIGatewayClient(
        base_url="http://gateway.internal",
        model="aria-reasoning",
        tenant_id="platform",
        agent_id="rca-agent",
    )
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "model": "physical-provider-model",
        "choices": [{"message": {"content": "Investigate the deployment."}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }

    with patch("server.llm.envoy_ai_gateway_client.requests.post", return_value=response) as post:
        result = client.generate("what happened?", system="be grounded")

    assert result["available"] is True
    assert result["provider"] == "envoy-ai-gateway"
    assert result["response"] == "Investigate the deployment."
    args, kwargs = post.call_args
    assert args[0] == "http://gateway.internal/v1/chat/completions"
    assert kwargs["json"]["model"] == "aria-reasoning"
    assert kwargs["headers"]["x-tenant-id"] == "platform"
    assert kwargs["headers"]["x-aria-agent-id"] == "rca-agent"
    assert kwargs["headers"]["x-ai-eg-model"] == "aria-reasoning"
    assert kwargs["headers"]["x-aria-request-id"]


def test_incident_reasoner_keeps_gateway_output_non_executable():
    fake = Mock()
    fake.generate.return_value = {
        "available": True,
        "provider": "envoy-ai-gateway",
        "model": "aria-reasoning",
        "response": "Consider scaling after policy checks.",
    }
    reasoner = IncidentReasoner(fake)
    result = reasoner.reason({"service": "checkout"}, {"findings": []}, {"documents": []})

    assert result["mode"] == "envoy-ai-gateway"
    assert "ReBAC" in result["safety_boundary"]
    assert "executor" in result["safety_boundary"]
