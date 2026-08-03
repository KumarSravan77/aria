from __future__ import annotations
from datetime import datetime
from typing import Optional
from server.utils_time import utc_now
from sqlalchemy import String, Text, DateTime, Integer, JSON, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from server.db.session import Base

class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    alert_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    service: Mapped[str] = mapped_column(String(120), index=True)
    environment: Mapped[str] = mapped_column(String(60), index=True)
    severity: Mapped[str] = mapped_column(String(40), index=True)
    source: Mapped[str] = mapped_column(String(80), default="unknown")
    status: Mapped[str] = mapped_column(String(40), default="TRIGGERED", index=True)
    channel_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    channel_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    dedupe_key: Mapped[Optional[str]] = mapped_column(String(250), index=True, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
    timeline: Mapped[list["IncidentTimelineEvent"]] = relationship(back_populates="incident", cascade="all, delete-orphan")

class IncidentTimelineEvent(Base):
    __tablename__ = "incident_timeline"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    message: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    incident: Mapped[Incident] = relationship(back_populates="timeline")

class IncidentAction(Base):
    __tablename__ = "incident_actions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(String(80), index=True)
    action: Mapped[str] = mapped_column(String(120))
    target: Mapped[str] = mapped_column(String(200))
    namespace: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    requested_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    executed: Mapped[bool] = mapped_column(Boolean, default=False)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class Approval(Base):
    __tablename__ = "incident_approvals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(String(80), index=True)
    action_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="PENDING")
    approver: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(120), default="system")
    action: Mapped[str] = mapped_column(String(180), index=True)
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str] = mapped_column(String(120), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class RCADraft(Base):
    __tablename__ = "incident_rca"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(String(80), index=True)
    markdown: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class OperationalMemoryEntry(Base):
    __tablename__ = "operational_memory"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service: Mapped[str] = mapped_column(String(120), index=True)
    incident_id: Mapped[str] = mapped_column(String(80), index=True)
    outcome: Mapped[str] = mapped_column(String(120), index=True)
    remediation: Mapped[str] = mapped_column(Text)
    team: Mapped[str] = mapped_column(String(120), index=True, default="unknown")
    environment: Mapped[str] = mapped_column(String(60), index=True, default="unknown")
    incident_type: Mapped[str] = mapped_column(String(120), index=True, default="unknown")
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_references: Mapped[list] = mapped_column(JSON, default=list)
    runbook_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    runbook_version: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    confidence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(40), index=True, default="candidate")
    verified_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    remediation_result: Mapped[dict] = mapped_column(JSON, default=dict)
    recovery_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    sensitivity: Mapped[str] = mapped_column(String(40), index=True, default="internal")
    retention_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    superseded_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class InvestigationCheckpoint(Base):
    __tablename__ = "investigation_checkpoints"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    checkpoint_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    investigation_id: Mapped[str] = mapped_column(String(80), index=True)
    incident_id: Mapped[str] = mapped_column(String(80), index=True)
    service: Mapped[str] = mapped_column(String(120), index=True)
    team: Mapped[str] = mapped_column(String(120), index=True, default="unknown")
    environment: Mapped[str] = mapped_column(String(60), index=True, default="unknown")
    node: Mapped[str] = mapped_column(String(120))
    mode: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    state_json: Mapped[dict] = mapped_column(JSON, default=dict)
    sensitivity: Mapped[str] = mapped_column(String(40), default="internal")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
