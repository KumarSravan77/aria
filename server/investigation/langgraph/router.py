from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel
try:
    from server.api.security import require_auth
except Exception:
    def require_auth():
        return {"id": "local"}
from server.investigation.langgraph.graph import LangGraphInvestigationWorkflow
from server.investigation.langgraph.replay import InvestigationReplayEngine

router = APIRouter(prefix="/investigation-graph", tags=["investigation-graph"])

class GraphInvestigationRequest(BaseModel):
    incident: dict
    active_incidents: int = 0

@router.post("/invoke")
def invoke(req: GraphInvestigationRequest, _user=Depends(require_auth)):
    return LangGraphInvestigationWorkflow().invoke(req.incident, active_incidents=req.active_incidents)

@router.post("/replay")
def replay(req: GraphInvestigationRequest, _user=Depends(require_auth)):
    return InvestigationReplayEngine().replay(req.incident)
