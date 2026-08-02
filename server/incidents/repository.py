from __future__ import annotations
from datetime import datetime
from server.utils_time import utc_now
from sqlalchemy.orm import Session
from server.db.models import Incident, IncidentTimelineEvent, AuditLog, RCADraft
from server.incidents.state_machine import require_transition

class IncidentRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert_incident(self, incident_id: str, payload: dict, channel: dict | None = None) -> Incident:
        item = self.db.get(Incident, incident_id)
        if item is None:
            item = Incident(
                id=incident_id,
                alert_name=payload.get("alert_name"),
                service=payload.get("service", "unknown"),
                environment=payload.get("environment", "unknown"),
                severity=payload.get("severity", "unknown"),
                source=payload.get("source", "unknown"),
                dedupe_key=payload.get("dedupe_key"),
                payload=payload,
            )
            self.db.add(item)
        else:
            item.payload = payload
            item.updated_at = utc_now()
        if channel:
            item.channel_id = channel.get("channel_id")
            item.channel_name = channel.get("channel_name")
        self.db.commit(); self.db.refresh(item)
        return item

    def add_timeline(self, incident_id: str, event_type: str, message: str, metadata: dict | None = None):
        if self.db.get(Incident, incident_id) is None:
            raise KeyError(f"Incident not found: {incident_id}")
        event = IncidentTimelineEvent(incident_id=incident_id, event_type=event_type, message=message, metadata_json=metadata or {})
        self.db.add(event)
        self.db.commit(); self.db.refresh(event)
        return event

    def list_timeline(self, incident_id: str) -> list[dict]:
        rows = self.db.query(IncidentTimelineEvent).filter_by(incident_id=incident_id).order_by(IncidentTimelineEvent.created_at.asc()).all()
        return [{"id": r.id, "timestamp": r.created_at.isoformat(), "event_type": r.event_type, "message": r.message, "metadata": r.metadata_json} for r in rows]

    def transition(self, incident_id: str, target_status: str, actor: str = "system") -> Incident:
        item = self.db.get(Incident, incident_id)
        if item is None:
            raise KeyError(f"Incident not found: {incident_id}")
        require_transition(item.status, target_status)
        previous = item.status
        item.status = target_status
        item.updated_at = utc_now()
        self.db.add(AuditLog(actor=actor, action="incident.transition", resource_type="incident", resource_id=incident_id, metadata_json={"from": previous, "to": target_status}))
        self.db.commit(); self.db.refresh(item)
        return item

    def save_rca(self, incident_id: str, markdown: str):
        row = RCADraft(incident_id=incident_id, markdown=markdown)
        self.db.add(row); self.db.commit(); self.db.refresh(row)
        return row

    def get(self, incident_id: str) -> Incident | None:
        return self.db.get(Incident, incident_id)
