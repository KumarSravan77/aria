from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from server.api.security import require_auth
from server.authz.authorization_service import AuthorizationService
from server.config import settings
from server.models.schemas import UserContext
from server.observability.otel import current_traceparent

router = APIRouter(prefix="/integrations/on-call", tags=["on-call-integration"])
authz = AuthorizationService()


class SignalEvidence(BaseModel):
    source: str = Field(min_length=2, max_length=100)
    uri: str = Field(min_length=3, max_length=2000)
    summary: str = Field(min_length=3, max_length=5000)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SignalHypothesis(BaseModel):
    summary: str = Field(min_length=3, max_length=2000)
    confidence: float = Field(ge=0, le=1)
    evidence_uris: list[str] = Field(min_length=1)


class IntelligencePublishRequest(BaseModel):
    signal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    service: str = Field(pattern=r"^[a-z][a-z0-9-]{2,80}$")
    environment: Literal["development", "staging", "production"] = "production"
    severity: Literal["low", "medium", "high", "critical"]
    title: str = Field(min_length=3, max_length=300)
    summary: str = Field(min_length=3, max_length=5000)
    confidence: float = Field(ge=0, le=1)
    affected_services: list[str] = Field(default_factory=list)
    evidence: list[SignalEvidence] = Field(min_length=1)
    hypotheses: list[SignalHypothesis] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


def _signature(secret: str, timestamp: str, nonce: str, body: bytes) -> str:
    message = timestamp.encode() + b"." + nonce.encode() + b"." + body
    return "sha256=" + hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


class OnCallSREClient:
    def __init__(self, base_url: str, secret: str, timeout_seconds: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.secret = secret
        self.timeout_seconds = timeout_seconds

    @property
    def available(self) -> bool:
        return bool(self.base_url and self.secret)

    def publish(self, request: IntelligencePublishRequest) -> dict[str, Any]:
        if not self.available:
            return {"available": False, "error": "on-call integration is not configured"}
        payload = {
            "schema_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "aria",
            **request.model_dump(mode="json"),
            "traceparent": current_traceparent(),
        }
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        timestamp, nonce = str(int(time.time())), str(uuid.uuid4())
        headers = {
            "Content-Type": "application/json",
            "X-ARIA-Timestamp": timestamp,
            "X-ARIA-Nonce": nonce,
            "X-ARIA-Signature": _signature(self.secret, timestamp, nonce, body),
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/intelligence/aria",
                data=body,
                headers=headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            return {"available": False, "error": str(exc), "signal_id": request.signal_id}
        return {
            "available": True,
            "signal_id": request.signal_id,
            "on_call": response.json(),
            "traceparent": payload["traceparent"],
        }


@router.post("/publish")
def publish_to_on_call(
    payload: IntelligencePublishRequest,
    _user: UserContext = Depends(require_auth),
) -> dict[str, Any]:
    if not authz.can_access_service(_user, payload.service):
        raise HTTPException(status_code=403, detail="ReBAC denied on-call publication")
    client = OnCallSREClient(
        settings.on_call_sre_url or "",
        settings.on_call_sre_integration_secret or "",
        settings.on_call_sre_timeout_seconds,
    )
    result = client.publish(payload)
    if not result["available"]:
        raise HTTPException(status_code=503, detail=result)
    return result
