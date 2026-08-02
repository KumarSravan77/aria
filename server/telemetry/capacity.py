from __future__ import annotations


def capacity_plan(
    tb_per_day: float,
    peak_multiplier: float = 3.0,
    replication_factor: int = 3,
    kafka_retention_hours: int = 24,
    compression_ratio: float = 0.25,
    partition_target_mbps: float = 15.0,
) -> dict:
    """Transparent planning math; this is not a claim of benchmarked capacity."""
    if tb_per_day <= 0 or peak_multiplier < 1 or replication_factor < 1:
        raise ValueError("capacity inputs must be positive and peak_multiplier must be at least 1")
    average_mbps = tb_per_day * 1_000_000 / 86_400
    peak_mbps = average_mbps * peak_multiplier
    partitions = max(3, int(peak_mbps / partition_target_mbps) + 1)
    kafka_storage_tb = tb_per_day * (kafka_retention_hours / 24) * compression_ratio * replication_factor
    return {
        "input_tb_per_day": tb_per_day,
        "average_ingest_mbps": round(average_mbps, 2),
        "design_peak_mbps": round(peak_mbps, 2),
        "minimum_log_partitions": partitions,
        "estimated_kafka_storage_tb": round(kafka_storage_tb, 2),
        "assumptions": {
            "decimal_terabytes": True,
            "peak_multiplier": peak_multiplier,
            "replication_factor": replication_factor,
            "kafka_retention_hours": kafka_retention_hours,
            "compression_ratio": compression_ratio,
            "partition_target_mbps": partition_target_mbps,
        },
        "disclaimer": "Planning estimate only; validate with representative load and failure tests.",
    }
