from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel

try:
    from server.api.security import require_auth
except Exception:
    def require_auth():
        return {"id": "local"}

from server.ai_observability.langfuse_client import LangfuseClient
from server.ai_observability.evaluation_runner import EvaluationRunner

router = APIRouter(prefix="/ai-observability", tags=["ai-observability"])

class TraceRequest(BaseModel):
    incident_id: str = "demo-incident"
    service: str = "checkout-api"
    prompt: str = "Investigate high latency"
    answer: str = "Rollback deployment after latency regression"
    sources: list[dict] = []

@router.post("/trace")
def trace_ai(req: TraceRequest, _user=Depends(require_auth)):
    client = LangfuseClient()
    trace = client.start_trace(
        "aria.investigation",
        {"incident_id": req.incident_id, "service": req.service, "prompt": req.prompt},
        {"system": "aria"},
    )
    client.observe(trace, "prompt", req.prompt, req.answer, {"service": req.service})
    eval_result = EvaluationRunner().groundedness(req.answer, req.sources)
    client.score(trace, "groundedness", eval_result["groundedness"], eval_result["verdict"])
    return {"trace": client.flush(trace), "evaluation": eval_result}

@router.post("/evaluate")
def evaluate(req: TraceRequest, _user=Depends(require_auth)):
    runner = EvaluationRunner()
    return {
        "grounding": runner.groundedness(req.answer, req.sources),
        "safety": runner.remediation_safety(req.answer),
    }
