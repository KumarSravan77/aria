from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from server.agents.kafka_agent import KafkaAgent
from server.api.security import require_auth
from server.authz.authorization_service import AuthorizationService
from server.models.schemas import UserContext

router = APIRouter(prefix="/integrations/fire-drill", tags=["fire-drill-integration"])


class FireDrillIncident(BaseModel):
    incident_id: str = Field(min_length=3, max_length=128)
    service: str = Field(pattern=r"^[a-z][a-z0-9-]{2,80}$")
    severity: Literal["P1", "P2", "P3", "P4"]
    source: Literal["fire-drill"]
    signals: list[str] = Field(min_length=2, max_length=32)
    topic: str | None = None
    consumer_group: str | None = None


class FireDrillContext(BaseModel):
    experiment_id: str = Field(min_length=3, max_length=128)
    event_id: str = Field(min_length=3, max_length=128)
    plan_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    evidence_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    scenario: str
    evidence_mode: Literal["synthetic"]
    environment: Literal["development", "staging"]
    approved_by: str | None = None
    blast_radius_percent: int = Field(ge=1, le=25)
    automatic_remediation: Literal[False] = False
    streaming_observation: dict[str, Any] = Field(default_factory=dict)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    slo: dict[str, Any] = Field(default_factory=dict)
    fire_drill_report: dict[str, Any] = Field(default_factory=dict)
    qualification_verdict: Literal["PASS", "ACTION_REQUIRED"] = "ACTION_REQUIRED"


class FireDrillInvestigationRequest(BaseModel):
    incident: FireDrillIncident
    context: FireDrillContext


def investigate_fire_drill(payload: FireDrillInvestigationRequest, agent: KafkaAgent | None = None) -> dict[str, Any]:
    canonical = json.dumps(payload.context.streaming_observation, sort_keys=True).encode()
    actual_digest = "sha256:" + hashlib.sha256(canonical).hexdigest()
    if actual_digest != payload.context.evidence_digest:
        raise ValueError("streaming observation digest mismatch")
    kafka = (agent or KafkaAgent()).run(payload.incident.model_dump(), payload.context.model_dump())
    return {
        "schema_version": "1.0",
        "source": "aria",
        "incident_id": payload.incident.incident_id,
        "experiment_id": payload.context.experiment_id,
        "event_id": payload.context.event_id,
        "plan_digest": payload.context.plan_digest,
        "evidence_digest": payload.context.evidence_digest,
        "evidence_mode": payload.context.evidence_mode,
        "investigation": kafka,
        "observation": payload.context.streaming_observation,
        "findings": payload.context.findings,
        "slo": payload.context.slo,
        "fire_drill_report": payload.context.fire_drill_report,
        "qualification_verdict": payload.context.qualification_verdict,
        "decision": "human-review-required",
        "automatic_remediation": False,
        "safety_boundary": "read-only streaming investigation; policy and approval required for remediation",
    }


@router.post("/streaming")
def streaming_fire_drill(
    payload: FireDrillInvestigationRequest,
    user: UserContext = Depends(require_auth),
) -> dict[str, Any]:
    if user.role not in {"sre", "incident-commander", "admin"} or not AuthorizationService().can_access_service(
        user, payload.incident.service
    ):
        raise HTTPException(status_code=403, detail="SRE role and service access required for Fire Drill evidence intake")
    try:
        return investigate_fire_drill(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
