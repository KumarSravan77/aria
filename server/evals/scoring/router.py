from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

try:
    from server.api.security import require_auth
except Exception:
    def require_auth():
        return {"id": "local"}

from server.evals.scoring.evaluation_scorecard import EvaluationScorecard

router = APIRouter(prefix="/evals/scorecard", tags=["eval-scorecard"])


class ScorecardRequest(BaseModel):
    route: list[str] = []
    expected_nodes: list[str] = []
    predicted_rca: str | None = None
    expected_rca: str | None = None
    recommendation: str = ""


@router.post("")
def scorecard(req: ScorecardRequest, _user=Depends(require_auth)):
    return EvaluationScorecard().score(
        route=req.route,
        expected_nodes=req.expected_nodes,
        predicted_rca=req.predicted_rca,
        expected_rca=req.expected_rca,
        recommendation=req.recommendation,
    )
