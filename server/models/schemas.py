from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field

class UserContext(BaseModel):
    id: str | None = "demo-user"
    role: str = "sre"
    team: str = "platform"

class AskRequest(BaseModel):
    question: str
    user: Optional[UserContext] = None

class InvestigationRequest(BaseModel):
    incident_id: str
    service: str
    environment: str = "dev"
    severity: str = "P2"
    symptoms: list[str] = []
    signals: dict[str, Any] = {}
    user: Optional[UserContext] = None

class HealRequest(BaseModel):
    action: str
    namespace: str = "demo"
    target: str
    replicas: int | None = None
    environment: str = "dev"
    dry_run: bool = True
    user: Optional[UserContext] = None

class IncidentIntakeRequest(BaseModel):
    incident_id: str
    source: str = "manual"
    alert_name: str = "manual-incident"
    service: str
    environment: str = "dev"
    severity: str = "P2"
    symptoms: list[str] = []
    signals: dict[str, Any] = {}
    user: Optional[UserContext] = None
    dedupe_key: str | None = None

class CollaborationMessageRequest(BaseModel):
    incident_id: str
    channel_id: str
    message: str
    metadata: dict[str, Any] = {}

class StatusTransitionRequest(BaseModel):
    status: str

class ApprovalRequest(BaseModel):
    incident_id: str
    action: dict[str, Any]

class ApprovalDecisionRequest(BaseModel):
    approved: bool
    reason: str | None = None
