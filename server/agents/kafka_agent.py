from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from server.platform.streaming.kafka.client import KafkaDiagnosticClient
from server.platform.streaming.kafka.analyzers import (
    KafkaLagAnalyzer,
    KafkaPartitionSkewAnalyzer,
    KafkaRebalanceAnalyzer,
)


@dataclass
class KafkaAgent:
    """Streaming platform investigation agent for Kafka incidents.

    Evidence only. No topic, ACL, broker, or consumer-group mutations.
    """

    client: KafkaDiagnosticClient = field(default_factory=KafkaDiagnosticClient)
    lag_analyzer: KafkaLagAnalyzer = field(default_factory=KafkaLagAnalyzer)
    rebalance_analyzer: KafkaRebalanceAnalyzer = field(default_factory=KafkaRebalanceAnalyzer)
    skew_analyzer: KafkaPartitionSkewAnalyzer = field(default_factory=KafkaPartitionSkewAnalyzer)

    def run(self, incident: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        service = incident.get("service") or incident.get("target") or context.get("service") or "unknown"
        signals = [str(x) for x in incident.get("signals", [])]
        topic = incident.get("topic") or context.get("topic")
        consumer_group = incident.get("consumer_group") or context.get("consumer_group")

        cluster = self.client.cluster_health()
        lag = self.client.consumer_group_lag(consumer_group=consumer_group, topic=topic)
        topic_health = self.client.topic_health(topic=topic)

        lag_analysis = self.lag_analyzer.analyze(signals, metrics=lag)
        rebalance_analysis = self.rebalance_analyzer.analyze(signals, deployment_context=context.get("deployment"))
        skew_analysis = self.skew_analyzer.analyze(signals, topic=topic)

        hypotheses = []
        for item in (lag_analysis, rebalance_analysis, skew_analysis):
            hypotheses.extend(item.get("hypotheses", []))

        return {
            "agent": "kafka",
            "type": "streaming_platform_evidence",
            "service": service,
            "topic": topic,
            "consumer_group": consumer_group,
            "cluster": cluster,
            "consumer_lag": lag,
            "topic_health": topic_health,
            "analysis": {
                "lag": lag_analysis,
                "rebalance": rebalance_analysis,
                "partition_skew": skew_analysis,
            },
            "hypotheses": hypotheses,
            "summary": "Kafka streaming diagnostics completed",
            "available": cluster.get("available", False),
            "safety_boundary": "read-only Kafka diagnostics; no streaming platform mutation",
        }
