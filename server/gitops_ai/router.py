from __future__ import annotations
from fastapi import APIRouter, Depends

try:
    from server.api.security import require_auth
except Exception:
    def require_auth():
        return {"id": "local"}

from server.gitops_ai.remediation_service import GitOpsRemediationService

router = APIRouter(prefix="/gitops-ai", tags=["gitops-ai"])

@router.post("/propose")
def propose(service: str, issue: str, dry_run: bool = True, _user=Depends(require_auth)):
    return GitOpsRemediationService().propose(service, issue, dry_run)
