from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from server.db.models import OperationalMemoryEntry
from server.utils_time import utc_now

_SENSITIVITY = {"public", "internal", "confidential", "restricted"}


@dataclass
class OperationalMemory:
    """Stores remediation outcomes for future incident recommendations.

    If a database session is supplied, memory is persisted in PostgreSQL/SQLite.
    Without a database, it falls back to in-process storage for unit tests and local
    lightweight demos.
    """

    db: Session | None = None
    items: list[dict[str, Any]] = field(default_factory=list)

    def record(self, service: str, incident_id: str, outcome: str, remediation: str, metadata: dict[str, Any] | None = None, **governance: Any) -> dict[str, Any]:
        confidence = governance.get("confidence")
        if confidence is not None and not 0 <= int(confidence) <= 100:
            raise ValueError("confidence must be between 0 and 100")
        sensitivity = governance.get("sensitivity", "internal")
        if sensitivity not in _SENSITIVITY:
            raise ValueError(f"sensitivity must be one of {sorted(_SENSITIVITY)}")
        item = {
            "service": service,
            "incident_id": incident_id,
            "outcome": outcome,
            "remediation": remediation,
            "metadata": metadata or {},
            "team": governance.get("team", "unknown"),
            "environment": governance.get("environment", "unknown"),
            "incident_type": governance.get("incident_type", "unknown"),
            "root_cause": governance.get("root_cause"),
            "evidence_references": governance.get("evidence_references", []),
            "runbook_id": governance.get("runbook_id"),
            "runbook_version": governance.get("runbook_version"),
            "model_version": governance.get("model_version"),
            "prompt_version": governance.get("prompt_version"),
            "confidence": confidence,
            "verification_status": "candidate",
            "verified_by": None,
            "remediation_result": governance.get("remediation_result", {}),
            "recovery_metrics": governance.get("recovery_metrics", {}),
            "sensitivity": sensitivity,
            "retention_until": governance.get("retention_until"),
        }
        if self.db is None:
            self.items.append(item)
            return {"stored": True, "backend": "memory", "item": item}

        row = OperationalMemoryEntry(
            service=service,
            incident_id=incident_id,
            outcome=outcome,
            remediation=remediation,
            metadata_json=metadata or {},
            **{key: value for key, value in item.items() if key not in {"service", "incident_id", "outcome", "remediation", "metadata"}},
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"stored": True, "backend": "database", "item": self._row_to_item(row)}

    def recall(self, service: str, limit: int = 5, *, team: str | None = None, environment: str | None = None, verified_only: bool = False) -> dict[str, Any]:
        if self.db is None:
            matches = [i for i in self.items if i.get("service") == service]
            if team:
                matches = [i for i in matches if i.get("team") == team]
            if environment:
                matches = [i for i in matches if i.get("environment") == environment]
            if verified_only:
                matches = [i for i in matches if i.get("verification_status") == "verified"]
            matches = matches[-limit:]
            return {"service": service, "backend": "memory", "count": len(matches), "items": matches}

        query = self.db.query(OperationalMemoryEntry).filter(OperationalMemoryEntry.service == service)
        if team:
            query = query.filter(OperationalMemoryEntry.team == team)
        if environment:
            query = query.filter(OperationalMemoryEntry.environment == environment)
        if verified_only:
            query = query.filter(OperationalMemoryEntry.verification_status == "verified")
        now = utc_now()
        rows = (
            query
            .filter(OperationalMemoryEntry.superseded_by.is_(None))
            .filter((OperationalMemoryEntry.retention_until.is_(None)) | (OperationalMemoryEntry.retention_until > now))
            .order_by(OperationalMemoryEntry.created_at.desc(), OperationalMemoryEntry.id.desc())
            .limit(limit)
            .all()
        )
        items = [self._row_to_item(row) for row in rows]
        return {"service": service, "backend": "database", "count": len(items), "items": items}

    def verify(self, entry_id: int, verified_by: str) -> dict[str, Any]:
        if self.db is None:
            raise ValueError("Verification requires persistent storage")
        row = self.db.get(OperationalMemoryEntry, entry_id)
        if row is None:
            raise LookupError("Memory entry not found")
        if not row.evidence_references or not row.root_cause:
            raise ValueError("Verified knowledge requires root cause and evidence references")
        if row.verification_status == "verified":
            raise ValueError("Memory entry is already verified")
        if (row.metadata_json or {}).get("recorded_by") == verified_by:
            raise ValueError("Memory verification requires a different actor")
        row.verification_status = "verified"
        row.verified_by = verified_by
        row.verified_at = utc_now()
        self.db.commit()
        self.db.refresh(row)
        return {"verified": True, "item": self._row_to_item(row)}

    def _row_to_item(self, row: OperationalMemoryEntry) -> dict[str, Any]:
        return {
            "id": row.id,
            "service": row.service,
            "incident_id": row.incident_id,
            "outcome": row.outcome,
            "remediation": row.remediation,
            "team": row.team,
            "environment": row.environment,
            "incident_type": row.incident_type,
            "root_cause": row.root_cause,
            "evidence_references": row.evidence_references or [],
            "runbook_id": row.runbook_id,
            "runbook_version": row.runbook_version,
            "model_version": row.model_version,
            "prompt_version": row.prompt_version,
            "confidence": row.confidence,
            "verification_status": row.verification_status,
            "verified_by": row.verified_by,
            "verified_at": row.verified_at.isoformat() if row.verified_at else None,
            "remediation_result": row.remediation_result or {},
            "recovery_metrics": row.recovery_metrics or {},
            "sensitivity": row.sensitivity,
            "retention_until": row.retention_until.isoformat() if row.retention_until else None,
            "superseded_by": row.superseded_by,
            "metadata": row.metadata_json or {},
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
