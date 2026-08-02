from __future__ import annotations
from server.collaboration.adapters import get_adapter

class NotificationRouter:
    def __init__(self, adapter=None):
        self.adapter = adapter or get_adapter()

    def post_message(self, channel_id: str, message: str, metadata: dict | None = None):
        return self.adapter.post_message(channel_id, message, metadata or {})
