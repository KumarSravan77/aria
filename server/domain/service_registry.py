from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml


DEFAULT_REGISTRY = Path("config/canadian_enterprise_services.yaml")


@dataclass
class ServiceRegistry:
    registry_path: Path = DEFAULT_REGISTRY

    def _load(self) -> dict[str, Any]:
        if not self.registry_path.exists():
            return {"domains": {}}
        return yaml.safe_load(self.registry_path.read_text()) or {"domains": {}}

    def domains(self) -> dict[str, Any]:
        return self._load().get("domains", {})

    def list_domains(self) -> list[dict[str, Any]]:
        result = []
        for key, value in self.domains().items():
            result.append({
                "domain": key,
                "display_name": value.get("display_name", key),
                "description": value.get("description"),
                "business_criticality": value.get("business_criticality"),
                "service_count": len(value.get("services", [])),
            })
        return result

    def list_services(self, domain: str | None = None) -> list[dict[str, Any]]:
        services = []
        for domain_key, domain_data in self.domains().items():
            if domain and domain_key != domain:
                continue
            for svc in domain_data.get("services", []):
                item = dict(svc)
                item["domain"] = domain_key
                item["domain_display_name"] = domain_data.get("display_name", domain_key)
                services.append(item)
        return services

    def get_service(self, name: str) -> dict[str, Any] | None:
        for svc in self.list_services():
            if svc.get("name") == name:
                return svc
        return None

    def incident_context(self, service_name: str) -> dict[str, Any]:
        svc = self.get_service(service_name)
        if not svc:
            return {
                "service": service_name,
                "found": False,
                "message": "service not found in Canadian enterprise registry",
            }
        return {
            "found": True,
            "service": svc["name"],
            "domain": svc["domain"],
            "owner_team": svc.get("owner_team"),
            "runtime": svc.get("runtime"),
            "language": svc.get("language"),
            "framework": svc.get("framework"),
            "slo": svc.get("slo", {}),
            "risk_profile": svc.get("risk_profile"),
            "common_incidents": svc.get("common_incidents", []),
        }
