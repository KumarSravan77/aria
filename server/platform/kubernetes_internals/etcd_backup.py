from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import time, json

@dataclass
class EtcdBackupInspector:
    """Inspects etcd backup metadata. Never restores production etcd."""
    metadata_path: Path = Path("backups/etcd/metadata.json")
    max_age_hours: int = 24

    def inspect_backups(self) -> dict[str, Any]:
        if not self.metadata_path.exists():
            return {
                "available": False,
                "status": "missing",
                "backup_fresh": False,
                "reason": "backup_metadata_not_found",
                "expected_metadata_path": str(self.metadata_path),
                "safety_boundary": "ARIA never restores production etcd automatically",
            }
        metadata = json.loads(self.metadata_path.read_text())
        created_at = float(metadata.get("created_at", 0))
        age_hours = round((time.time() - created_at) / 3600, 2) if created_at else None
        fresh = age_hours is not None and age_hours <= self.max_age_hours
        encrypted = bool(metadata.get("encrypted", False))
        size_bytes = int(metadata.get("size_bytes", 0))
        return {
            "available": True,
            "status": "ok" if fresh and encrypted and size_bytes > 0 else "review",
            "backup_fresh": fresh,
            "age_hours": age_hours,
            "encrypted": encrypted,
            "size_bytes": size_bytes,
            "location": metadata.get("location"),
            "restore_validated_at": metadata.get("restore_validated_at"),
            "safety_boundary": "Production restore is manual-only and approval-gated",
        }

    def recovery_plan(self) -> dict[str, Any]:
        return {
            "plan": "etcd_recovery_advisory",
            "manual_only": True,
            "approval_required": True,
            "steps": [
                "Verify latest backup metadata, freshness, size and encryption",
                "Validate snapshot integrity in sandbox",
                "Restore snapshot into non-prod control plane",
                "Run API server and workload smoke tests",
                "Require platform commander approval for production restore",
                "Execute production restore manually using platform runbook",
                "Audit restore and validate cluster health",
            ],
        }
