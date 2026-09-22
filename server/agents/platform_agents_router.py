from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from server.api.security import require_auth
from server.authz.authorization_service import AuthorizationService
from server.models.schemas import UserContext

from server.agents.istio_agent import IstioAgent
from server.agents.thanos_agent import ThanosAgent
from server.agents.kafka_agent import KafkaAgent

router = APIRouter(prefix="/platform-agents", tags=["platform-agents"])


class AgentRunRequest(BaseModel):
    incident: dict
    context: dict = Field(default_factory=dict)


@router.post("/istio")
def run_istio(req: AgentRunRequest, _user=Depends(require_auth)):
    return IstioAgent().run(req.incident, req.context)


@router.post("/thanos")
def run_thanos(req: AgentRunRequest, _user=Depends(require_auth)):
    return ThanosAgent().run(req.incident, req.context)


@router.post("/kafka")
def run_kafka(req: AgentRunRequest, user: UserContext = Depends(require_auth)):
    service = req.incident.get("service") or req.incident.get("target") or req.context.get("service")
    if user.role not in {"sre", "incident-commander", "admin"} or not AuthorizationService().can_access_service(user, service):
        raise HTTPException(status_code=403, detail="SRE role and service access required for Kafka diagnostics")
    return KafkaAgent().run(req.incident, req.context)
