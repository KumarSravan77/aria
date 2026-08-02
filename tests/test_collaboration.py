from server.collaboration.channel_manager import ChannelManager
from server.collaboration.incident_timeline import IncidentTimeline
from server.collaboration.ai_teammate import AITeammate


def test_channel_name_is_incident_friendly():
    cm = ChannelManager()
    channel = cm.create_incident_channel("INC-1", "Checkout API", "P1")
    assert channel["channel_name"].startswith("inc-p1-checkout-api")
    assert channel["provider"] == "stdout"


def test_timeline_records_events():
    timeline = IncidentTimeline()
    timeline.add("INC-1", "created", "incident created")
    events = timeline.list("INC-1")
    assert len(events) == 1
    assert events[0]["event_type"] == "created"


def test_ai_teammate_opening_update_contains_service():
    teammate = AITeammate()
    msg = teammate.opening_update(
        {"incident_id": "INC-1", "service": "checkout-api", "severity": "P1", "environment": "dev", "symptoms": [], "signals": {}},
        {"channel_name": "inc-p1-checkout-api", "channel_id": "local-inc"},
    )
    assert "checkout-api" in msg
    assert "starting investigation" in msg.lower()
