from __future__ import annotations

from hashlib import sha1
from server.utils_time import utc_now


def normalize_pagerduty_payload(payload: dict) -> dict:
    event = payload.get("event") or payload
    data = event.get("data") or event
    incident = data.get("incident") or data
    service_obj = incident.get("service") or {}
    service = service_obj.get("summary") or service_obj.get("name") or incident.get("service_name") or "unknown-service"
    title = incident.get("title") or data.get("title") or "PagerDuty incident"
    urgency = str(incident.get("urgency") or data.get("urgency") or "high").lower()
    external_id = str(incident.get("id") or data.get("id") or sha1(f"{service}:{title}".encode()).hexdigest()[:12])
    status = str(incident.get("status") or data.get("status") or "triggered").lower()
    return {
        "incident_id": f"PD-{external_id}"[:80], "source": "pagerduty", "alert_name": title,
        "service": service, "environment": incident.get("environment", "prod"),
        "severity": "P1" if urgency == "high" else "P2", "status": status,
        "starts_at": incident.get("created_at") or utc_now().isoformat(), "summary": title,
        "description": incident.get("description", ""), "labels": {"pagerduty_id": external_id},
        "annotations": {}, "dedupe_key": f"pagerduty:{external_id}", "symptoms": [title.lower()],
        "signals": {}, "user": {"role": "sre", "team": "platform"},
    }
