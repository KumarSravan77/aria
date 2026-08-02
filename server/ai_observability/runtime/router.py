from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

try:
    from server.api.security import require_auth
except Exception:
    def require_auth():
        return {"id": "local"}

from server.ai_observability.runtime.session_recorder import AiRuntimeSessionRecorder
from server.ai_observability.runtime.cache_analyzer import PromptCacheAnalyzer
from server.ai_observability.runtime.flow_exporter import AgentFlowExporter
from server.ai_observability.runtime.replay_comparator import ReplayComparator
from server.agent_runtime.contract import AgentRuntimeContract
from server.agent_runtime.enforcer import AgentRuntimeEnforcer

router = APIRouter(prefix="/ai-runtime", tags=["ai-runtime"])
recorder = AiRuntimeSessionRecorder()


class StartSessionRequest(BaseModel):
    incident_id: str | None = None
    metadata: dict = {}


class RecordEventRequest(BaseModel):
    session_id: str
    event_type: str
    incident_id: str | None = None
    node: str | None = None
    tool: str | None = None
    status: str = "success"
    duration_ms: float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    metadata: dict = {}


class CacheAnalyzeRequest(BaseModel):
    previous_prompt: str
    current_prompt: str


class RuntimeValidateRequest(BaseModel):
    action: str
    tool: str | None = None
    approved: bool = False
    approval_id: str | None = None
    actor_id: str | None = None
    before_state: dict | None = None
    rollback_plan: dict | None = None


class ReplayCompareRequest(BaseModel):
    before: dict
    after: dict


@router.get("/contract")
def contract(_user=Depends(require_auth)):
    return AgentRuntimeContract().as_dict()


@router.post("/validate-action")
def validate_action(req: RuntimeValidateRequest, _user=Depends(require_auth)):
    return AgentRuntimeEnforcer().validate_action(
        req.action,
        tool=req.tool,
        approved=req.approved,
        approval_id=req.approval_id,
        actor_id=req.actor_id,
        before_state=req.before_state,
        rollback_plan=req.rollback_plan,
    )


@router.post("/sessions")
def start_session(req: StartSessionRequest, _user=Depends(require_auth)):
    return recorder.start_session(req.incident_id, req.metadata)


@router.post("/events")
def record_event(req: RecordEventRequest, _user=Depends(require_auth)):
    return recorder.record(
        req.session_id,
        req.event_type,
        incident_id=req.incident_id,
        node=req.node,
        tool=req.tool,
        status=req.status,
        duration_ms=req.duration_ms,
        input_tokens=req.input_tokens,
        output_tokens=req.output_tokens,
        cached_tokens=req.cached_tokens,
        metadata=req.metadata,
    )


@router.get("/sessions/{session_id}/summary")
def session_summary(session_id: str, _user=Depends(require_auth)):
    return recorder.summary(session_id)


@router.get("/sessions/{session_id}/events")
def session_events(session_id: str, _user=Depends(require_auth)):
    return {"events": recorder.list_events(session_id)}


@router.get("/sessions/{session_id}/flow")
def session_flow(session_id: str, _user=Depends(require_auth)):
    return AgentFlowExporter().export(recorder.list_events(session_id))


@router.post("/cache/analyze")
def cache_analyze(req: CacheAnalyzeRequest, _user=Depends(require_auth)):
    return PromptCacheAnalyzer().prefix_match(req.previous_prompt, req.current_prompt)


@router.post("/replay/compare")
def replay_compare(req: ReplayCompareRequest, _user=Depends(require_auth)):
    return ReplayComparator().compare(req.before, req.after)
