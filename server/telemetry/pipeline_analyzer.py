from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class MetricsClient(Protocol):
    def query(self, promql: str) -> dict[str, Any]: ...


@dataclass
class PipelineAnalyzer:
    """Collect deterministic evidence about the telemetry data plane."""

    metrics: MetricsClient

    QUERIES = {
        "collector_refused_logs": "sum(rate(otelcol_receiver_refused_log_records[5m]))",
        "collector_export_failures": "sum(rate(otelcol_exporter_send_failed_log_records[5m]))",
        "collector_queue_utilization": "max(otelcol_exporter_queue_size / clamp_min(otelcol_exporter_queue_capacity, 1))",
        "kafka_consumer_lag": "max(kafka_consumergroup_lag{group=~\"aria-.*\"})",
        "loki_rejected_bytes": "sum(rate(loki_discarded_bytes_total[5m]))",
        "cardinality_growth": "sum(scrape_series_added{job=~\"otel.*|loki.*\"})",
    }

    def snapshot(self) -> dict[str, Any]:
        signals = {name: self.metrics.query(query) for name, query in self.QUERIES.items()}
        available = sum(bool(signal.get("available")) for signal in signals.values())
        return {
            "available": available > 0,
            "signals_available": available,
            "signals_total": len(signals),
            "signals": signals,
        }

    @staticmethod
    def recommend(snapshot: dict[str, Any]) -> list[str]:
        if not snapshot.get("available"):
            return ["Restore Prometheus connectivity before changing telemetry capacity."]
        return [
            "Inspect collector refusal and queue trends before scaling gateways.",
            "Compare Kafka lag with Loki rejection rates to locate the bottleneck.",
            "Identify the highest-volume tenant before changing global limits.",
        ]
