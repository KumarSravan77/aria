from __future__ import annotations

class InteractiveApprovalBuilder:
    """Builds Slack/Mattermost-style approval cards without calling external APIs."""
    def build(self, approval_id: int, incident_id: str, action: dict, requester: str) -> dict:
        return {
            "type": "approval_card",
            "approval_id": approval_id,
            "incident_id": incident_id,
            "requester": requester,
            "text": f"Approval requested for {action.get('action')} on {action.get('target')}",
            "actions": [
                {"label": "Approve", "command": f"/aria approve {approval_id}"},
                {"label": "Reject", "command": f"/aria reject {approval_id}"},
            ],
            "safety": "Approval commands still call the authenticated approval API; chat cards do not bypass ReBAC or 4-eyes controls.",
        }
