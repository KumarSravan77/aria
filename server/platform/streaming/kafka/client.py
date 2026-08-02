from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import os


@dataclass
class KafkaDiagnosticClient:
    """Read-only Kafka diagnostic boundary.

    This client intentionally degrades gracefully when Kafka admin libraries or
    broker access are unavailable. It never mutates topics, ACLs, brokers, or consumer groups.
    """

    bootstrap_servers: str | None = None
    timeout_seconds: float = 5.0

    def __post_init__(self) -> None:
        self.bootstrap_servers = self.bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS")

    def cluster_health(self) -> dict[str, Any]:
        if not self.bootstrap_servers:
            return {
                "available": False,
                "reason": "KAFKA_BOOTSTRAP_SERVERS_not_configured",
                "summary": "Kafka diagnostics unavailable until bootstrap servers are configured",
            }

        try:
            from kafka import KafkaAdminClient
            admin = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers.split(","),
                request_timeout_ms=int(self.timeout_seconds * 1000),
            )
            topics = admin.list_topics()
            admin.close()
            return {
                "available": True,
                "bootstrap_servers": self.bootstrap_servers,
                "topic_count": len(topics),
                "topics_sample": sorted(topics)[:25],
                "summary": "Kafka cluster reachable",
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "available": False,
                "bootstrap_servers": self.bootstrap_servers,
                "error": str(exc),
                "summary": "Kafka cluster health check failed",
            }

    def consumer_group_lag(self, consumer_group: str | None = None, topic: str | None = None) -> dict[str, Any]:
        return {
            "available": False,
            "implemented": "metrics_boundary",
            "consumer_group": consumer_group,
            "topic": topic,
            "summary": "Consumer lag should be read from Prometheus/JMX exporter or Kafka admin offset APIs",
            "recommended_promql": (
                f'kafka_consumergroup_lag{{consumergroup="{consumer_group}"}}'
                if consumer_group else "kafka_consumergroup_lag"
            ),
        }

    def topic_health(self, topic: str | None = None) -> dict[str, Any]:
        return {
            "available": False,
            "implemented": "metadata_boundary",
            "topic": topic,
            "checks": [
                "partition count",
                "under replicated partitions",
                "offline partitions",
                "leader imbalance",
                "ISR shrink",
                "message throughput",
            ],
            "summary": "Topic health should be read from Kafka admin metadata and Prometheus broker metrics",
        }
