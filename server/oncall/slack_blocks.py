from __future__ import annotations


def incident_message(incident: dict, analysis: dict | None = None) -> dict:
    analysis = analysis or {}
    incident_id = incident.get("incident_id", "unknown")
    service = incident.get("service", "unknown")
    severity = incident.get("severity", "P2")
    summary = incident.get("summary") or incident.get("alert_name") or "Incident detected"
    cause = analysis.get("probable_cause") or "Investigation in progress"
    confidence = analysis.get("confidence", "pending")
    fallback = f"{severity} {incident_id}: {service} — {summary}"
    return {"text": fallback, "blocks": [
        {"type": "header", "text": {"type": "plain_text", "text": f"{severity} · {service}", "emoji": True}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*Incident*\n`{incident_id}`"},
            {"type": "mrkdwn", "text": f"*Environment*\n{incident.get('environment', 'unknown')}"},
            {"type": "mrkdwn", "text": f"*Summary*\n{summary}"},
            {"type": "mrkdwn", "text": f"*Confidence*\n{confidence}"},
        ]},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Current assessment*\n{cause}"}},
        {"type": "actions", "block_id": f"incident_actions_{incident_id}"[:255], "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "Show evidence"}, "action_id": "aria_show_evidence", "value": incident_id},
            {"type": "button", "text": {"type": "plain_text", "text": "Open incident"}, "action_id": "aria_open_incident", "url": incident.get("incident_url", "http://localhost:8000/docs")},
        ]},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": "ARIA recommends; policy and human approval govern production changes."}]},
    ]}


def approval_message(approval_id: int, incident_id: str, action: dict) -> dict:
    fallback = f"Approval {approval_id} requested for {action.get('action')} on {action.get('target')}"
    return {"text": fallback, "blocks": [
        {"type": "header", "text": {"type": "plain_text", "text": "Production action approval"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Incident:* `{incident_id}`\n*Action:* `{action.get('action')}`\n*Target:* `{action.get('target')}`"}},
        {"type": "actions", "block_id": f"approval_{approval_id}", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "Approve"}, "style": "primary", "action_id": "aria_approve_action", "value": str(approval_id), "confirm": {"title": {"type": "plain_text", "text": "Approve action?"}, "text": {"type": "mrkdwn", "text": "ARIA will queue deterministic execution and verify recovery."}, "confirm": {"type": "plain_text", "text": "Approve"}, "deny": {"type": "plain_text", "text": "Cancel"}}},
            {"type": "button", "text": {"type": "plain_text", "text": "Reject"}, "style": "danger", "action_id": "aria_reject_action", "value": str(approval_id)},
        ]},
    ]}
