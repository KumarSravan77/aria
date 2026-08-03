from __future__ import annotations
from server.platform.kubernetes_internals.router import router as kubernetes_internals_router
from server.ai_observability.runtime.router import router as ai_runtime_router
from server.rag_types.router import router as rag_types_router
from server.evals.scoring.router import router as eval_scorecard_router
from server.evals.k8s_issues_dataset.router import router as k8s_issues_router
from server.domain.router import router as domain_router
from server.agents.platform_agents_router import router as platform_agents_router
from server.investigation.langgraph.router import router as investigation_graph_router
from server.investigation.kubernetes_troubleshooter.router import router as kubernetes_troubleshooter_router
from server.ai_observability.router import router as ai_observability_router
from server.evals.router import router as evals_router
from server.gitops_ai.router import router as gitops_ai_router
from server.platform.router import router as self_service_platform_router
from server.platform.secrets.router import router as secrets_platform_router
import json
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from server.models.schemas import (
    AskRequest, InvestigationRequest, HealRequest, IncidentIntakeRequest,
    CollaborationMessageRequest, StatusTransitionRequest, ApprovalRequest, ApprovalDecisionRequest,
)
from server.rag.lazy_rag_service import LazyRagService as RagService
from server.correlation.incident_analyzer import IncidentAnalyzer
from server.healing.policy_validator import PolicyValidator
from server.healing.kubernetes_actions import KubernetesActions
from server.collaboration.channel_manager import ChannelManager
from server.collaboration.notification_router import NotificationRouter
from server.collaboration.ai_teammate import AITeammate
from server.collaboration.rca_writer import generate_rca_draft
from server.db.session import get_db, init_db
from server.incidents.repository import IncidentRepository
from server.intake.alertmanager_parser import normalize_alertmanager_payload
from server.events.event_bus import event_bus
from server.approvals.approval_service import ApprovalService
from server.observability.otel import setup_otel
from server.api.security import require_auth, require_alertmanager_signature, require_falco_signature
from server.models.schemas import UserContext
from server.authz.authorization_service import AuthorizationService
from server.workers.tasks import execute_approved_healing_action
from server.config import settings
from server.llm.incident_reasoner import IncidentReasoner
from server.llm.ollama_client import OllamaClient
from server.gitops.argocd_client import ArgoCDClient
from server.gitops.rollout_service import RolloutService
from server.observability.prometheus_client import PrometheusClient
from server.observability.loki_client import LokiClient
from server.observability.tempo_client import TempoClient
from server.cost.opencost_client import OpenCostClient
from server.scaling.keda_client import KedaClient
from server.topology.cilium_hubble_client import CiliumHubbleClient
from server.security_runtime.falco_parser import FalcoParser
from server.models.chaos_schemas import ChaosRunRequest, ChaosValidationRequest
from server.chaos.experiment_catalog import list_experiments
from server.chaos.litmus_client import LitmusChaosClient
from server.chaos.validation_engine import ChaosValidationEngine
from server.chaos.chaos_reporter import ChaosReporter
from server.chaos.experiment_runner import ChaosExperimentRunner
from server.telemetry.router import router as telemetry_router

from server.agents.orchestrator import MultiAgentOrchestrator
from server.agents.metrics_agent import MetricsAgent
from server.agents.logs_agent import LogsAgent
from server.agents.trace_agent import TraceAgent
from server.agents.k8s_agent import KubernetesAgent
from server.agents.rag_agent import RagAgent
from server.agents.healing_agent import HealingAgent
from server.agents.rca_agent import RcaAgent
from server.agents.slack_agent import SlackAgent
from server.agents.remediation_ranker import RemediationRankerAgent
from server.slo.slo_engine import SloEngine
from server.memory.operational_memory import OperationalMemory
from server.memory.remediation_scorer import RemediationScorer
from server.memory.rl_optimizer import RLOptimizer
from server.correlation.temporal_clusterer import TemporalClusterer
from server.forecasting.incident_forecaster import IncidentForecaster
from server.deployment.deployment_intelligence import DeploymentIntelligence
from server.chatops.command_parser import ChatOpsCommandParser
# Scalability & autonomy layer
from server.orchestration.degradation import DegradationController, OrchestrationType
from server.orchestration.token_budget import TokenBudgetEnforcer
from server.orchestration.backpressure import BackpressureController
from server.orchestration.investigation_cache import InvestigationCache
from server.orchestration.circuit_breaker import CircuitBreakerRegistry
from server.agents.agent_router import AgentRouter
from server.agents.health_tracker import AgentHealthTracker
from server.topology.dependency_graph import ServiceDependencyGraph
from server.topology.blast_radius import BlastRadiusAnalyzer
from server.topology.rca_topology_enricher import enrich_rca_with_topology
from server.integrations.servicenow_client import ServiceNowClient
from server.integrations.pagerduty_simulator import PagerDutySimulator
from fastapi.responses import StreamingResponse
from server.platform.canary_planner import CanaryPlanner
from server.platform.tool_registry import list_tools as list_platform_tools
from server.recovery.recovery_planner import RecoveryPlanner
from server.recovery.rto_rpo_tracker import RtoRpoTracker
from server.recovery.recovery_validator import RecoveryValidator
from server.observability.correlator import ObservabilityCorrelator
from server.slo.burn_rate_alerts import SloBurnRateAlertEngine
from server.chaos.scheduler import ChaosScheduler
from server.chaos.resilience_trending import ResilienceTrending
from server.security_runtime.policy_violation_ingestor import PolicyViolationIngestor
from server.chatops.interactive_approvals import InteractiveApprovalBuilder
from server.chatops.threaded_updates import ThreadedUpdateBuilder
from server.llm.guardrails import LLMGuardrails
from server.db.models import AuditLog, OperationalMemoryEntry

