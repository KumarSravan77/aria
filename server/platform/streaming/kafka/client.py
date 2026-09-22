from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import os


@dataclass
class KafkaDiagnosticClient:
    """Bounded, read-only Kafka metadata and offset queries.

    No consumer joins a group, reads records, or commits offsets. Never call
    list_topics(topic=...), which may auto-create an unknown topic.
    """

    bootstrap_servers: str | None = None
    timeout_seconds: float = 5.0
    max_partitions: int = 128

    def __post_init__(self) -> None:
        self.bootstrap_servers = self.bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS")

    def _admin(self):
        from confluent_kafka.admin import AdminClient

        config: dict[str, Any] = {
            "bootstrap.servers": self.bootstrap_servers,
            "socket.timeout.ms": int(self.timeout_seconds * 1000),
            "client.id": "aria-read-only-diagnostics",
            "allow.auto.create.topics": False,
        }
        for env, key in (
            ("KAFKA_SECURITY_PROTOCOL", "security.protocol"),
            ("KAFKA_SASL_MECHANISM", "sasl.mechanism"),
            ("KAFKA_SASL_USERNAME", "sasl.username"),
            ("KAFKA_SASL_PASSWORD", "sasl.password"),
            ("KAFKA_SSL_CA_LOCATION", "ssl.ca.location"),
        ):
            if value := os.getenv(env):
                config[key] = value
        return AdminClient(config)

    @staticmethod
    def _unavailable(reason: str, summary: str, **details: Any) -> dict[str, Any]:
        return {"available": False, "reason": reason, "summary": summary, **details}

    @staticmethod
    def _failure(exc: Exception, summary: str) -> dict[str, Any]:
        # Kafka exception text can contain broker addresses or auth details.
        return KafkaDiagnosticClient._unavailable(type(exc).__name__, summary)

    def _metadata(self):
        # Request cluster metadata, then filter locally; no topic-name request.
        return self._admin().list_topics(timeout=self.timeout_seconds)

    def cluster_health(self) -> dict[str, Any]:
        if not self.bootstrap_servers:
            return self._unavailable("not_configured", "Kafka bootstrap servers are not configured")
        try:
            metadata = self._metadata()
            return {
                "available": bool(metadata.brokers),
                "broker_count": len(metadata.brokers),
                "topic_count": len(metadata.topics),
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "summary": "Kafka metadata reachable" if metadata.brokers else "No Kafka brokers in metadata",
            }
        except ImportError:
            return self._unavailable("client_not_installed", "Kafka client dependency is unavailable")
        except Exception as exc:  # noqa: BLE001
            return self._failure(exc, "Kafka cluster metadata query failed")

    def topic_health(self, topic: str | None = None) -> dict[str, Any]:
        if not topic:
            return self._unavailable("topic_required", "A topic is required for scoped diagnostics")
        if not self.bootstrap_servers:
            return self._unavailable("not_configured", "Kafka bootstrap servers are not configured", topic=topic)
        try:
            metadata = self._metadata()
            target = metadata.topics.get(topic)
            if target is None:
                return self._unavailable("topic_not_found_or_not_authorized", "Topic metadata unavailable", topic=topic)
            if target.error:
                return self._unavailable("topic_metadata_error", "Topic metadata query failed", topic=topic)
            partitions = target.partitions
            if not partitions or len(partitions) > self.max_partitions:
                return self._unavailable("partition_limit", "Topic has no partitions or exceeds diagnostic limit", topic=topic)
            offline = []
            under_replicated = []
            for number, part in sorted(partitions.items()):
                if part.error or part.leader is None or part.leader < 0:
                    offline.append(number)
                if len(part.isrs) < len(part.replicas):
                    under_replicated.append(number)
            return {
                "available": True,
                "topic": topic,
                "partition_count": len(partitions),
                "offline_partitions": offline,
                "under_replicated_partitions": under_replicated,
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "summary": "Kafka topic metadata collected",
            }
        except ImportError:
            return self._unavailable("client_not_installed", "Kafka client dependency is unavailable", topic=topic)
        except Exception as exc:  # noqa: BLE001
            return self._failure(exc, "Kafka topic metadata query failed")

    def consumer_group_lag(self, consumer_group: str | None = None, topic: str | None = None) -> dict[str, Any]:
        if not consumer_group or not topic:
            return self._unavailable("scope_required", "Consumer group and topic are required for lag diagnostics")
        if not self.bootstrap_servers:
            return self._unavailable("not_configured", "Kafka bootstrap servers are not configured", topic=topic)
        try:
            from confluent_kafka import TopicPartition
            from confluent_kafka.admin import ConsumerGroupTopicPartitions, OffsetSpec

            admin = self._admin()
            metadata = admin.list_topics(timeout=self.timeout_seconds)
            target = metadata.topics.get(topic)
            if target is None or target.error:
                return self._unavailable("topic_not_found_or_not_authorized", "Topic metadata unavailable", topic=topic)
            numbers = sorted(target.partitions)
            if not numbers or len(numbers) > self.max_partitions:
                return self._unavailable("partition_limit", "Topic has no partitions or exceeds diagnostic limit", topic=topic)

            request = ConsumerGroupTopicPartitions(consumer_group, [TopicPartition(topic, n) for n in numbers])
            committed = admin.list_consumer_group_offsets([request], request_timeout=self.timeout_seconds)
            committed_rows = committed[consumer_group].result(timeout=self.timeout_seconds).topic_partitions
            committed_by_partition = {row.partition: row for row in committed_rows if row.topic == topic}
            latest = admin.list_offsets(
                {TopicPartition(topic, n): OffsetSpec.latest() for n in numbers},
                request_timeout=self.timeout_seconds,
            )
            latest_by_partition = {key.partition: future for key, future in latest.items() if key.topic == topic}
            rows = []
            unknown = []
            for number in numbers:
                row = committed_by_partition.get(number)
                if row is None or row.error or row.offset < 0 or number not in latest_by_partition:
                    unknown.append(number)
                    continue
                try:
                    end_offset = latest_by_partition[number].result(timeout=self.timeout_seconds).offset
                except Exception:  # noqa: BLE001
                    unknown.append(number)
                    continue
                if end_offset < 0 or end_offset < row.offset:
                    unknown.append(number)
                    continue
                rows.append({
                    "partition": number,
                    "committed_offset": row.offset,
                    "end_offset": end_offset,
                    "lag": max(0, end_offset - row.offset),
                })
            return {
                "available": not unknown,
                "partial": bool(unknown),
                "topic": topic,
                "consumer_group": consumer_group,
                "partition_count": len(numbers),
                "partitions": rows,
                "unknown_partitions": unknown,
                "total_lag": sum(row["lag"] for row in rows) if not unknown else None,
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "summary": "Kafka offset snapshot collected" if not unknown else "Kafka offset snapshot incomplete",
            }
        except ImportError:
            return self._unavailable("client_not_installed", "Kafka client dependency is unavailable", topic=topic)
        except Exception as exc:  # noqa: BLE001
            return self._failure(exc, "Kafka offset query failed")
