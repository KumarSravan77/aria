from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel
try:
    from server.api.security import require_auth
except Exception:
    def require_auth():
        return {"id": "local"}
from server.investigation.kubernetes_troubleshooter.agent import KubernetesTroubleshooterAgent

router = APIRouter(prefix="/kubernetes-troubleshooter", tags=["kubernetes-troubleshooter"])

class TroubleshootRequest(BaseModel):
    incident: dict

@router.post("/analyze")
def analyze(req: TroubleshootRequest, _user=Depends(require_auth)):
    return KubernetesTroubleshooterAgent().run(req.incident)
