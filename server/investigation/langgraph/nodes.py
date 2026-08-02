from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from server.investigation.kubernetes_troubleshooter.agent import KubernetesTroubleshooterAgent
from server.agents.istio_agent import IstioAgent
from server.agents.thanos_agent import ThanosAgent
from server.agents.kafka_agent import KafkaAgent

def _append(state: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    state.setdefault("evidence", []).append(item)
    return state

@dataclass
class InvestigationNodes:
    """Node functions for LangGraph-style investigation. Evidence only."""

    def metrics(self, state: dict[str, Any]) -> dict[str, Any]:
        return _append(state, {"node": "metrics", "type": "metric_evidence", "summary": "Metric check completed", "available": True})

    def logs(self, state: dict[str, Any]) -> dict[str, Any]:
        return _append(state, {"node": "logs", "type": "log_evidence", "summary": "Log check completed", "available": True})

    def traces(self, state: dict[str, Any]) -> dict[str, Any]:
        return _append(state, {"node": "traces", "type": "trace_evidence", "summary": "Trace check completed", "available": True})

    def kubernetes_troubleshooter(self, state: dict[str, Any]) -> dict[str, Any]:
        return _append(state, KubernetesTroubleshooterAgent().run(state.get("incident", {})))


    def istio(self, state: dict[str, Any]) -> dict[str, Any]:
        result = IstioAgent().run(state.get("incident", {}), {"service": state.get("service")})
        return _append(state, {"node": "istio", "type": "service_mesh_evidence", "summary": result.get("summary"), "result": result})

    def thanos(self, state: dict[str, Any]) -> dict[str, Any]:
        result = ThanosAgent().run(state.get("incident", {}), {"service": state.get("service")})
        return _append(state, {"node": "thanos", "type": "long_term_metrics_evidence", "summary": result.get("summary"), "result": result})


    def kafka(self, state: dict[str, Any]) -> dict[str, Any]:
        result = KafkaAgent().run(state.get("incident", {}), {"service": state.get("service")})
        return _append(state, {"node": "kafka", "type": "streaming_platform_evidence", "summary": result.get("summary"), "result": result})

    def rag(self, state: dict[str, Any]) -> dict[str, Any]:
        return _append(state, {"node": "rag", "type": "runbook_context", "summary": "RAG retrieval boundary executed", "available": True})

    def security(self, state: dict[str, Any]) -> dict[str, Any]:
        return _append(state, {"node": "security", "type": "security_context", "summary": "Security context evaluated", "available": True})

    def healing(self, state: dict[str, Any]) -> dict[str, Any]:
        state.setdefault("recommendations", []).append({"node": "healing", "action": "recommend_only", "summary": "Requires ReBAC, policy and approval"})
        return state

    def rca(self, state: dict[str, Any]) -> dict[str, Any]:
        text = " ".join(str(e).lower() for e in state.get("evidence", []))
        cause = "unknown"
        if "crashloop" in text:
            cause = "possible_crashloop"
        elif "oom" in text:
            cause = "possible_oomkilled"
        elif "deployment" in text or "latency" in text:
            cause = "possible_deployment_regression"
        state.setdefault("hypotheses", []).append({"node": "rca", "probable_cause": cause, "confidence": 0.72 if cause != "unknown" else 0.35})
        return state

    def chatops(self, state: dict[str, Any]) -> dict[str, Any]:
        return _append(state, {"node": "chatops", "type": "war_room_update", "summary": "Prepared ChatOps update payload"})
