from __future__ import annotations
from typing import Any, Literal, TypedDict

class InvestigationState(TypedDict, total=False):
    incident: dict[str, Any]
    incident_id: str
    investigation_id: str
    service: str
    severity: str
    mode: Literal["NORMAL", "DEGRADED", "SURVIVAL"]
    signals: list[str]
    routing: list[str]
    evidence: list[dict[str, Any]]
    hypotheses: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    errors: list[dict[str, Any]]
    checkpoints: list[dict[str, Any]]
    safety_boundary: str
