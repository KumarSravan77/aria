from __future__ import annotations
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from typing import Any

from server.agents.base import AgentResult
from server.agents.agent_router import AgentRouter
from server.agents.health_tracker import AgentHealthTracker
from server.orchestration.degradation import DegradationController, OrchestrationType
from server.orchestration.token_budget import TokenBudgetEnforcer
from server.orchestration.backpressure import BackpressureController
from server.orchestration.investigation_cache import InvestigationCache
from server.orchestration.circuit_breaker import CircuitBreakerRegistry


class MultiAgentOrchestrator:
    """Adaptive parallel agent orchestrator with survivability controls.

    Layer order on every investigation call:
    1. Backpressure check — reject if at capacity
    2. Cache check — return cached result for repeated (service, cause) pairs
    3. Degradation mode — reduce agent set under load
    4. Dynamic routing — skip irrelevant agents per incident profile
    5. Health filter — exclude quarantined agents
    6. Token budget — trim expensive agents if over budget
    7. Circuit breaker — skip agents whose downstream deps are open-circuited
    8. Parallel execution — ThreadPoolExecutor with stable result ordering
    9. Health recording — feed latency/success back to tracker
    """

    def __init__(
        self,
        agents: list,
        max_workers: int | None = None,
        router: AgentRouter | None = None,
        health: AgentHealthTracker | None = None,
        degradation: DegradationController | None = None,
        budget: TokenBudgetEnforcer | None = None,
        backpressure: BackpressureController | None = None,
        cache: InvestigationCache | None = None,
        circuits: CircuitBreakerRegistry | None = None,
    ) -> None:
        self.agents = agents
        self.max_workers = max_workers or min(len(agents) or 1, 9)
        self.router = router or AgentRouter()
        self.health = health or AgentHealthTracker()
        self.degradation = degradation or DegradationController()
        self.budget = budget or TokenBudgetEnforcer()
        self.backpressure = backpressure or BackpressureController()
        self.cache = cache or InvestigationCache()
        self.circuits = circuits or CircuitBreakerRegistry()

    def _run_agent(self, agent, incident: dict[str, Any], context: dict[str, Any]) -> tuple[AgentResult, float]:
        name = getattr(agent, "name", agent.__class__.__name__)
        cb = self.circuits.get(name)
        if not cb.can_execute():
            result = AgentResult(agent=name, available=False,
                                 summary=f"Circuit open — {name} temporarily excluded",
                                 error="circuit_open")
            return result, 0.0
        t0 = time.monotonic()
        try:
            result = agent.run(incident, context=context)
            cb.record_success()
        except Exception as exc:
            result = AgentResult(agent=name, available=False,
                                 summary="Agent failed safely", error=str(exc))
            cb.record_failure()
        latency_ms = (time.monotonic() - t0) * 1000
        self.health.record(name, result.available, latency_ms)
        return result, latency_ms

    def investigate(
        self,
        incident: dict[str, Any],
        context: dict[str, Any] | None = None,
        active_incidents: int = 0,
    ) -> dict[str, Any]:
        ctx = context or {}
        service = incident.get("service", "unknown")
        probable_cause = (
            incident.get("probable_cause")
            or (incident.get("analysis") or {}).get("probable_cause", "unknown")
        )

        # 1. Backpressure
        if not self.backpressure.acquire():
            return {
                "mode": "backpressure-rejected",
                "incident_id": incident.get("incident_id"),
                "service": service,
                "agent_count": 0,
                "evidence_count": 0,
                "agents": [],
                "summary": "Investigation rejected — orchestration at capacity. Retry shortly.",
                "recommendations": ["Retry investigation when load decreases."],
                "safety_boundary": "Backpressure active; no agents executed.",
                "orchestration_meta": self.backpressure.metrics(),
            }
        try:
            return self._run_investigation(incident, ctx, service, probable_cause, active_incidents)
        finally:
            self.backpressure.release()

    def _run_investigation(
        self,
        incident: dict[str, Any],
        ctx: dict[str, Any],
        service: str,
        probable_cause: str,
        active_incidents: int,
    ) -> dict[str, Any]:
        # 2. Cache
        cached = self.cache.get(service, probable_cause)
        if cached:
            return {**cached, "cache_hit": True}

        # 3. Degradation mode
        mode = self.degradation.get_mode(active_incidents)
        candidates = self.degradation.filter_agents(self.agents, mode)

        if mode == OrchestrationType.SURVIVAL:
            return {
                "mode": "survival",
                "incident_id": incident.get("incident_id"),
                "service": service,
                "agent_count": 0,
                "evidence_count": 0,
                "agents": [],
                "summary": "Survival mode active — AI orchestration suspended. Manual escalation required.",
                "recommendations": ["Page on-call immediately. Platform is in survival mode."],
                "safety_boundary": "No agents executed in survival mode.",
            }

        # 4. Dynamic routing
        routed, routing_reason = self.router.select(incident, candidates)

        # 5. Health filter
        healthy = [a for a in routed if self.health.is_healthy(getattr(a, "name", ""))]
        quarantined_names = [getattr(a, "name", "") for a in routed if a not in healthy]

        # 6. Token budget
        trimmed, estimated_tokens = self.budget.trim_to_budget(healthy)
        self.budget.record_usage(estimated_tokens)

        # 7 + 8. Parallel execution with circuit breaker inside _run_agent
        results_by_index: dict[int, AgentResult] = {}
        latencies: dict[str, float] = {}
        with ThreadPoolExecutor(max_workers=min(self.max_workers, max(1, len(trimmed)))) as executor:
            futures = {
                executor.submit(self._run_agent, agent, incident, ctx): index
                for index, agent in enumerate(trimmed)
            }
            for future in as_completed(futures):
                result, latency = future.result()
                idx = futures[future]
                results_by_index[idx] = result
                latencies[result.agent] = round(latency, 1)

        results = [results_by_index[i] for i in sorted(results_by_index)]
        evidence_count = sum(len(r.evidence) for r in results)
        recommendations: list[str] = []
        for r in results:
            recommendations.extend(r.recommendations)

        response = {
            "mode": f"multi-agent-{mode.value}-parallel",
            "incident_id": incident.get("incident_id"),
            "service": service,
            "agent_count": len(results),
            "evidence_count": evidence_count,
            "agents": [asdict(r) for r in results],
            "summary": f"{len(results)} agents completed with {evidence_count} evidence items",
            "recommendations": recommendations,
            "safety_boundary": "Agents can recommend and summarize. Infrastructure mutation still requires ReBAC, policy, approval, and async execution.",
            "orchestration_meta": {
                "degradation_mode": mode,
                "routing_reason": routing_reason,
                "quarantined_agents": quarantined_names,
                "estimated_tokens": estimated_tokens,
                "estimated_cost_usd": self.budget.estimate_cost_usd(estimated_tokens),
                "agent_latencies_ms": latencies,
                "backpressure": self.backpressure.metrics(),
                "cache_metrics": self.cache.metrics(),
            },
        }
        # 2b. Store in cache (skip caching survival/backpressure paths)
        self.cache.set(service, probable_cause, response)
        return response
