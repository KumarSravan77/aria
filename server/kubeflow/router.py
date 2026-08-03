from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from server.api.security import require_auth
from server.authz.authorization_service import AuthorizationService
from server.kubeflow.agent import KubeflowOperationsAgent

router = APIRouter(prefix="/kubeflow", tags=["kubeflow-operations"])
authz = AuthorizationService()


class KubeflowInvestigationRequest(BaseModel):
    resource_kind: str = Field(default="TrainJob")
    resource_name: str = Field(min_length=1)
    namespace: str = Field(default="default", min_length=1)
    service: str = Field(default="ml-platform")
    symptoms: list[str] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)


@router.get("/resources")
def supported_resources(_user=Depends(require_auth)):
    return {"resources": KubeflowOperationsAgent().client.supported_resources(), "mode": "read-only"}


@router.post("/investigate")
def investigate(req: KubeflowInvestigationRequest, user=Depends(require_auth)):
    if not authz.can_access_namespace(user, req.namespace):
        raise HTTPException(status_code=403, detail="ReBAC denied Kubeflow namespace access")
    agent = KubeflowOperationsAgent(headlamp_base_url=os.getenv("HEADLAMP_BASE_URL", ""))
    return agent.run(req.model_dump()).__dict__

