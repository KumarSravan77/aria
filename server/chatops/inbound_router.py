from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    from server.chatops.command_parser import ChatOpsCommandParser
except Exception:
    ChatOpsCommandParser = None


@dataclass
class InboundChatOpsRouter:
    def route(self, text: str, user: str = "unknown") -> dict[str, Any]:
        if ChatOpsCommandParser:
            parsed = ChatOpsCommandParser().parse(text)
        else:
            parsed = {"intent": "unknown", "text": text}
        return {
            "user": user,
            "parsed": parsed,
            "action": "route_to_api",
            "implemented": False,
            "note": "Inbound Slack/Mattermost callback boundary; connect Slack Bolt or Mattermost Apps here.",
        }
