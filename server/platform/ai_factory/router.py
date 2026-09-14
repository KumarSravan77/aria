from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from server.api.security import require_auth
from server.platform.ai_factory.planner import AiFactoryPlanner

router = APIRouter(prefix="/ai-factory", tags=["ai-factory"])
planner = AiFactoryPlanner()


class WorkloadPlanRequest(BaseModel):
    tenant: str
    workload_type: str
    trust_level: str
    gpu_count: int = Field(default=1, ge=1, le=64)
    gpu_memory_gib: int | None = Field(default=None, ge=1)
    priority: str = "standard"
    distributed: bool = False


class CapacityRequest(BaseModel):
    nodes: list[dict]


@router.post("/plan")
def plan_workload(request: WorkloadPlanRequest, _user=Depends(require_auth)):
    try:
        return planner.plan(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/capacity")
def capacity(request: CapacityRequest, _user=Depends(require_auth)):
    return planner.capacity_summary(request.nodes)
