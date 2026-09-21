from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import uuid
from server.investigation.langgraph.checkpoints import InMemoryCheckpointStore
from server.investigation.langgraph.nodes import InvestigationNodes
from server.investigation.langgraph.routing import GraphRouter
from server.investigation.langgraph.state_utils import route_budget
from sqlalchemy.orm import Session

@dataclass
class LangGraphInvestigationWorkflow:
    """LangGraph-compatible investigation workflow with local fallback."""
    router: GraphRouter = field(default_factory=GraphRouter)
    nodes: InvestigationNodes = field(default_factory=InvestigationNodes)
    checkpoints: InMemoryCheckpointStore = field(default_factory=InMemoryCheckpointStore)

    @classmethod
    def persistent(cls, db: Session) -> "LangGraphInvestigationWorkflow":
        return cls(checkpoints=InMemoryCheckpointStore(db=db))

    def invoke(self, incident: dict[str, Any], active_incidents: int = 0) -> dict[str, Any]:
        investigation_id = str(uuid.uuid4())
        route = route_budget(self.router.route(incident, active_incidents=active_incidents))
        mode = self.router.select_mode(active_incidents)
        state: dict[str, Any] = {
            "incident": incident,
            "incident_id": incident.get("incident_id") or incident.get("id") or investigation_id,
            "investigation_id": investigation_id,
            "service": incident.get("service") or incident.get("target") or "unknown",
            "team": incident.get("team", "unknown"),
            "environment": incident.get("environment", "unknown"),
            "sensitivity": incident.get("sensitivity", "internal"),
            "severity": incident.get("severity", "P3"),
            "mode": mode,
            "signals": incident.get("signals", []),
            "routing": route,
            "evidence": [],
            "hypotheses": [],
            "recommendations": [],
            "errors": [],
            "checkpoints": [],
            "safety_boundary": "Graph nodes recommend only; execution remains behind ReBAC, policy and approvals.",
        }
        state = self._run_graph(state, route, investigation_id)
        return {
            "workflow": "langgraph_investigation" if self._langgraph_available() else "bounded_fallback_investigation",
            "langgraph_installed": self._langgraph_available(),
            "state": state,
            "summary": {
                "investigation_id": investigation_id,
                "mode": mode,
                "route": route,
                "evidence_count": len(state.get("evidence", [])),
                "hypothesis_count": len(state.get("hypotheses", [])),
                "error_count": len(state.get("errors", [])),
            },
        }

    def _run_graph(self, state: dict[str, Any], route: list[str], investigation_id: str) -> dict[str, Any]:
        try:
            from langgraph.graph import END, START, StateGraph
            from server.investigation.langgraph.state import InvestigationState
        except ImportError:
            return self._run_fallback(state, route, investigation_id)

        builder = StateGraph(InvestigationState)
        previous = START
        for index, node_name in enumerate(route):
            graph_name = f"{index:02d}_{node_name}"

            def execute(current, selected=node_name):
                return self._execute_node(current, selected, investigation_id)

            builder.add_node(graph_name, execute)
            builder.add_edge(previous, graph_name)
            previous = graph_name
        builder.add_edge(previous, END)
        return dict(builder.compile().invoke(state))

    def _run_fallback(self, state: dict[str, Any], route: list[str], investigation_id: str) -> dict[str, Any]:
        for node_name in route:
            state = self._execute_node(state, node_name, investigation_id)
        return state

    def _execute_node(self, state: dict[str, Any], node_name: str, investigation_id: str) -> dict[str, Any]:
        try:
            state = getattr(self.nodes, node_name)(state)
        except Exception as exc:
            state.setdefault("errors", []).append({"node": node_name, "error": str(exc)})
        state.setdefault("checkpoints", []).append(self.checkpoints.save(investigation_id, node_name, state))
        return state

    def _langgraph_available(self) -> bool:
        try:
            import langgraph  # noqa
            return True
        except Exception:
            return False
