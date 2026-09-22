import hashlib
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.api.security import require_auth
from server.integrations.fire_drill import FireDrillInvestigationRequest, investigate_fire_drill, router
from server.models.schemas import UserContext


class StubKafkaAgent:
    def run(self, incident, context):
        return {
            "agent": "kafka",
            "service": incident["service"],
            "available": True,
            "context_experiment": context["experiment_id"],
            "safety_boundary": "read-only",
        }


def payload() -> FireDrillInvestigationRequest:
    observation = {"consumer_lag": 20000}
    digest = "sha256:" + hashlib.sha256(json.dumps(observation, sort_keys=True).encode()).hexdigest()
    return FireDrillInvestigationRequest.model_validate({
        "incident": {
            "incident_id": "stream-123", "service": "payment-events", "severity": "P2",
            "source": "fire-drill", "signals": ["kafka", "CONSUMER_LAG"],
            "topic": "payments", "consumer_group": "fraud-detector",
        },
        "context": {
            "experiment_id": "drill-123", "event_id": "event-123",
            "plan_digest": "sha256:" + "a" * 64, "evidence_digest": digest,
            "scenario": "network-latency", "environment": "staging",
            "evidence_mode": "synthetic",
            "approved_by": "reliability-reviewer", "blast_radius_percent": 10,
            "automatic_remediation": False,
            "streaming_observation": observation,
            "findings": [{"code": "CONSUMER_LAG"}],
            "slo": {"burn_rate": 2.0},
            "fire_drill_report": {"detection_seconds": 12, "recovery_seconds": 45},
        },
    })


def test_fire_drill_intake_preserves_evidence_chain() -> None:
    result = investigate_fire_drill(payload(), StubKafkaAgent())
    assert result["experiment_id"] == "drill-123"
    assert result["plan_digest"] == "sha256:" + "a" * 64
    assert result["evidence_digest"] == payload().context.evidence_digest
    assert result["investigation"]["agent"] == "kafka"
    assert result["automatic_remediation"] is False
    assert result["decision"] == "human-review-required"
    assert result["evidence_mode"] == "synthetic"
    assert result["observation"]["consumer_lag"] == 20000
    assert result["findings"][0]["code"] == "CONSUMER_LAG"
    assert result["fire_drill_report"]["recovery_seconds"] == 45


def test_production_environment_is_rejected() -> None:
    raw = payload().model_dump()
    raw["context"]["environment"] = "production"
    try:
        FireDrillInvestigationRequest.model_validate(raw)
        raise AssertionError("production Fire Drill evidence must be rejected")
    except ValueError:
        pass


def test_tampered_observation_is_rejected() -> None:
    request = payload()
    request.context.streaming_observation["consumer_lag"] = 0
    with pytest.raises(ValueError, match="digest mismatch"):
        investigate_fire_drill(request, StubKafkaAgent())


def test_endpoint_enforces_service_access_and_digest() -> None:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: UserContext(id="test-sre", role="sre", team="platform")
    client = TestClient(app)
    allowed = payload().model_dump(mode="json")
    response = client.post("/integrations/fire-drill/streaming", json=allowed)
    assert response.status_code == 200
    assert response.json()["qualification_verdict"] == "ACTION_REQUIRED"

    denied = payload().model_dump(mode="json")
    denied["incident"]["service"] = "unowned-service"
    assert client.post("/integrations/fire-drill/streaming", json=denied).status_code == 403

    tampered = payload().model_dump(mode="json")
    tampered["context"]["streaming_observation"]["consumer_lag"] = 0
    assert client.post("/integrations/fire-drill/streaming", json=tampered).status_code == 422