app = FastAPI(title="ARIA — Autonomous Resilience Intelligence Assistant", version="2.0.0")
setup_otel(app)
rag = RagService()
analyzer = IncidentAnalyzer()
policy = PolicyValidator(Path(__file__).resolve().parents[1] / "healing" / "policies" / "self_healing_policy.yaml")
k8s = KubernetesActions()
channel_manager = ChannelManager()
notifier = NotificationRouter()
ai_teammate = AITeammate()
authz = AuthorizationService()
reasoner = IncidentReasoner(OllamaClient(base_url=settings.ollama_base_url, model=settings.ollama_model))
argocd = ArgoCDClient(base_url=settings.argocd_api_url or "http://localhost:8082", token=settings.argocd_token)
rollouts = RolloutService()
prometheus = PrometheusClient(base_url=settings.prometheus_url)
loki = LokiClient(base_url=settings.loki_url)
tempo = TempoClient(base_url=settings.tempo_url)
opencost = OpenCostClient(base_url=settings.opencost_url)
keda = KedaClient()
hubble = CiliumHubbleClient()
falco_parser = FalcoParser()
chaos_validator = ChaosValidationEngine()
chaos_reporter = ChaosReporter()
chaos_runner = ChaosExperimentRunner(LitmusChaosClient(), chaos_validator, chaos_reporter)
# Intelligence layer — shared singletons accumulate state across requests
_scorer = RemediationScorer()
_rl = RLOptimizer()
_degradation = DegradationController()
_budget = TokenBudgetEnforcer(model=settings.ollama_model)
_backpressure = BackpressureController()
_inv_cache = InvestigationCache()
_circuits = CircuitBreakerRegistry()
_health = AgentHealthTracker()
_dep_graph = ServiceDependencyGraph()
_blast_radius = BlastRadiusAnalyzer(_dep_graph)
_servicenow = ServiceNowClient(
    base_url=settings.servicenow_url or "",
    token=settings.servicenow_token,
)
_pagerduty_sim = PagerDutySimulator()
_canary_planner = CanaryPlanner()
_recovery_planner = RecoveryPlanner()
_rto_rpo_tracker = RtoRpoTracker()
_recovery_validator = RecoveryValidator()
_obs_correlator = ObservabilityCorrelator(prometheus, loki, tempo, hubble)
slo_engine = SloEngine()                          # must be before _slo_alerts
_slo_alerts = SloBurnRateAlertEngine(slo_engine)
_chaos_scheduler = ChaosScheduler()
_resilience_trending = ResilienceTrending()
_policy_ingestor = PolicyViolationIngestor()
_approval_cards = InteractiveApprovalBuilder()
_thread_updates = ThreadedUpdateBuilder()
_llm_guardrails = LLMGuardrails()

multi_agent = MultiAgentOrchestrator(
    agents=[
        MetricsAgent(prometheus), LogsAgent(loki), TraceAgent(tempo), KubernetesAgent(),
        RagAgent(rag), HealingAgent(policy), RcaAgent(), SlackAgent(),
        RemediationRankerAgent(policy, _scorer, _rl),
    ],
    router=AgentRouter(),
    health=_health,
    degradation=_degradation,
    budget=_budget,
    backpressure=_backpressure,
    cache=_inv_cache,
    circuits=_circuits,
)
temporal_clusterer = TemporalClusterer()
incident_forecaster = IncidentForecaster()
deployment_intelligence = DeploymentIntelligence()
chatops_parser = ChatOpsCommandParser()

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok", "service": "aria", "version": "2.0.0"}


@app.post("/recovery/plan")
def recovery_plan(payload: dict, _user: UserContext = Depends(require_auth)):
    service = payload.get("service", "checkout-api")
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied recovery planning for this service")
    return _recovery_planner.plan(
        service=service,
        failure_type=payload.get("failure_type", "unknown"),
        environment=payload.get("environment", "prod"),
    )


@app.post("/recovery/validate")
def recovery_validate(payload: dict, _user: UserContext = Depends(require_auth)):
    service = payload.get("service", "checkout-api")
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied recovery validation for this service")
    return _recovery_validator.validate(
        service=service,
        replicas_ready=bool(payload.get("replicas_ready", True)),
        traffic_restored=bool(payload.get("traffic_restored", True)),
        data_restored=bool(payload.get("data_restored", True)),
        alerts_resolved=bool(payload.get("alerts_resolved", True)),
        rto_met=bool(payload.get("rto_met", True)),
        rpo_met=bool(payload.get("rpo_met", True)),
    )


