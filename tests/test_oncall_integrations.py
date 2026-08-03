import json
from datetime import datetime, timedelta
from server.db.session import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.intake.pagerduty_parser import normalize_pagerduty_payload
from server.mcp.server import handle
from server.oncall.security import verify_hmac, verify_slack_signature
from server.oncall.slack_blocks import approval_message, incident_message
from server.sdlc.service import SDLCMemoryService
import hashlib, hmac, time


def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_pagerduty_normalization():
    item = normalize_pagerduty_payload({"event": {"data": {"incident": {"id": "PX1", "title": "Payments failing", "urgency": "high", "service": {"summary": "banking-api"}}}}})
    assert item["incident_id"] == "PD-PX1"
    assert item["service"] == "banking-api"
    assert item["severity"] == "P1"


def test_signed_webhooks():
    body, secret = b'{"ok":true}', "secret"
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_hmac(body, signature, secret, prefix="sha256=")
    timestamp = str(int(time.time()))
    slack = "v0=" + hmac.new(secret.encode(), b"v0:" + timestamp.encode() + b":" + body, hashlib.sha256).hexdigest()
    assert verify_slack_signature(body, timestamp, slack, secret)


def test_blocks_have_accessibility_fallback_and_governed_actions():
    incident = incident_message({"incident_id": "INC-1", "service": "banking-api", "severity": "P1", "incident_url": "https://aria.example/incidents/INC-1"})
    approval = approval_message(7, "INC-1", {"action": "rollback", "target": "banking-api"})
    assert incident["text"] and incident["blocks"][-1]["type"] == "context"
    assert {e["action_id"] for e in approval["blocks"][2]["elements"]} == {"aria_approve_action", "aria_reject_action"}


def test_sdlc_memory_is_durable_idempotent_and_correlates():
    db = db_session(); service = SDLCMemoryService(db)
    now = datetime.utcnow()
    deploy = {"event_id": "deploy-1", "event_type": "deployment", "service": "banking-api", "revision": "abc123", "occurred_at": now.isoformat()}
    alert = {"event_id": "alert-1", "event_type": "alert_change", "service": "banking-api", "occurred_at": (now + timedelta(minutes=10)).isoformat()}
    first = service.record(deploy, "sre-1")
    assert service.record(deploy, "sre-1")["event_id"] == first["event_id"]
    service.record(alert, "sre-1")
    context = service.context("banking-api")
    assert context["count"] == 2 and context["correlations"][0]["revision"] == "abc123"


def test_mcp_exposes_read_only_investigation_tools():
    response = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    names = {tool["name"] for tool in response["result"]["tools"]}
    assert "aria_investigate" in names
    assert not any("execute" in name or "approve" in name for name in names)
