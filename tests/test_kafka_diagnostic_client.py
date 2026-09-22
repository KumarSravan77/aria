from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

from server.platform.streaming.kafka.client import KafkaDiagnosticClient


class Future:
    def __init__(self, value):
        self.value = value

    def result(self, timeout=None):
        return self.value


class TopicPartition:
    def __init__(self, topic, partition, offset=-1, error=None):
        self.topic = topic
        self.partition = partition
        self.offset = offset
        self.error = error

    def __hash__(self):
        return hash((self.topic, self.partition))

    def __eq__(self, other):
        return isinstance(other, TopicPartition) and (self.topic, self.partition) == (other.topic, other.partition)


class ConsumerGroupTopicPartitions:
    def __init__(self, group_id, topic_partitions=None):
        self.group_id = group_id
        self.topic_partitions = topic_partitions


class OffsetSpec:
    @staticmethod
    def latest():
        return "latest"


class FakeAdmin:
    def __init__(self, config, committed=None):
        self.config = config
        self.committed = committed or {0: 90, 1: 70}
        self.calls = []
        self.metadata = SimpleNamespace(
            brokers={1: object()},
            topics={"payments": SimpleNamespace(
                error=None,
                partitions={
                    0: SimpleNamespace(error=None, leader=1, replicas=[1, 2], isrs=[1, 2]),
                    1: SimpleNamespace(error=None, leader=1, replicas=[1, 2], isrs=[1]),
                },
            )},
        )

    def list_topics(self, *args, **kwargs):
        self.calls.append(("list_topics", args, kwargs))
        assert not args and "topic" not in kwargs
        return self.metadata

    def list_consumer_group_offsets(self, requests, **kwargs):
        self.calls.append(("list_consumer_group_offsets", requests, kwargs))
        assert requests[0].group_id == "fraud-detector"
        rows = [TopicPartition("payments", p, offset) for p, offset in self.committed.items()]
        return {"fraud-detector": Future(ConsumerGroupTopicPartitions("fraud-detector", rows))}

    def list_offsets(self, requests, **kwargs):
        self.calls.append(("list_offsets", requests, kwargs))
        assert all(value == "latest" for value in requests.values())
        return {tp: Future(SimpleNamespace(offset={0: 100, 1: 100}[tp.partition])) for tp in requests}


def fake_kafka(monkeypatch, admin):
    package = ModuleType("confluent_kafka")
    admin_module = ModuleType("confluent_kafka.admin")
    package.TopicPartition = TopicPartition
    admin_module.ConsumerGroupTopicPartitions = ConsumerGroupTopicPartitions
    admin_module.OffsetSpec = OffsetSpec
    def admin_factory(config):
        admin.config = config
        return admin

    admin_module.AdminClient = admin_factory
    monkeypatch.setitem(sys.modules, "confluent_kafka", package)
    monkeypatch.setitem(sys.modules, "confluent_kafka.admin", admin_module)


def test_live_metadata_and_offsets_are_scoped_and_read_only(monkeypatch):
    admin = FakeAdmin({})
    fake_kafka(monkeypatch, admin)
    client = KafkaDiagnosticClient(bootstrap_servers="broker:9092")
    monkeypatch.setattr(client, "_admin", lambda: admin)

    assert client.cluster_health()["broker_count"] == 1
    topic = client.topic_health("payments")
    assert topic["partition_count"] == 2
    assert topic["under_replicated_partitions"] == [1]
    lag = client.consumer_group_lag("fraud-detector", "payments")
    assert lag["available"] is True
    assert lag["total_lag"] == 40
    assert [row["lag"] for row in lag["partitions"]] == [10, 30]
    assert {name for name, _, _ in admin.calls} == {
        "list_topics", "list_consumer_group_offsets", "list_offsets"
    }


def test_missing_committed_offset_is_unknown_not_zero(monkeypatch):
    admin = FakeAdmin({}, committed={0: 90})
    fake_kafka(monkeypatch, admin)
    client = KafkaDiagnosticClient(bootstrap_servers="broker:9092")
    monkeypatch.setattr(client, "_admin", lambda: admin)

    lag = client.consumer_group_lag("fraud-detector", "payments")
    assert lag["available"] is False
    assert lag["partial"] is True
    assert lag["unknown_partitions"] == [1]
    assert lag["total_lag"] is None


def test_unknown_topic_does_not_get_requested_or_created(monkeypatch):
    admin = FakeAdmin({})
    fake_kafka(monkeypatch, admin)
    client = KafkaDiagnosticClient(bootstrap_servers="broker:9092")
    monkeypatch.setattr(client, "_admin", lambda: admin)

    assert client.topic_health("absent")["reason"] == "topic_not_found_or_not_authorized"
    assert client.consumer_group_lag("fraud-detector", "absent")["available"] is False
    assert all(name == "list_topics" for name, _, _ in admin.calls)


def test_queries_are_bounded_and_errors_do_not_leak_credentials(monkeypatch):
    admin = FakeAdmin({})
    fake_kafka(monkeypatch, admin)
    client = KafkaDiagnosticClient(bootstrap_servers="broker:9092", max_partitions=1)
    monkeypatch.setattr(client, "_admin", lambda: admin)
    assert client.consumer_group_lag("fraud-detector", "payments")["reason"] == "partition_limit"

    def fail():
        raise RuntimeError("secret-password at broker:9092")

    monkeypatch.setattr(client, "_metadata", fail)
    result = client.cluster_health()
    assert result["available"] is False
    assert "secret-password" not in str(result)


def test_security_options_are_configured_but_not_returned(monkeypatch):
    admin = FakeAdmin({})
    fake_kafka(monkeypatch, admin)
    monkeypatch.setenv("KAFKA_SASL_PASSWORD", "private-password")
    monkeypatch.setenv("KAFKA_SECURITY_PROTOCOL", "SASL_SSL")
    client = KafkaDiagnosticClient(bootstrap_servers="broker:9092")
    assert client._admin() is admin
    assert admin.config["sasl.password"] == "private-password"
    assert admin.config["security.protocol"] == "SASL_SSL"
    assert admin.config["allow.auto.create.topics"] is False
    assert "private-password" not in str(client.cluster_health())
