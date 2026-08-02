from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class ServiceNowClient:
    """Fetches recent change records and calculates change-risk score.

    Returns `available: False` gracefully when ServiceNow is not configured,
    so investigations can proceed with a risk_score of 0.
    """

    base_url: str = ""
    token: str | None = None
    timeout_seconds: int = 15

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def get_recent_changes(self, service: str, window_hours: int = 24) -> dict[str, Any]:
        if not self.base_url or not self.token:
            return {
                "available": False,
                "error": "ServiceNow not configured (SERVICENOW_URL + SERVICENOW_TOKEN required)",
                "changes": [],
            }
        url = f"{self.base_url.rstrip('/')}/api/now/table/change_request"
        params = {
            "sysparm_query": f"cmdb_ci={service}^state=implement^opened_at>javascript:gs.hoursAgo({window_hours})",
            "sysparm_fields": "number,short_description,risk,state,opened_at,cmdb_ci",
            "sysparm_limit": 20,
        }
        try:
            r = requests.get(url, params=params, headers=self._headers(), timeout=self.timeout_seconds)
            r.raise_for_status()
            records = r.json().get("result", [])
            return {"available": True, "service": service, "window_hours": window_hours, "changes": records}
        except Exception as exc:
            return {"available": False, "service": service, "error": str(exc), "changes": []}

    def change_risk_score(self, changes: list[dict[str, Any]]) -> dict[str, Any]:
        if not changes:
            return {"risk_score": 0, "risk_level": "none", "high_risk_changes": [], "changes_count": 0}
        high = [c for c in changes if str(c.get("risk", "")).lower() in {"high", "critical"}]
        medium = [c for c in changes if str(c.get("risk", "")).lower() == "moderate"]
        score = min(100, len(high) * 30 + len(medium) * 10 + len(changes) * 2)
        level = "critical" if score >= 60 else "high" if score >= 30 else "low"
        return {
            "risk_score": score,
            "risk_level": level,
            "high_risk_changes": [c.get("number") for c in high],
            "changes_count": len(changes),
            "recommendation": (
                "Change window active — correlate deployment with incident start time."
                if score > 0 else "No recent high-risk changes detected."
            ),
        }
