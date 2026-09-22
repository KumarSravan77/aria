from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.agents.platform_agents_router import router
from server.api.security import require_auth
from server.models.schemas import UserContext


def _client(user: UserContext) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: user
    return TestClient(app)


def test_kafka_endpoint_requires_service_access_and_sre_role():
    request = {"incident": {"service": "payment-events", "topic": "payments", "consumer_group": "fraud-detector"}}
    allowed = _client(UserContext(id="test-sre", role="sre", team="platform"))
    assert allowed.post("/platform-agents/kafka", json=request).status_code == 200

    unowned = {"incident": {**request["incident"], "service": "other-service"}}
    assert allowed.post("/platform-agents/kafka", json=unowned).status_code == 403

    viewer = _client(UserContext(id="test-sre", role="viewer", team="platform"))
    assert viewer.post("/platform-agents/kafka", json=request).status_code == 403

    assert allowed.post("/platform-agents/kafka", json={"incident": {"topic": "payments"}}).status_code == 403
