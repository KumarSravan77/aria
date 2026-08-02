from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ServiceProfile:
    service_id: str
    owner: str
    language: str
    framework: str
    tier: str
    environment: str
    compliance: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_platform_profile(self) -> Dict[str, Any]:
        return {
            "service_id": self.service_id,
            "owner": self.owner,
            "language": self.language,
            "framework": self.framework,
            "tier": self.tier,
            "environment": self.environment,
            "compliance": self.compliance,
            **self.metadata,
        }
