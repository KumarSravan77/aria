from pathlib import Path

from server.agents.kafka_agent import KafkaAgent
from server.platform.streaming.kafka.scopes import KafkaResourceScope


class NeverCalledClient:
    def cluster_health(self):
        raise AssertionError("broker must not be contacted for an unmapped resource")

    def consumer_group_lag(self, **kwargs):
        raise AssertionError("broker must not be contacted for an unmapped resource")

    def topic_health(self, **kwargs):
        raise AssertionError("broker must not be contacted for an unmapped resource")


def test_scope_requires_exact_service_topic_group():
    policy = KafkaResourceScope()
    assert policy.allows("payment-events", "payments", "fraud-detector")
    assert not policy.allows("payment-events", "other-topic", "fraud-detector")
    assert not policy.allows("payment-events", "payments", "other-group")
    assert not policy.allows("other-service", "payments", "fraud-detector")


def test_missing_policy_fails_closed(tmp_path: Path):
    assert not KafkaResourceScope(tmp_path / "missing.yaml").allows("payment-events", "payments", "fraud-detector")


def test_agent_does_not_contact_broker_outside_resource_scope():
    agent = KafkaAgent(client=NeverCalledClient())
    result = agent.run({
        "service": "payment-events", "topic": "private-topic", "consumer_group": "fraud-detector",
        "signals": ["consumer lag"],
    })
    assert result["available"] is False
    assert result["cluster"]["reason"] == "resource_scope_denied"
    assert result["live_evidence_complete"] is False
