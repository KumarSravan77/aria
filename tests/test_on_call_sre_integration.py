import json

from server.integrations.on_call_sre import (
    IntelligencePublishRequest,
    OnCallSREClient,
    SignalEvidence,
)


class Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {"incident_id": "incident-1", "status": "triggered"}


def request() -> IntelligencePublishRequest:
    return IntelligencePublishRequest(
        signal_id="signal-12345",
        service="checkout-api",
        severity="critical",
        title="Checkout failure correlated across telemetry",
        summary="ARIA correlated errors with a recent deployment.",
        confidence=0.91,
        evidence=[
            SignalEvidence(
                source="tempo",
                uri="tempo://trace/abc",
                summary="Database spans became slow after the deployment.",
            )
        ],
        recommended_actions=["Inspect the deployment before requesting rollback"],
    )


def test_signed_on_call_delivery(monkeypatch):
    captured = {}

    def post(url, data, headers, timeout):
        captured.update(url=url, data=data, headers=headers, timeout=timeout)
        return Response()

    monkeypatch.setattr("server.integrations.on_call_sre.requests.post", post)
    result = OnCallSREClient("https://on-call.example.test", "shared-secret").publish(request())

    assert result["available"] is True
    assert captured["url"].endswith("/api/v1/intelligence/aria")
    assert captured["headers"]["X-ARIA-Signature"].startswith("sha256=")
    assert json.loads(captured["data"])["schema_version"] == "1.0"


def test_unconfigured_on_call_degrades_gracefully():
    result = OnCallSREClient("", "").publish(request())
    assert result == {"available": False, "error": "on-call integration is not configured"}
