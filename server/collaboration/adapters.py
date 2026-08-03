from __future__ import annotations
import os, requests
from abc import ABC, abstractmethod

class CollaborationAdapter(ABC):
    @abstractmethod
    def create_channel(self, name: str, purpose: str = "") -> dict: ...
    @abstractmethod
    def post_message(self, channel_id: str, message: str, metadata: dict | None = None) -> dict: ...

class StdoutAdapter(CollaborationAdapter):
    def create_channel(self, name: str, purpose: str = "") -> dict:
        return {"provider": "stdout", "channel_id": name, "channel_name": name, "purpose": purpose}
    def post_message(self, channel_id: str, message: str, metadata: dict | None = None) -> dict:
        print(f"[war-room:{channel_id}] {message}")
        return {"provider": "stdout", "channel_id": channel_id, "posted": True}

class SlackAdapter(CollaborationAdapter):
    def __init__(self, token: str | None = None):
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        if not self.token:
            raise ValueError("SLACK_BOT_TOKEN is required for SlackAdapter")
    def _post(self, method: str, payload: dict):
        r = requests.post(f"https://slack.com/api/{method}", json=payload, headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}, timeout=20)
        r.raise_for_status()
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack API error: {data}")
        return data
    def create_channel(self, name: str, purpose: str = "") -> dict:
        safe = name.lower().replace("_", "-")[:75]
        data = self._post("conversations.create", {"name": safe, "is_private": False})
        channel_id = data["channel"]["id"]
        if purpose:
            self._post("conversations.setPurpose", {"channel": channel_id, "purpose": purpose[:250]})
        return {"provider": "slack", "channel_id": channel_id, "channel_name": safe}
    def post_message(self, channel_id: str, message: str, metadata: dict | None = None) -> dict:
        payload = {"channel": channel_id, "text": message}
        if metadata and metadata.get("blocks"):
            payload["blocks"] = metadata["blocks"]
        if metadata and metadata.get("thread_ts"):
            payload["thread_ts"] = metadata["thread_ts"]
        data = self._post("chat.postMessage", payload)
        return {"provider": "slack", "channel_id": channel_id, "posted": True, "ts": data.get("ts")}

class TeamsAdapter(CollaborationAdapter):
    """Posts incident cards through a Teams Workflow incoming-webhook URL.

    Teams webhooks cannot create channels, so incidents use the configured channel
    and keep their incident id as the conversation correlation key.
    """
    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = webhook_url or os.getenv("TEAMS_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("TEAMS_WEBHOOK_URL is required for TeamsAdapter")
    def create_channel(self, name: str, purpose: str = "") -> dict:
        return {"provider": "teams", "channel_id": "configured-workflow", "channel_name": name, "purpose": purpose}
    def post_message(self, channel_id: str, message: str, metadata: dict | None = None) -> dict:
        body = {"type": "message", "attachments": [{"contentType": "application/vnd.microsoft.card.adaptive", "contentUrl": None, "content": {"$schema": "http://adaptivecards.io/schemas/adaptive-card.json", "type": "AdaptiveCard", "version": "1.4", "body": [{"type": "TextBlock", "text": message, "wrap": True}]}}]}
        r = requests.post(self.webhook_url, json=body, timeout=20)
        r.raise_for_status()
        return {"provider": "teams", "channel_id": channel_id, "posted": True}

class MattermostAdapter(CollaborationAdapter):
    def __init__(self, base_url: str | None = None, token: str | None = None, team_id: str | None = None):
        self.base_url = (base_url or os.getenv("MATTERMOST_URL") or "").rstrip("/")
        self.token = token or os.getenv("MATTERMOST_TOKEN")
        self.team_id = team_id or os.getenv("MATTERMOST_TEAM_ID")
        if not all([self.base_url, self.token, self.team_id]):
            raise ValueError("MATTERMOST_URL, MATTERMOST_TOKEN, and MATTERMOST_TEAM_ID are required")
    def _headers(self):
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    def create_channel(self, name: str, purpose: str = "") -> dict:
        safe = name.lower().replace("_", "-")[:60]
        payload = {"team_id": self.team_id, "name": safe, "display_name": safe, "type": "O", "purpose": purpose[:250]}
        r = requests.post(f"{self.base_url}/api/v4/channels", json=payload, headers=self._headers(), timeout=20)
        if r.status_code == 409:
            # channel already exists; fetch by name
            r = requests.get(f"{self.base_url}/api/v4/teams/{self.team_id}/channels/name/{safe}", headers=self._headers(), timeout=20)
        r.raise_for_status()
        data = r.json()
        return {"provider": "mattermost", "channel_id": data["id"], "channel_name": safe}
    def post_message(self, channel_id: str, message: str, metadata: dict | None = None) -> dict:
        r = requests.post(f"{self.base_url}/api/v4/posts", json={"channel_id": channel_id, "message": message}, headers=self._headers(), timeout=20)
        r.raise_for_status()
        data = r.json()
        return {"provider": "mattermost", "channel_id": channel_id, "posted": True, "post_id": data.get("id")}

def get_adapter(provider: str | None = None) -> CollaborationAdapter:
    provider = (provider or os.getenv("COLLABORATION_PROVIDER") or "stdout").lower()
    if provider == "slack": return SlackAdapter()
    if provider == "teams": return TeamsAdapter()
    if provider == "mattermost": return MattermostAdapter()
    return StdoutAdapter()
