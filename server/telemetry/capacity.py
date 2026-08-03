from __future__ import annotations


def capacity_plan(
    tb_per_day: float,
    peak_multiplier: float = 3.0,
    replication_factor: int = 3,
    kafka_retention_hours: int = 24,
    compression_ratio: float = 0.25,
    partition_target_mbps: float = 15.0,
    average_event_bytes: int = 1024,
    collector_target_mbps: float = 40.0,
    gateway_target_mbps: float = 100.0,
    hot_retention_days: int = 7,
    archive_retention_days: int = 365,
    object_store_replication_factor: int = 1,
) -> dict:
    """Transparent planning math; this is not a claim of benchmarked capacity."""
    positive = (
        tb_per_day,
        average_event_bytes,
        collector_target_mbps,
        gateway_target_mbps,
        hot_retention_days,
        archive_retention_days,
        object_store_replication_factor,
    )
    if any(value <= 0 for value in positive) or peak_multiplier < 1 or replication_factor < 1:
        raise ValueError("capacity inputs must be positive and peak_multiplier must be at least 1")
    average_mbps = tb_per_day * 1_000_000 / 86_400
    peak_mbps = average_mbps * peak_multiplier
    average_events_per_second = tb_per_day * 1_000_000_000_000 / 86_400 / average_event_bytes
    peak_events_per_second = average_events_per_second * peak_multiplier
    partitions = max(3, int(peak_mbps / partition_target_mbps) + 1)
    collector_replicas = max(2, int(peak_mbps / collector_target_mbps) + 1)
    gateway_replicas = max(3, int(peak_mbps / gateway_target_mbps) + 1)
    kafka_storage_tb = tb_per_day * (kafka_retention_hours / 24) * compression_ratio * replication_factor
    hot_storage_tb = tb_per_day * hot_retention_days * compression_ratio * object_store_replication_factor
    archive_storage_tb = tb_per_day * archive_retention_days * compression_ratio * object_store_replication_factor
    return {
        "input_tb_per_day": tb_per_day,
        "average_ingest_mbps": round(average_mbps, 2),
        "design_peak_mbps": round(peak_mbps, 2),
        "average_events_per_second": round(average_events_per_second),
        "design_peak_events_per_second": round(peak_events_per_second),
        "minimum_log_partitions": partitions,
        "minimum_collector_replicas": collector_replicas,
        "minimum_gateway_replicas": gateway_replicas,
        "estimated_kafka_storage_tb": round(kafka_storage_tb, 2),
        "estimated_hot_storage_tb": round(hot_storage_tb, 2),
        "estimated_archive_storage_tb": round(archive_storage_tb, 2),
        "assumptions": {
            "decimal_terabytes": True,
            "peak_multiplier": peak_multiplier,
            "replication_factor": replication_factor,
            "kafka_retention_hours": kafka_retention_hours,
            "compression_ratio": compression_ratio,
            "partition_target_mbps": partition_target_mbps,
            "average_event_bytes": average_event_bytes,
            "collector_target_mbps": collector_target_mbps,
            "gateway_target_mbps": gateway_target_mbps,
            "hot_retention_days": hot_retention_days,
            "archive_retention_days": archive_retention_days,
            "object_store_replication_factor": object_store_replication_factor,
        },
        "disclaimer": "Planning estimate only; validate with representative load and failure tests.",
    }
