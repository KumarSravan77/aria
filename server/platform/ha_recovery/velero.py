from __future__ import annotations
from typing import Any


def backup_schedule(namespace: str = "demo", schedule: str = "0 2 * * *", ttl: str = "720h0m0s") -> dict[str, Any]:
    return {
        "apiVersion": "velero.io/v1", "kind": "Schedule",
        "metadata": {"name": f"aria-{namespace}-backup", "namespace": "velero",
                     "labels": {"app.kubernetes.io/managed-by": "aria"}},
        "spec": {"schedule": schedule, "template": {
            "includedNamespaces": [namespace], "ttl": ttl,
            "storageLocation": "default", "snapshotVolumes": True}},
    }


def restore_plan(namespace: str = "demo", backup_name: str = "") -> dict[str, Any]:
    if not backup_name:
        return {"available": False, "error": "backup_name is required for restore"}
    return {
        "apiVersion": "velero.io/v1", "kind": "Restore",
        "metadata": {"name": f"aria-restore-{namespace}", "namespace": "velero"},
        "spec": {"backupName": backup_name, "includedNamespaces": [namespace], "restorePVs": True},
        "safety_boundary": "Apply only after verifying backup integrity. Restore is destructive. Requires approval.",
    }
