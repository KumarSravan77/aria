from fastapi import APIRouter, Depends, HTTPException

from server.api.security import require_auth
from server.models.schemas import UserContext
from server.observability.prometheus_client import PrometheusClient
from server.telemetry.capacity import capacity_plan
from server.telemetry.pipeline_analyzer import PipelineAnalyzer
from server.config import settings

router = APIRouter(prefix="/telemetry", tags=["telemetry-platform"])
analyzer = PipelineAnalyzer(PrometheusClient(base_url=settings.prometheus_url))


@router.get("/health")
def pipeline_health(_user: UserContext = Depends(require_auth)):
    snapshot = analyzer.snapshot()
    return {**snapshot, "recommendations": analyzer.recommend(snapshot)}


@router.get("/capacity")
def pipeline_capacity(
    tb_per_day: float = 1.0,
    peak_multiplier: float = 3.0,
    replication_factor: int = 3,
    kafka_retention_hours: int = 24,
    _user: UserContext = Depends(require_auth),
):
    try:
        return capacity_plan(tb_per_day, peak_multiplier, replication_factor, kafka_retention_hours)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/remediation/propose")
def remediation_proposal(payload: dict, _user: UserContext = Depends(require_auth)):
    """Recommendation-only boundary; execution stays in ARIA's governed healing path."""
    action = payload.get("action", "scale_gateway")
    allowed = {"scale_gateway", "increase_consumer_concurrency", "quarantine_noisy_tenant", "adjust_retention"}
    if action not in allowed:
        raise HTTPException(status_code=422, detail="unsupported telemetry remediation")
    return {
        "executed": False,
        "dry_run": True,
        "action": action,
        "target": payload.get("target", "otel-gateway"),
        "reason": payload.get("reason", "telemetry pipeline evidence requires operator review"),
        "safety_boundary": "Submit an approved GitOps change; this endpoint never mutates infrastructure.",
    }
