from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from .broker import SecretBroker, SecretRequest
from .governance import SecretGovernanceAgent

router = APIRouter(prefix="/aria/platform/secrets", tags=["ARIA Secret Governance"])
broker = SecretBroker()
agent = SecretGovernanceAgent()


@router.post("/lease")
def issue_secret_lease(request: Dict[str, Any]) -> Dict[str, Any]:
    return broker.request_secret_lease(SecretRequest(
        service_id=request.get("service_id", ""),
        environment=request.get("environment", ""),
        secret_ref=request.get("secret_ref", ""),
        purpose=request.get("purpose", "runtime"),
        requester=request.get("requester", "aria"),
    ))


@router.post("/review")
def review_secret_risk(request: Dict[str, Any]) -> Dict[str, Any]:
    return agent.review(request)


@router.post("/sanitize-rag")
def sanitize_for_rag(request: Dict[str, Any]) -> Dict[str, Any]:
    return agent.sanitize_for_rag(request)
