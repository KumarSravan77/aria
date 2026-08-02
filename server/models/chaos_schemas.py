from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class ChaosRunRequest(BaseModel):
    experiment: str = Field(..., examples=["pod-delete", "cpu-hog", "memory-hog", "network-latency", "dns-failure"])
    namespace: str = "demo"
    service: str = "checkout-api"
    app_label: str = "app=checkout-api"
    duration_seconds: Optional[int] = None
    dry_run: bool = True


class ChaosValidationRequest(BaseModel):
    service: str = "checkout-api"
    experiment: str = "pod-delete"
    incident_created: bool = False
    alert_fired: bool = False
    healing_succeeded: bool = False
    rag_sources: int = 0
    mttr_seconds: int | None = None
    slo_burn_observed: bool = False
