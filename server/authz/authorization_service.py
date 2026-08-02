from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from server.config import settings
from server.models.schemas import UserContext
from server.authz.openfga_client import OpenFGAClient

_RELATIONSHIP_FILE = Path(__file__).resolve().parent / "relationships.yaml"


@lru_cache(maxsize=1)
def _load_relationships() -> dict[str, Any]:
    if not _RELATIONSHIP_FILE.exists():
        return {"users": {}, "teams": {}}
    return yaml.safe_load(_RELATIONSHIP_FILE.read_text()) or {"users": {}, "teams": {}}


class AuthorizationService:
    """ReBAC service boundary.

    Local mode is the default for demos/tests. If REBAC_BACKEND=openfga is set,
    direct allow/deny checks delegate to OpenFGA and gracefully fall back to the
    local relationship graph when OpenFGA is unavailable. Vector allow-lists
    still come from the local seed because OpenFGA check APIs do not provide a
    list operation in this lightweight demo.
    """

    def __init__(self, relationships: dict[str, Any] | None = None, openfga_client: OpenFGAClient | None = None):
        self.relationships = relationships or _load_relationships()
        self.openfga = openfga_client or OpenFGAClient(
            api_url=settings.openfga_api_url or "http://localhost:8081",
            store_id=settings.openfga_store_id,
            authorization_model_id=settings.openfga_authorization_model_id,
            token=settings.openfga_token,
        )

    def _openfga_enabled(self) -> bool:
        return (settings.rebac_backend or "local").lower() == "openfga"

    def _check_openfga(self, user: UserContext | None, relation: str, object_: str) -> bool | None:
        if not self._openfga_enabled() or not user or not user.id:
            return None
        result = self.openfga.check(f"user:{user.id}", relation, object_)
        if result.get("available"):
            return bool(result.get("allowed"))
        return None

    def user_teams(self, user: UserContext | None) -> list[str]:
        if not user:
            return []
        explicit = self.relationships.get("users", {}).get(user.id or "", {}).get("teams", [])
        teams = set(explicit)
        if user.team:
            teams.add(user.team)
        return sorted(teams)

    def allowed_services(self, user: UserContext | None) -> list[str]:
        if not user:
            return []
        if user.role == "admin":
            services: set[str] = set()
            for team_data in self.relationships.get("teams", {}).values():
                services.update(team_data.get("owns_services", []))
                services.update(team_data.get("supports_services", []))
            return sorted(services)
        services: set[str] = set()
        for team in self.user_teams(user):
            team_data = self.relationships.get("teams", {}).get(team, {})
            services.update(team_data.get("owns_services", []))
            services.update(team_data.get("supports_services", []))
        return sorted(services)

    def can_access_service(self, user: UserContext | None, service: str | None) -> bool:
        if not service:
            return False
        if user and user.role == "admin":
            return True
        openfga_allowed = self._check_openfga(user, "can_access", f"service:{service}")
        if openfga_allowed is not None:
            return openfga_allowed
        return service in self.allowed_services(user)

    def can_access_namespace(self, user: UserContext | None, namespace: str | None) -> bool:
        if not namespace or not str(namespace).strip():
            return False
        if user and user.role == "admin":
            return True
        openfga_allowed = self._check_openfga(user, "can_access", f"namespace:{namespace}")
        if openfga_allowed is not None:
            return openfga_allowed
        # Local fallback: namespace name usually equals team or service namespace in the demo.
        return namespace in self.user_teams(user) or namespace in self.allowed_services(user) or namespace in {"demo", "default"}

    def can_view_incident(self, user: UserContext | None, incident: dict[str, Any]) -> bool:
        return self.can_access_service(user, incident.get("service"))

    def can_access_runbook_metadata(self, user: UserContext | None, metadata: dict[str, Any]) -> bool:
        service = metadata.get("service")
        if service:
            return self.can_access_service(user, service)
        team = metadata.get("team")
        return bool(team and team in self.user_teams(user))

    def can_approve_service_action(self, user: UserContext | None, service: str | None) -> bool:
        if not user or not service:
            return False
        if user.role not in {"sre", "incident-commander", "admin"}:
            return False
        if user.role == "admin":
            return True
        openfga_allowed = self._check_openfga(user, "can_approve", f"service:{service}")
        if openfga_allowed is not None:
            return openfga_allowed
        for team in self.user_teams(user):
            team_data = self.relationships.get("teams", {}).get(team, {})
            if service in team_data.get("can_approve_services", []):
                return True
        return False

    def vector_where_filter(self, user: UserContext | None) -> dict[str, Any]:
        if user and user.role == "admin":
            return {}
        services = self.allowed_services(user)
        if not services:
            return {"service": "__no_authorized_services__"}
        if len(services) == 1:
            return {"service": services[0]}
        return {"service": {"$in": services}}
