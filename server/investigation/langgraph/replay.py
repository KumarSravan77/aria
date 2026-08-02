from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from server.investigation.langgraph.graph import LangGraphInvestigationWorkflow

@dataclass
class InvestigationReplayEngine:
    def replay(self, incident: dict[str, Any], expected_route: list[str] | None = None) -> dict[str, Any]:
        result = LangGraphInvestigationWorkflow().invoke(incident)
        route = result["summary"]["route"]
        return {"replayed": True, "route": route, "expected_route": expected_route, "route_match": expected_route is None or route == expected_route, "result": result}
