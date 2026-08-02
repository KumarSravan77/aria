from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PipelineStage:
    name: str
    purpose: str
    required: bool = True
    gates: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "required": self.required,
            "gates": self.gates,
            "tools": self.tools,
        }


@dataclass
class PipelineTemplate:
    service_id: str
    provider: str
    language: str
    deployment_target: str
    stages: List[PipelineStage]
    generated_files: Dict[str, str]
    standards: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_id": self.service_id,
            "provider": self.provider,
            "language": self.language,
            "deployment_target": self.deployment_target,
            "stages": [stage.to_dict() for stage in self.stages],
            "generated_files": self.generated_files,
            "standards": self.standards,
        }
