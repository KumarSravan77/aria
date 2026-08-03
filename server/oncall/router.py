from __future__ import annotations

import json
from urllib.parse import parse_qs
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from server.api.security import require_auth
from server.authz.authorization_service import AuthorizationService
from server.config import settings
from server.db.session import get_db
from server.incidents.repository import IncidentRepository
from server.intake.pagerduty_parser import normalize_pagerduty_payload
from server.models.schemas import UserContext
from server.oncall.security import verify_hmac, verify_slack_signature
from server.oncall.slack_blocks import incident_message, approval_message
from server.sdlc.service import SDLCMemoryService

router = APIRouter(prefix="/oncall", tags=["on-call"])
authz = AuthorizationService()


@router.post("/webhooks/pagerduty")
async def pagerduty_webhook(request: Request, x_aria_signature: str | None = Header(default=None), db: Session = Depends(get_db)):
    body = await request.body()
    if not verify_hmac(body, x_aria_signature, settings.pagerduty_webhook_secret, prefix="sha256="):
        raise HTTPException(status_code=401, detail="Invalid PagerDuty webhook signature")
    incident = normalize_pagerduty_payload(json.loads(body))
    repo = IncidentRepository(db); repo.upsert_incident(incident["incident_id"], incident)
    repo.add_timeline(incident["incident_id"], "pagerduty_event", "PagerDuty incident received", {"status": incident["status"]})
    return {"accepted": True, "incident": incident, "collaboration": incident_message(incident)}


@router.post("/webhooks/slack/interactions")
async def slack_interactions(request: Request, x_slack_request_timestamp: str | None = Header(default=None), x_slack_signature: str | None = Header(default=None)):
    body = await request.body()
    if not verify_slack_signature(body, x_slack_request_timestamp, x_slack_signature, settings.slack_signing_secret, settings.webhook_timestamp_tolerance_seconds):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")
    # Interaction identity is returned for the authenticated ARIA approval endpoint.
    # This webhook never executes or approves a production action by itself.
    form = parse_qs(body.decode("utf-8")); payload = json.loads((form.get("payload") or ["{}"]) [0])
    action = (payload.get("actions") or [{}])[0]
    return {"response_type": "ephemeral", "text": "Identity verified. Complete this decision through ARIA's authenticated approval API.", "action_id": action.get("action_id"), "approval_id": action.get("value"), "slack_user_id": (payload.get("user") or {}).get("id")}


@router.post("/sdlc/events")
def record_sdlc_event(payload: dict, db: Session = Depends(get_db), user: UserContext = Depends(require_auth)):
    service = payload.get("service", "")
    if not authz.can_access_service(user, service): raise HTTPException(status_code=403, detail="ReBAC denied SDLC event access")
    try: return SDLCMemoryService(db).record(payload, user.id or "unknown")
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/sdlc/{service}/context")
def sdlc_context(service: str, window_hours: int = 168, db: Session = Depends(get_db), user: UserContext = Depends(require_auth)):
    if not authz.can_access_service(user, service): raise HTTPException(status_code=403, detail="ReBAC denied SDLC context access")
    return SDLCMemoryService(db).context(service, window_hours)


@router.post("/identities/link")
def link_identity(payload: dict, db: Session = Depends(get_db), user: UserContext = Depends(require_auth)):
    if user.role not in {"admin", "incident-commander"}: raise HTTPException(status_code=403, detail="Admin or incident commander required")
    try: return SDLCMemoryService(db).link_identity(payload["aria_user_id"], payload["provider"], payload["external_user_id"], payload.get("team", "unknown"), user.id or "unknown")
    except (KeyError, ValueError) as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/render/incident")
def render_incident(payload: dict, user: UserContext = Depends(require_auth)):
    if not authz.can_access_service(user, payload.get("service", "")): raise HTTPException(status_code=403, detail="ReBAC denied")
    return incident_message(payload, payload.get("analysis"))


@router.post("/render/approval")
def render_approval(payload: dict, user: UserContext = Depends(require_auth)):
    return approval_message(int(payload["approval_id"]), payload.get("incident_id", "unknown"), payload.get("action") or {})
