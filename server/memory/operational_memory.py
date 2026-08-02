from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from server.db.models import OperationalMemoryEntry


@dataclass
class OperationalMemory:
    """Stores remediation outcomes for future incident recommendations.

    If a database session is supplied, memory is persisted in PostgreSQL/SQLite.
    Without a database, it falls back to in-process storage for unit tests and local
    lightweight demos.
    """

    db: Session | None = None
    items: list[dict[str, Any]] = field(default_factory=list)

    def record(self, service: str, incident_id: str, outcome: str, remediation: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        item = {
            "service": service,
            "incident_id": incident_id,
            "outcome": outcome,
            "remediation": remediation,
            "metadata": metadata or {},
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
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"stored": True, "backend": "database", "item": self._row_to_item(row)}

    def recall(self, service: str, limit: int = 5) -> dict[str, Any]:
        if self.db is None:
            matches = [i for i in self.items if i.get("service") == service][-limit:]
            return {"service": service, "backend": "memory", "count": len(matches), "items": matches}

        rows = (
            self.db.query(OperationalMemoryEntry)
            .filter(OperationalMemoryEntry.service == service)
            .order_by(OperationalMemoryEntry.created_at.desc(), OperationalMemoryEntry.id.desc())
            .limit(limit)
            .all()
        )
        items = [self._row_to_item(row) for row in rows]
        return {"service": service, "backend": "database", "count": len(items), "items": items}

    def _row_to_item(self, row: OperationalMemoryEntry) -> dict[str, Any]:
        return {
            "id": row.id,
            "service": row.service,
            "incident_id": row.incident_id,
            "outcome": row.outcome,
            "remediation": row.remediation,
            "metadata": row.metadata_json or {},
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
