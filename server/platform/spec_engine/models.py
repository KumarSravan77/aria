from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ServiceSpecContext:
    service_profile: Dict[str, Any]
    golden_path: Dict[str, Any]
    capabilities: List[Dict[str, Any]]
    policies: List[Dict[str, Any]]
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    remediations: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def service_id(self) -> str:
        return self.service_profile.get("service", {}).get("id", "unknown")
