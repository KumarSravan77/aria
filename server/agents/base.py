from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class AgentResult:
    agent: str
    available: bool
    summary: str
    evidence: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    error: str | None = None

class BaseAgent:
    name = "base"
    def run(self, incident: dict[str, Any], context: dict[str, Any] | None = None) -> AgentResult:
        raise NotImplementedError
