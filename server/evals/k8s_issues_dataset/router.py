from __future__ import annotations

from fastapi import APIRouter, Depends

try:
    from server.api.security import require_auth
except Exception:
    def require_auth():
        return {"id": "local"}

from server.evals.k8s_issues_dataset.replay_runner import K8sIssueReplayRunner

router = APIRouter(prefix="/evals/k8s-issues", tags=["k8s-issues-evals"])


@router.get("/normalized")
def normalized(_user=Depends(require_auth)):
    return K8sIssueReplayRunner().list_normalized()


@router.post("/replay")
def replay(limit: int = 10, _user=Depends(require_auth)):
    return K8sIssueReplayRunner().replay(limit=limit)