@app.post("/recovery/rto-rpo")
def rto_rpo(payload: dict, _user: UserContext = Depends(require_auth)):
    service = payload.get("service", "checkout-api")
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied RTO/RPO access for this service")
    return _rto_rpo_tracker.evaluate(
        service=service,
        rto_target_minutes=int(payload.get("rto_target_minutes", 30)),
        rpo_target_minutes=int(payload.get("rpo_target_minutes", 15)),
        actual_recovery_minutes=int(payload.get("actual_recovery_minutes", 0)),
        actual_data_loss_minutes=int(payload.get("actual_data_loss_minutes", 0)),
    )



@app.get("/recovery/dr-checklist/{service}")
def dr_checklist(service: str, namespace: str = "demo", _user: UserContext = Depends(require_auth)):
    from server.platform.ha_recovery.regional_dr import dr_readiness_checklist
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied DR checklist for this service")
    return dr_readiness_checklist(service, namespace)

@app.get("/chaos/experiments")
def chaos_experiments(_user: UserContext = Depends(require_auth)):
    return {"available": settings.chaos_enabled, "experiments": list_experiments()}

@app.post("/chaos/run")
def chaos_run(req: ChaosRunRequest, _user: UserContext = Depends(require_auth)):
    if not settings.chaos_enabled:
        return {"available": False, "reason": "Chaos engineering is disabled. Set CHAOS_ENABLED=true to enable dry-run and Litmus workflows."}
    if not authz.can_access_service(_user, req.service):
        raise HTTPException(status_code=403, detail="ReBAC denied chaos access for this service")
    if not authz.can_access_namespace(_user, req.namespace):
        raise HTTPException(status_code=403, detail="ReBAC denied chaos access for this namespace")
    return chaos_runner.run(
        experiment=req.experiment,
        namespace=req.namespace,
        service=req.service,
        app_label=req.app_label,
        duration_seconds=req.duration_seconds,
        dry_run=req.dry_run,
    )

@app.post("/chaos/validate")
def chaos_validate(req: ChaosValidationRequest, _user: UserContext = Depends(require_auth)):
    if not authz.can_access_service(_user, req.service):
        raise HTTPException(status_code=403, detail="ReBAC denied chaos validation for this service")
    return chaos_validator.validate(
        service=req.service,
        experiment=req.experiment,
        incident_created=req.incident_created,
        alert_fired=req.alert_fired,
        healing_succeeded=req.healing_succeeded,
        rag_sources=req.rag_sources,
        mttr_seconds=req.mttr_seconds,
        slo_burn_observed=req.slo_burn_observed,
    )

@app.post("/chaos/report")
def chaos_report(req: ChaosValidationRequest, _user: UserContext = Depends(require_auth)):
    if not authz.can_access_service(_user, req.service):
        raise HTTPException(status_code=403, detail="ReBAC denied chaos report for this service")
    validation = chaos_validator.validate(
        service=req.service,
        experiment=req.experiment,
        incident_created=req.incident_created,
        alert_fired=req.alert_fired,
        healing_succeeded=req.healing_succeeded,
        rag_sources=req.rag_sources,
        mttr_seconds=req.mttr_seconds,
        slo_burn_observed=req.slo_burn_observed,
    )
    return {"validation": validation, "report_markdown": chaos_reporter.markdown(validation)}

