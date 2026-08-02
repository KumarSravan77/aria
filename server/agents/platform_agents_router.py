from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

try:
    from server.api.security import require_auth
except Exception:
    def require_auth():
        return {"id": "local"}

from server.agents.istio_agent import IstioAgent
from server.agents.thanos_agent import ThanosAgent
from server.agents.kafka_agent import KafkaAgent

router = APIRouter(prefix="/platform-agents", tags=["platform-agents"])


class AgentRunRequest(BaseModel):
    incident: dict
    context: dict = {}


@router.post("/istio")
def run_istio(req: AgentRunRequest, _user=Depends(require_auth)):
    return IstioAgent().run(req.incident, req.context)


@router.post("/thanos")
def run_thanos(req: AgentRunRequest, _user=Depends(require_auth)):
    return ThanosAgent().run(req.incident, req.context)


@router.post("/kafka")
def run_kafka(req: AgentRunRequest, _user=Depends(require_auth)):
    return KafkaAgent().run(req.incident, req.context)
