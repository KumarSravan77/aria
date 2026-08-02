from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class KafkaLagAnalyzer:
    def analyze(self, signals: list[str], metrics: dict[str, Any] | None = None) -> dict[str, Any]:
        text = " ".join(signals).lower() + " " + str(metrics or {}).lower()
        hypotheses = []
        if "lag" in text:
            hypotheses.append("consumer_lag_growth")
        if "backpressure" in text:
            hypotheses.append("downstream_backpressure")
        if "database" in text or "db" in text:
            hypotheses.append("consumer_blocked_by_database_dependency")
        return {
            "analyzer": "kafka_lag",
            "hypotheses": hypotheses or ["insufficient_lag_evidence"],
            "recommended_evidence": [
                "consumer group lag by topic/partition",
                "consumer processing rate",
                "producer input rate",
                "consumer pod restarts",
                "downstream dependency latency",
            ],
        }


@dataclass
class KafkaRebalanceAnalyzer:
    def analyze(self, signals: list[str], deployment_context: dict[str, Any] | None = None) -> dict[str, Any]:
        text = " ".join(signals).lower() + " " + str(deployment_context or {}).lower()
        hypotheses = []
        if "rebalance" in text:
            hypotheses.append("consumer_group_rebalance_storm")
        if "deployment" in text or "rollout" in text:
            hypotheses.append("deployment_triggered_consumer_rebalance")
        if "restart" in text:
            hypotheses.append("consumer_restart_instability")
        return {
            "analyzer": "kafka_rebalance",
            "hypotheses": hypotheses or ["no_rebalance_signal"],
            "recommended_evidence": [
                "consumer group rebalance count",
                "consumer restart count",
                "deployment revision",
                "pod readiness history",
            ],
        }


@dataclass
class KafkaPartitionSkewAnalyzer:
    def analyze(self, signals: list[str], topic: str | None = None) -> dict[str, Any]:
        text = " ".join(signals).lower()
        hypotheses = []
        if "skew" in text or "hot partition" in text:
            hypotheses.append("partition_skew_or_hot_key")
        return {
            "analyzer": "kafka_partition_skew",
            "topic": topic,
            "hypotheses": hypotheses or ["partition_skew_not_confirmed"],
            "recommended_evidence": [
                "records per partition",
                "bytes in/out by partition",
                "consumer lag by partition",
                "message key distribution",
            ],
        }