@app.post("/agents/investigate")
def multi_agent_investigate(req: InvestigationRequest, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    if not authz.can_access_service(_user, req.service):
        raise HTTPException(status_code=403, detail="ReBAC denied multi-agent investigation for this service")
    # Pass memory items so RemediationRankerAgent can weight by past remediations
    memory_items = OperationalMemory(db).recall(req.service, team=None if _user.role == "admin" else _user.team, environment=req.environment, verified_only=True).get("items", [])
    return multi_agent.investigate(req.model_dump(), context={"user": _user, "memory_items": memory_items})

@app.post("/slo/evaluate")
def slo_evaluate(payload: dict, _user: UserContext = Depends(require_auth)):
    service = payload.get("service", "checkout-api")
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied SLO access for this service")
    return slo_engine.evaluate(
        service=service,
        total_requests=int(payload.get("total_requests", 10000)),
        failed_requests=int(payload.get("failed_requests", 0)),
        slo_target=float(payload.get("slo_target", 99.9)),
    )

@app.post("/memory/record")
def memory_record(payload: dict, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    service = payload.get("service", "unknown")
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied memory write for this service")
    try:
        result = OperationalMemory(db).record(
            service=service,
            incident_id=payload.get("incident_id", "unknown"),
            outcome=payload.get("outcome", "unknown"),
            remediation=payload.get("remediation", "unknown"),
            metadata={"recorded_by": _user.id, **payload.get("metadata", {})},
            team=_user.team,
            environment=payload.get("environment", "unknown"),
            incident_type=payload.get("incident_type", "unknown"),
            root_cause=payload.get("root_cause"),
            evidence_references=payload.get("evidence_references", []),
            runbook_id=payload.get("runbook_id"),
            runbook_version=payload.get("runbook_version"),
            model_version=payload.get("model_version"),
            prompt_version=payload.get("prompt_version"),
            confidence=payload.get("confidence"),
            remediation_result=payload.get("remediation_result", {}),
            recovery_metrics=payload.get("recovery_metrics", {}),
            sensitivity=payload.get("sensitivity", "internal"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    # Candidate memories never influence ranking until independently verified.
    return result

@app.get("/memory/{service}")
def memory_recall(service: str, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied memory read for this service")
    return OperationalMemory(db).recall(service, team=None if _user.role == "admin" else _user.team)

@app.post("/memory/{entry_id}/verify")
def memory_verify(entry_id: int, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    if _user.role not in {"incident-commander", "admin"}:
        raise HTTPException(status_code=403, detail="Independent incident-commander verification required")
    memory = OperationalMemory(db)
    row = db.get(OperationalMemoryEntry, entry_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    if not authz.can_access_service(_user, row.service):
        raise HTTPException(status_code=403, detail="ReBAC denied memory verification")
    try:
        result = memory.verify(entry_id, _user.id or "unknown")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    item = result["item"]
    meta = item.get("metadata", {})
    _rl.update(
        service=item["service"],
        probable_cause=item.get("root_cause") or meta.get("probable_cause", "unknown"),
        severity=meta.get("severity", "P2"),
        action=item["remediation"],
        success="mitigat" in item["outcome"].lower() or "resolved" in item["outcome"].lower(),
        mttr_seconds=meta.get("mttr_seconds"),
    )
    db.add(AuditLog(actor=_user.id or "unknown", action="memory.verify", resource_type="operational_memory", resource_id=str(entry_id), metadata_json={"service": item["service"], "incident_id": item["incident_id"]}))
    db.commit()
    return result

@app.get("/forecast/{service}")
def forecast_incident(service: str, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied forecast access for this service")
    slo = slo_engine.evaluate(service)
    memory_items = OperationalMemory(db).recall(service).get("items", [])
    cluster = temporal_clusterer.cluster(service, db)
    return incident_forecaster.forecast(service, slo, memory_items, cluster.get("cluster_size", 0))

@app.get("/incidents/{incident_id}/cluster")
def incident_cluster(incident_id: str, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    from server.incidents.repository import IncidentRepository
    incident = IncidentRepository(db).get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if not authz.can_view_incident(_user, incident.payload):
        raise HTTPException(status_code=403, detail="ReBAC denied access to this incident")
    return temporal_clusterer.cluster(incident.service, db)

# ── Scalability & Autonomy Endpoints ──────────────────────────────────────────

@app.get("/topology/graph")
def topology_graph(_user: UserContext = Depends(require_auth)):
    return _dep_graph.to_dict()

@app.get("/topology/{service}/blast-radius")
def blast_radius(service: str, severity: str = "P1", _user: UserContext = Depends(require_auth)):
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied topology access for this service")
    return _blast_radius.analyze(service, severity)

@app.get("/incidents/{incident_id}/rca-draft/topology")
def rca_draft_topology(incident_id: str, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    from server.incidents.repository import IncidentRepository
    repo = IncidentRepository(db)
    incident = repo.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if not authz.can_view_incident(_user, incident.payload):
        raise HTTPException(status_code=403, detail="ReBAC denied RCA access")
    payload = incident.payload or {}
    analysis = analyzer.analyze(payload)
    rca = generate_rca_draft(payload, repo.list_timeline(incident_id), analysis)
    blast = _blast_radius.analyze(incident.service, payload.get("severity", "P1"))
    enriched = enrich_rca_with_topology(rca, blast)
    repo.save_rca(incident_id, enriched)
    return {"incident_id": incident_id, "rca_markdown": enriched, "blast_radius": blast}

@app.get("/integrations/servicenow/{service}/changes")
def servicenow_changes(service: str, window_hours: int = 24, _user: UserContext = Depends(require_auth)):
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied ServiceNow access for this service")
    result = _servicenow.get_recent_changes(service, window_hours)
    risk = _servicenow.change_risk_score(result.get("changes", []))
    return {**result, "change_risk": risk}

@app.get("/integrations/pagerduty/{service}/escalation")
def pagerduty_escalation(service: str, severity: str = "P1", _user: UserContext = Depends(require_auth)):
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied PagerDuty access for this service")
    return _pagerduty_sim.simulate_escalation(service, severity)

@app.get("/orchestration/status")
def orchestration_status(_user: UserContext = Depends(require_auth)):
    return {
        "backpressure": _backpressure.metrics(),
        "cache": _inv_cache.metrics(),
        "agent_health": _health.summary(),
        "circuit_breakers": _circuits.all_status(),
        "token_budget": _budget.session_summary(),
        "degradation": _degradation.status(),
    }

@app.post("/orchestration/degradation")
def set_degradation_mode(payload: dict, _user: UserContext = Depends(require_auth)):
    if _user.role not in {"sre", "incident-commander", "admin"}:
        raise HTTPException(status_code=403, detail="Only SREs and commanders can change degradation mode")
    mode_str = payload.get("mode")
    if mode_str is None:
        _degradation.set_manual(None)
        return {"mode": "auto", "message": "Degradation returned to automatic threshold control"}
    try:
        mode = OrchestrationType(mode_str)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Unknown mode '{mode_str}'. Use: normal, degraded, survival")
    _degradation.set_manual(mode)
    return {"mode": mode, "message": f"Degradation manually set to {mode}"}

@app.get("/agents/{incident_id}/stream")
async def stream_investigation(
    incident_id: str,
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_auth),
):
    """U13 — Partial result streaming: yields agent results as SSE as they complete."""
    from server.incidents.repository import IncidentRepository
    incident = IncidentRepository(db).get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if not authz.can_view_incident(_user, incident.payload):
        raise HTTPException(status_code=403, detail="ReBAC denied")
    incident_dict = incident.payload or {}

    async def event_stream():
        for agent in multi_agent.agents:
            name = getattr(agent, "name", agent.__class__.__name__)
            if not _health.is_healthy(name):
                yield f"data: {json.dumps({'agent': name, 'skipped': True, 'reason': 'quarantined'})}\n\n"
                continue
            try:
                result = agent.run(incident_dict, context={"user": _user})
                yield f"data: {json.dumps({'agent': result.agent, 'summary': result.summary, 'evidence_count': len(result.evidence), 'recommendations': result.recommendations})}\n\n"
            except Exception as exc:
                yield f"data: {json.dumps({'agent': name, 'error': str(exc)})}\n\n"
        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ── Platform Tooling Endpoints (Kubernetes-native stack) ──────────────────────

@app.get("/platform/tools")
def platform_tools(_user: UserContext = Depends(require_auth)):
    return list_platform_tools()

@app.post("/platform/canary/plan")
def platform_canary_plan(payload: dict, _user: UserContext = Depends(require_auth)):
    service = payload.get("service", "checkout-api")
    namespace = payload.get("namespace", "demo")
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied canary planning for this service")
    if not authz.can_access_namespace(_user, namespace):
        raise HTTPException(status_code=403, detail="ReBAC denied canary planning for this namespace")
    return _canary_planner.plan(
        service=service,
        namespace=namespace,
        strategy=payload.get("strategy", "canary"),
        traffic_steps=payload.get("traffic_steps"),
    )

@app.post("/deployment/correlate")
def deployment_correlate(payload: dict, _user: UserContext = Depends(require_auth)):
    service = payload.get("service", "unknown")
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied deployment intelligence for this service")
    return deployment_intelligence.correlate(payload)

@app.post("/chatops/parse")
def chatops_parse(payload: dict, _user: UserContext = Depends(require_auth)):
    parsed = chatops_parser.parse(payload.get("text", ""))
    return {**parsed, "user": _user.id}

@app.post("/rag/ask")
def ask(req: AskRequest, _user: UserContext = Depends(require_auth)):
    return rag.answer(req.question, user=_user)

@app.post("/llm/reason")
def llm_reason(req: InvestigationRequest, _user: UserContext = Depends(require_auth)):
    if not settings.llm_enabled:
        return {"available": False, "reason": "LLM reasoning is disabled. Set LLM_ENABLED=true to enable Ollama-backed reasoning."}
    if not authz.can_access_service(_user, req.service):
        raise HTTPException(status_code=403, detail="ReBAC denied access to this service")
    payload = req.model_dump()
    analysis = analyzer.analyze(payload)
    rag_answer = rag.answer(analysis["rag_query"], user=_user)
    llm_result = reasoner.reason(payload, analysis, rag_answer)
    return _llm_guardrails.apply(llm_result, rag_answer, evidence=analysis.get("evidence") or analysis.get("findings") or [])

@app.get("/observability/{service}")
def service_observability(service: str, _user: UserContext = Depends(require_auth)):
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied access to this service")
    return {
        "service": service,
        "metrics": prometheus.query(f'rate(http_requests_total{{service="{service}"}}[5m])'),
        "logs": loki.query(f'{{app="{service}"}} |= "error"'),
        "traces": tempo.search_service_traces(service),
        "topology": hubble.service_topology(service),
    }


@app.post("/observability/correlate")
def observability_correlate(payload: dict, _user: UserContext = Depends(require_auth)):
    service = payload.get("service", "checkout-api")
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied observability correlation for this service")
    return _obs_correlator.correlate(
        service=service,
        window_minutes=int(payload.get("window_minutes", 30)),
        deployment=payload.get("deployment") or {},
    )

@app.post("/slo/burn-alert")
def slo_burn_alert(payload: dict, _user: UserContext = Depends(require_auth)):
    service = payload.get("service", "checkout-api")
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied SLO alert access for this service")
    return _slo_alerts.evaluate(
        service=service,
        total_requests=int(payload.get("total_requests", 10000)),
        failed_requests=int(payload.get("failed_requests", 0)),
        slo_target=float(payload.get("slo_target", 99.9)),
        window_minutes=int(payload.get("window_minutes", 30)),
    )

@app.post("/chaos/schedule")
def chaos_schedule(payload: dict, _user: UserContext = Depends(require_auth)):
    service = payload.get("service", settings.chaos_default_service)
    namespace = payload.get("namespace", settings.chaos_default_namespace)
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied chaos schedule for this service")
    if not authz.can_access_namespace(_user, namespace):
        raise HTTPException(status_code=403, detail="ReBAC denied chaos schedule for this namespace")
    return _chaos_scheduler.plan_weekly(service=service, namespace=namespace, experiments=payload.get("experiments"))

@app.get("/chaos/trends/{service}")
def chaos_trends(service: str, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied chaos trends for this service")
    memory = OperationalMemory(db).recall(service)
    return _resilience_trending.trend(service, memory)

@app.post("/webhooks/kyverno")
def kyverno_webhook(payload: dict, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    incidents = _policy_ingestor.normalize_kyverno(payload)
    results = []
    for incident in incidents:
        if not authz.can_access_service(_user, incident.get("service", "unknown")):
            raise HTTPException(status_code=403, detail="ReBAC denied Kyverno incident intake for this service")
        results.append(_create_incident(incident, db, user=_user))
    return {"received": len(incidents), "incidents": results}

@app.post("/webhooks/gatekeeper")
def gatekeeper_webhook(payload: dict, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    incidents = _policy_ingestor.normalize_gatekeeper(payload)
    results = []
    for incident in incidents:
        if not authz.can_access_service(_user, incident.get("service", "unknown")):
            raise HTTPException(status_code=403, detail="ReBAC denied Gatekeeper incident intake for this service")
        results.append(_create_incident(incident, db, user=_user))
    return {"received": len(incidents), "incidents": results}

@app.post("/chatops/approval-card")
def chatops_approval_card(payload: dict, _user: UserContext = Depends(require_auth)):
    return _approval_cards.build(
        approval_id=int(payload.get("approval_id", 0)),
        incident_id=payload.get("incident_id", "unknown"),
        action=payload.get("action") or {},
        requester=_user.id or "unknown",
    )

@app.post("/chatops/thread-update")
def chatops_thread_update(payload: dict, _user: UserContext = Depends(require_auth)):
    return _thread_updates.evidence_update(
        incident_id=payload.get("incident_id", "unknown"),
        evidence=payload.get("evidence") or [],
        recommendation=payload.get("recommendation"),
    )

@app.post("/llm/guardrails/validate")
def llm_guardrails_validate(payload: dict, _user: UserContext = Depends(require_auth)):
    return _llm_guardrails.validate_text(
        answer=payload.get("answer", ""),
        sources=payload.get("sources") or [],
        evidence=payload.get("evidence") or [],
    )

@app.get("/gitops/argocd/apps")
def argocd_apps(_user: UserContext = Depends(require_auth)):
    return argocd.list_apps()

@app.post("/gitops/argocd/{app_name}/sync")
def argocd_sync(app_name: str, revision: str | None = None, dry_run: bool = True, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    if not authz.can_access_service(_user, app_name):
        raise HTTPException(status_code=403, detail="ReBAC denied GitOps action for this app/service")
    if dry_run:
        return argocd.sync_app(app_name, revision=revision, dry_run=True)
    # ArgoCD sync mutates live state, so it must follow the same approval path as healing actions.
    approval = ApprovalService(db).request_approval(
        f"gitops-{app_name}",
        {"action": "argocd_sync", "target": app_name, "namespace": "argocd", "revision": revision, "environment": "prod"},
        requested_by=_user.id or "unknown",
    )
    return {"executed": False, "approval_required": True, "approval": approval, "message": "ArgoCD sync requires approval and async execution"}

@app.post("/gitops/rollouts/{namespace}/{rollout}/promote")
def rollout_promote(namespace: str, rollout: str, dry_run: bool = True, _user: UserContext = Depends(require_auth)):
    if not authz.can_access_namespace(_user, namespace):
        raise HTTPException(status_code=403, detail="ReBAC denied rollout access for this namespace")
    return rollouts.promote(rollout, namespace, dry_run=dry_run)

@app.post("/gitops/rollouts/{namespace}/{rollout}/abort")
def rollout_abort(namespace: str, rollout: str, dry_run: bool = True, _user: UserContext = Depends(require_auth)):
    if not authz.can_access_namespace(_user, namespace):
        raise HTTPException(status_code=403, detail="ReBAC denied rollout access for this namespace")
    return rollouts.abort(rollout, namespace, dry_run=dry_run)

@app.get("/cost/allocation")
def cost_allocation(namespace: str | None = None, _user: UserContext = Depends(require_auth)):
    if namespace and not authz.can_access_namespace(_user, namespace):
        raise HTTPException(status_code=403, detail="ReBAC denied cost allocation access for this namespace")
    return opencost.allocation(namespace=namespace)

@app.get("/scaling/keda/{namespace}/{service}/recommendation")
def keda_recommendation(namespace: str, service: str, _user: UserContext = Depends(require_auth)):
    if not authz.can_access_service(_user, service):
        raise HTTPException(status_code=403, detail="ReBAC denied access to this service")
    return keda.recommend_scaled_object(service=service, namespace=namespace)

@app.post("/webhooks/falco")
def falco_webhook(raw_body: bytes = Depends(require_falco_signature), db: Session = Depends(get_db)):
    payload = json.loads(raw_body.decode("utf-8"))
    incident = falco_parser.normalize(payload)
    incident["incident_id"] = payload.get("incident_id") or f"FALCO-{incident['alert_name']}"
    system_user = UserContext(id="falco-webhook", role="sre", team="platform")
    return _create_incident(incident, db, user=system_user)

@app.post("/investigate")
def investigate(req: InvestigationRequest, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    # Authorization must happen before any DB mutation. Otherwise a valid bearer token
    # could create/overwrite incident records for services it cannot access.
    if not authz.can_access_service(_user, req.service):
        raise HTTPException(status_code=403, detail="ReBAC denied access to this service")
    payload = req.model_dump()
    repo = IncidentRepository(db)
    repo.upsert_incident(req.incident_id, {**payload, "source": "manual_investigation", "alert_name": "manual-investigation"})
    analysis = analyzer.analyze(payload)
    rag_answer = rag.answer(analysis["rag_query"], user=_user)
    repo.add_timeline(req.incident_id, "manual_investigation", "Manual investigation completed", {"analysis": analysis})
    return {"incident_id": req.incident_id, "analysis": analysis, "runbook_guidance": rag_answer, "recommended_next_step": analysis.get("recommended_next_step")}

@app.post("/incidents/intake")
def incident_intake(req: IncidentIntakeRequest, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    if not authz.can_access_service(_user, req.service):
        raise HTTPException(status_code=403, detail="ReBAC denied incident intake for this service")
    return _create_incident(req.model_dump(), db, user=_user)

@app.post("/webhooks/alertmanager")
def alertmanager_webhook(raw_body: bytes = Depends(require_alertmanager_signature), db: Session = Depends(get_db)):
    payload = json.loads(raw_body.decode("utf-8"))
    incidents = normalize_alertmanager_payload(payload)
    results = [_create_incident(item, db) for item in incidents]
    return {"received": len(incidents), "incidents": results}

def _create_incident(incident: dict, db: Session, user: UserContext | None = None):
    repo = IncidentRepository(db)
    channel = channel_manager.create_incident_channel(incident["incident_id"], incident.get("service", "unknown"), incident.get("severity", "P2"))
    repo.upsert_incident(incident["incident_id"], incident, channel)
    repo.add_timeline(incident["incident_id"], "incident_created", f"Incident created from {incident.get('source')}", {"alert_name": incident.get("alert_name")})
    repo.add_timeline(incident["incident_id"], "channel_created", f"War-room channel ready: {channel['channel_name']}", channel)
    event_bus.publish("incident.created", {"incident_id": incident["incident_id"], "service": incident.get("service"), "severity": incident.get("severity")})
    opening_message = ai_teammate.opening_update(incident, channel)
    try:
        posted = notifier.post_message(channel["channel_id"], opening_message, {"incident_id": incident["incident_id"]})
    except Exception as exc:
        posted = {"posted": False, "error": str(exc)}
        repo.add_timeline(incident["incident_id"], "notification_failed", "Opening war-room message failed", {"error": str(exc)})
    analysis = analyzer.analyze(incident)
    try:
        rag_answer = rag.answer(analysis["rag_query"], user=user or incident.get("user"))
    except Exception as exc:
        rag_answer = {"answer": "RAG retrieval failed; continue with deterministic investigation evidence.", "sources": [], "error": str(exc)}
        repo.add_timeline(incident["incident_id"], "rag_failed", "Runbook retrieval failed", {"error": str(exc)})
    investigation_message = ai_teammate.investigation_update(analysis, rag_answer)
    repo.add_timeline(incident["incident_id"], "ai_analysis", "AI teammate completed initial analysis", analysis)
    try:
        notifier.post_message(channel["channel_id"], investigation_message, {"incident_id": incident["incident_id"]})
    except Exception as exc:
        repo.add_timeline(incident["incident_id"], "notification_failed", "Investigation message failed", {"error": str(exc)})
    return {"incident_id": incident["incident_id"], "channel": channel, "opening_message_posted": posted, "analysis": analysis, "runbook_guidance": rag_answer, "timeline": repo.list_timeline(incident["incident_id"])}

@app.post("/incidents/{incident_id}/status")
def transition_incident(incident_id: str, req: StatusTransitionRequest, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    # Actor is always derived from the authenticated identity; request body actor is ignored to prevent audit spoofing.
    item = IncidentRepository(db).transition(incident_id, req.status, actor=_user.id or "unknown")
    return {"incident_id": incident_id, "status": item.status, "actor": _user.id}

@app.get("/incidents/{incident_id}/timeline")
def incident_timeline(incident_id: str, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    repo = IncidentRepository(db)
    incident = repo.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if not authz.can_view_incident(_user, incident.payload):
        raise HTTPException(status_code=403, detail="ReBAC denied access to this incident")
    return {"incident_id": incident_id, "timeline": repo.list_timeline(incident_id)}

@app.get("/incidents/{incident_id}/rca-draft")
def rca_draft(incident_id: str, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    repo = IncidentRepository(db)
    incident = repo.get(incident_id)
    payload = incident.payload if incident else {"incident_id": incident_id, "service": "unknown", "severity": "unknown", "environment": "unknown"}
    if incident and not authz.can_view_incident(_user, payload):
        raise HTTPException(status_code=403, detail="ReBAC denied access to this RCA")
    analysis = analyzer.analyze(payload)
    markdown = generate_rca_draft(payload, repo.list_timeline(incident_id), analysis)
    repo.save_rca(incident_id, markdown)
    return {"incident_id": incident_id, "rca_markdown": markdown}

@app.post("/collaboration/message")
def collaboration_message(req: CollaborationMessageRequest, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    try:
        IncidentRepository(db).add_timeline(req.incident_id, "manual_message", req.message, req.metadata)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return notifier.post_message(req.channel_id, req.message, req.metadata)

@app.post("/approvals")
def request_approval(req: ApprovalRequest, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    # Requester is authoritative from auth context, not caller-supplied body.
    return ApprovalService(db).request_approval(req.incident_id, req.action, _user.id or "unknown")

@app.post("/approvals/{approval_id}/decision")
def decide_approval(approval_id: int, req: ApprovalDecisionRequest, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    # Approver is authoritative from auth context, not caller-supplied body.
    svc = ApprovalService(db)
    try:
        if req.approved:
            target = svc.get_approval_target(approval_id)
            if not authz.can_approve_service_action(_user, target):
                raise HTTPException(status_code=403, detail=f"ReBAC denied: you cannot approve healing actions for '{target}'")
        decision = svc.decide(approval_id, req.approved, _user.id or "unknown", req.reason)
        execution = None
        if req.approved:
            queued = svc.queue_execution(approval_id)
            try:
                async_result = execute_approved_healing_action.delay(approval_id)
                execution = {**queued, "dispatched": True, "task_id": async_result.id}
            except Exception as exc:
                # Approval remains APPROVED and execution remains QUEUED.
                # A worker/operator can safely retry because executed=False and queue_execution is idempotent for queued actions.
                execution = {**queued, "dispatched": False, "error": str(exc)}
        return {**decision, "execution": execution}
    except HTTPException:
        raise
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/approvals/{approval_id}/execute")
def dispatch_approved_execution(approval_id: int, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    service = ApprovalService(db)
    try:
        target = service.get_approval_target(approval_id)
        if not authz.can_approve_service_action(_user, target):
            raise HTTPException(status_code=403, detail=f"ReBAC denied: you cannot execute healing actions for '{target}'")
        queued = service.queue_execution(approval_id)
        async_result = execute_approved_healing_action.delay(approval_id)
        return {**queued, "dispatched": True, "task_id": async_result.id, "requested_by": _user.id}
    except HTTPException:
        raise
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Celery broker unavailable. Approval is APPROVED and action is QUEUED — retry via this endpoint. Error: {exc}",
        ) from exc

@app.post("/heal")
def heal(req: HealRequest, db: Session = Depends(get_db), _user: UserContext = Depends(require_auth)):
    request_payload = req.model_dump()
    request_payload["user"] = _user.model_dump()
    if not authz.can_access_service(_user, req.target):
        raise HTTPException(status_code=403, detail="ReBAC denied healing action for this service")
    decision = policy.validate(request_payload)
    if not decision["allowed"]:
        return {"executed": False, "policy": decision, "message": "Action blocked by policy"}
    if decision.get("requires_approval") and not req.dry_run:
        approval = ApprovalService(db).request_approval("manual", request_payload, requested_by=_user.id or "unknown")
        return {"executed": False, "approval_required": True, "approval": approval, "policy": decision}
    if req.dry_run:
        return {"executed": False, "dry_run": True, "policy": decision, "planned_action": request_payload}

    # Safety invariant: every live mutation goes through the approval/executor
    # pipeline so Celery, AuditLog, idempotency guards, and rollback metadata are
    # always in the path. Auto-approved actions are approved by policy, but still
    # queued and executed by the same worker flow as human-approved actions.
    svc = ApprovalService(db)
    approval = svc.request_approval("manual", request_payload, requested_by=_user.id or "unknown")
    decision_record = svc.decide(approval["approval_id"], approved=True, approver="policy-auto-approver", reason="Policy allowed without human approval")
    queued = svc.queue_execution(approval["approval_id"])
    try:
        async_result = execute_approved_healing_action.delay(approval["approval_id"])
        execution = {**queued, "dispatched": True, "task_id": async_result.id}
    except Exception as exc:
        execution = {**queued, "dispatched": False, "error": str(exc)}
    return {"executed": False, "queued": True, "approval_required": False, "approval": decision_record, "policy": decision, "execution": execution}


# Phase 1-10 maturity routers
app.include_router(evals_router)
app.include_router(gitops_ai_router)

# AI-SRE maturity routers
app.include_router(ai_observability_router)
app.include_router(investigation_graph_router)
app.include_router(kubernetes_troubleshooter_router)
app.include_router(platform_agents_router)
app.include_router(self_service_platform_router)
app.include_router(secrets_platform_router)
app.include_router(domain_router)
app.include_router(k8s_issues_router)
app.include_router(eval_scorecard_router)
app.include_router(rag_types_router)
app.include_router(ai_runtime_router)
app.include_router(kubernetes_internals_router)
app.include_router(telemetry_router)
