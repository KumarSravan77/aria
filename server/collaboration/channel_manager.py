from datetime import datetime, timezone
import re
from server.collaboration.adapters import get_adapter

class ChannelManager:
    def __init__(self, adapter=None):
        self.adapter = adapter or get_adapter()

    def create_incident_channel(self, incident_id: str, service: str, severity: str):
        date = datetime.now(timezone.utc).strftime("%Y%m%d")
        service_slug = re.sub(r"[^a-z0-9-]+", "-", service.lower().replace("_", "-")).strip("-")
        incident_suffix = re.sub(r"[^a-z0-9-]+", "-", incident_id.lower()).strip("-")
        name = f"inc-{severity.lower()}-{service_slug}-{incident_suffix}-{date}"
        purpose = f"War room for {incident_id} affecting {service}. AI teammate posts investigation evidence here."
        channel = self.adapter.create_channel(name, purpose)
        channel["incident_id"] = incident_id
        return channel
