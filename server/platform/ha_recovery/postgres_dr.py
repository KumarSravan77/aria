from __future__ import annotations
from typing import Any


def streaming_replication_config(primary_host: str = "postgres-primary",
                                  replica_count: int = 1, namespace: str = "demo") -> dict[str, Any]:
    return {
        "strategy": "streaming-replication",
        "primary_host": primary_host, "replica_count": replica_count, "namespace": namespace,
        "recommended_settings": {"wal_level": "replica", "max_wal_senders": replica_count + 2,
                                  "synchronous_commit": "on"},
        "failover_steps": [
            "Confirm primary is unreachable via pg_isready",
            "Promote standby: SELECT pg_promote() or pg_ctl promote",
            "Update connection strings via ConfigMap or service DNS",
            "Verify application reconnects and WAL lag is zero",
            "Run smoke tests before marking recovery complete",
        ],
        "safety_boundary": "Failover is destructive. Requires ReBAC, approval, and audit logging.",
    }


def point_in_time_recovery(backup_location: str = "s3://aria-backups/postgres",
                            target_time: str = "") -> dict[str, Any]:
    return {
        "strategy": "point-in-time-recovery", "backup_location": backup_location,
        "target_time": target_time or "latest",
        "recovery_steps": [
            f"Restore base backup from {backup_location}",
            f"Apply WAL segments up to target time: {target_time or 'latest'}",
            "Verify data integrity with application smoke tests",
            "Promote to primary when validation passes",
        ],
        "safety_boundary": "PITR replaces existing data. Requires approval before execution.",
    }
