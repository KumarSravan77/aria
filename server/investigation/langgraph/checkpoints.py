from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import time, uuid
from sqlalchemy.orm import Session
from server.db.models import InvestigationCheckpoint

@dataclass
class InMemoryCheckpointStore:
    db: Session | None = None
    checkpoints: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def save(self, investigation_id: str, node: str, state: dict[str, Any]) -> dict[str, Any]:
        checkpoint = {
            "checkpoint_id": str(uuid.uuid4()),
            "investigation_id": investigation_id,
            "node": node,
            "timestamp": time.time(),
            "mode": state.get("mode"),
            "evidence_count": len(state.get("evidence", [])),
            "hypothesis_count": len(state.get("hypotheses", [])),
        }
        if self.db is not None:
            row = InvestigationCheckpoint(
                checkpoint_id=checkpoint["checkpoint_id"],
                investigation_id=investigation_id,
                incident_id=str(state.get("incident_id", "unknown")),
                service=str(state.get("service", "unknown")),
                team=str(state.get("team", "unknown")),
                environment=str(state.get("environment", "unknown")),
                node=node,
                mode=state.get("mode"),
                state_json={
                    "routing": state.get("routing", []),
                    "evidence_count": checkpoint["evidence_count"],
                    "hypothesis_count": checkpoint["hypothesis_count"],
                    "recommendation_count": len(state.get("recommendations", [])),
                    "error_count": len(state.get("errors", [])),
                },
                sensitivity=str(state.get("sensitivity", "internal")),
            )
            self.db.add(row)
            self.db.commit()
            checkpoint["backend"] = "database"
        else:
            checkpoint["backend"] = "memory"
        self.checkpoints.setdefault(investigation_id, []).append(checkpoint)
        return checkpoint

    def list(self, investigation_id: str) -> list[dict[str, Any]]:
        if self.db is not None:
            rows = self.db.query(InvestigationCheckpoint).filter(InvestigationCheckpoint.investigation_id == investigation_id).order_by(InvestigationCheckpoint.id).all()
            return [{"checkpoint_id": row.checkpoint_id, "investigation_id": row.investigation_id, "node": row.node, "mode": row.mode, "backend": "database", "state": row.state_json} for row in rows]
        return self.checkpoints.get(investigation_id, [])
