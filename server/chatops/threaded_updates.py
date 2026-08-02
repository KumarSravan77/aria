from __future__ import annotations

class ThreadedUpdateBuilder:
    """Formats incident updates for threaded ChatOps messages."""
    def evidence_update(self, incident_id: str, evidence: list[dict], recommendation: str | None = None) -> dict:
        bullets = [f"• {item.get('source', 'evidence')}: {item.get('summary', item.get('message', 'collected'))}" for item in evidence]
        return {
            "incident_id": incident_id,
            "thread_key": incident_id,
            "text": "\n".join([f"ARIA evidence update for {incident_id}", *bullets, f"Recommendation: {recommendation or 'continue investigation'}"]),
            "message_type": "threaded_evidence_update",
        }
