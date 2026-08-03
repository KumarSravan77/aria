from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from server.db.session import get_db
from server.authz.authorization_service import AuthorizationService
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
def invoke(req: GraphInvestigationRequest, db: Session = Depends(get_db), _user=Depends(require_auth)):
    service = req.incident.get("service")
    if not AuthorizationService().can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied investigation for this service")
    req.incident.setdefault("team", getattr(_user, "team", "unknown"))
    return LangGraphInvestigationWorkflow.persistent(db).invoke(req.incident, active_incidents=req.active_incidents)

@router.post("/replay")
def replay(req: GraphInvestigationRequest, _user=Depends(require_auth)):
    return InvestigationReplayEngine().replay(req.incident)
