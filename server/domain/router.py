from __future__ import annotations

from fastapi import APIRouter, Depends

try:
    from server.api.security import require_auth
except Exception:
    def require_auth():
        return {"id": "local"}

from server.domain.service_registry import ServiceRegistry
from server.domain.scenario_catalog import list_scenarios

router = APIRouter(prefix="/domain", tags=["domain"])


@router.get("/domains")
def domains(_user=Depends(require_auth)):
    return {"domains": ServiceRegistry().list_domains()}


@router.get("/services")
def services(domain: str | None = None, _user=Depends(require_auth)):
    return {"services": ServiceRegistry().list_services(domain=domain)}


@router.get("/services/{service_name}")
def service(service_name: str, _user=Depends(require_auth)):
    return ServiceRegistry().incident_context(service_name)


@router.get("/scenarios")
def scenarios(domain: str | None = None, _user=Depends(require_auth)):
    return {"scenarios": list_scenarios(domain=domain)}
