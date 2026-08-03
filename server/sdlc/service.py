from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from sqlalchemy.orm import Session
from server.db.models import SDLCEvent, ExternalIdentity, AuditLog
from server.utils_time import utc_now


class SDLCMemoryService:
    ALLOWED_TYPES = {"code_change", "pull_request", "deployment", "alert_change", "runbook_change", "engineer_decision", "incident_outcome"}

    def __init__(self, db: Session): self.db = db

    def record(self, payload: dict, actor: str) -> dict:
        event_type = payload.get("event_type", "")
        if event_type not in self.ALLOWED_TYPES:
            raise ValueError(f"Unsupported event_type: {event_type}")
        service = payload.get("service")
        if not service:
            raise ValueError("service is required")
        raw_id = payload.get("event_id") or f"{event_type}:{service}:{payload.get('revision')}:{payload.get('occurred_at')}"
        event_id = sha256(raw_id.encode()).hexdigest()[:32]
        existing = self.db.query(SDLCEvent).filter_by(event_id=event_id).one_or_none()
        if existing: return self._serialize(existing)
        occurred = payload.get("occurred_at")
        occurred_at = datetime.fromisoformat(occurred.replace("Z", "+00:00")).replace(tzinfo=None) if occurred else utc_now()
        row = SDLCEvent(event_id=event_id, event_type=event_type, service=service, environment=payload.get("environment", "unknown"), actor=actor, revision=payload.get("revision"), occurred_at=occurred_at, payload=payload.get("metadata") or {})
        self.db.add(row)
        self.db.add(AuditLog(actor=actor, action="sdlc.event_recorded", resource_type="service", resource_id=service, metadata_json={"event_id": event_id, "event_type": event_type}))
        self.db.commit(); self.db.refresh(row)
        return self._serialize(row)

    def context(self, service: str, window_hours: int = 168) -> dict:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=min(max(window_hours, 1), 720))).replace(tzinfo=None)
        rows = self.db.query(SDLCEvent).filter(SDLCEvent.service == service, SDLCEvent.occurred_at >= cutoff).order_by(SDLCEvent.occurred_at.desc()).limit(200).all()
        events = [self._serialize(row) for row in rows]
        return {"service": service, "window_hours": window_hours, "count": len(events), "events": events, "correlations": self._correlate(events)}

    def link_identity(self, aria_user_id: str, provider: str, external_user_id: str, team: str, actor: str) -> dict:
        provider = provider.lower()
        if provider not in {"slack", "teams", "github", "pagerduty", "mcp"}: raise ValueError("Unsupported identity provider")
        row = self.db.query(ExternalIdentity).filter_by(provider=provider, external_user_id=external_user_id).one_or_none()
        if row is None:
            row = ExternalIdentity(aria_user_id=aria_user_id, provider=provider, external_user_id=external_user_id, team=team, verified=True); self.db.add(row)
        else:
            row.aria_user_id, row.team, row.verified = aria_user_id, team, True
        self.db.add(AuditLog(actor=actor, action="identity.linked", resource_type="user", resource_id=aria_user_id, metadata_json={"provider": provider, "external_user_id": external_user_id}))
        self.db.commit(); self.db.refresh(row)
        return {"aria_user_id": row.aria_user_id, "provider": row.provider, "external_user_id": row.external_user_id, "team": row.team, "verified": row.verified}

    @staticmethod
    def _serialize(row: SDLCEvent) -> dict:
        return {"event_id": row.event_id, "event_type": row.event_type, "service": row.service, "environment": row.environment, "actor": row.actor, "revision": row.revision, "occurred_at": row.occurred_at.isoformat(), "metadata": row.payload}

    @staticmethod
    def _correlate(events: list[dict]) -> list[dict]:
        deployments = [e for e in events if e["event_type"] == "deployment"]
        alerts = [e for e in events if e["event_type"] in {"alert_change", "incident_outcome"}]
        results = []
        for dep in deployments:
            dep_time = datetime.fromisoformat(dep["occurred_at"])
            related = [a for a in alerts if 0 <= (datetime.fromisoformat(a["occurred_at"]) - dep_time).total_seconds() <= 86400]
            if related: results.append({"deployment_event_id": dep["event_id"], "revision": dep["revision"], "subsequent_events": [a["event_id"] for a in related], "inference": "temporal correlation only; requires evidence review"})
        return results
