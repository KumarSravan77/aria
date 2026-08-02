from __future__ import annotations

from typing import Any, Dict, List, Optional

from server.platform.issue_response.models import IssueResponsePlan, PlatformIssueEvent
from server.platform.service_review.agent import AIServiceReviewAgent


class AIIssueResponseAgent:
    """Event-driven AI agent for pipeline, deploy, alert, and SLO issues.

    This agent is the runtime responder for the self-service platform. It does
    not mutate infrastructure directly. It classifies the event, runs relevant
    specialist agents, produces triage steps, and marks whether approval or
    rollback is required.
    """

    name = "ai-issue-response-agent"

    def __init__(self) -> None:
        self.service_review_agent = AIServiceReviewAgent()

    def analyze(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        event = PlatformIssueEvent.from_dict(payload)
        context = payload.get("context", {}) or {}
        agents = self._select_agents(event)
        triage_steps = self._triage_steps(event)
        recommended_actions = self._recommended_actions(event)
        rollback_recommended = self._rollback_recommended(event)
        approval_required = event.severity in {"P0", "P1"} or rollback_recommended
        service_review = None

        # For high-severity service events, run a focused operational readiness
        # review using the supplied context. This lets alert/deployment events
        # reuse the same SLO, K8s, OTel, CI/CD, security, and runbook checks.
        if event.event_type in {"slo_burn", "deployment_failure", "runtime_alert", "pipeline_failure"}:
            service_review = self.service_review_agent.review(
                service_id=event.service_id,
                environment=event.environment,
                service_profile=context.get("service_profile", {"service_id": event.service_id}),
                slo_config=context.get("slo_config"),
                telemetry_snapshot=context.get("telemetry_snapshot"),
                incident_history=context.get("incident_history"),
                latest_drift_summary=context.get("latest_drift_summary"),
            ).to_dict()

        return IssueResponsePlan(
            service_id=event.service_id,
            environment=event.environment,
            event_type=event.event_type,
            severity=event.severity,
            incident_mode=self._incident_mode(event),
            agents_to_run=agents,
            triage_steps=triage_steps,
            recommended_actions=recommended_actions,
            approval_required=approval_required,
            rollback_recommended=rollback_recommended,
            service_review=service_review,
        ).to_dict()

    def _select_agents(self, event: PlatformIssueEvent) -> List[str]:
        base = ["rca-agent", "runbook-quality-agent", "remediation-ranker-agent"]
        mapping = {
            "pipeline_failure": ["cicd-standards-agent", "security-governance-agent", "otel-guardian-agent"],
            "deployment_failure": ["kubernetes-standards-agent", "cicd-standards-agent", "reliability-agent"],
            "slo_burn": ["reliability-agent", "metrics-agent", "trace-agent", "logs-agent", "kubernetes-standards-agent"],
            "runtime_alert": ["metrics-agent", "logs-agent", "trace-agent", "kubernetes-troubleshooter-agent"],
            "security_alert": ["security-governance-agent", "falco-agent", "rbac-advisory-agent"],
            "terraform_drift": ["terraform-drift-agent", "security-governance-agent", "cost-optimization-agent"],
        }
        return base + mapping.get(event.event_type, ["ai-service-review-agent"])

    def _incident_mode(self, event: PlatformIssueEvent) -> str:
        if event.severity == "P0":
            return "major_incident"
        if event.event_type in {"slo_burn", "runtime_alert"} and event.severity == "P1":
            return "active_incident"
        if event.event_type in {"pipeline_failure", "deployment_failure"}:
            return "release_guard"
        return "advisory"

    def _triage_steps(self, event: PlatformIssueEvent) -> List[str]:
        common = [
            "Create or update the incident timeline with event source, service, environment, and correlation id.",
            "Collect recent deployments, alerts, logs, traces, metrics, and Kubernetes events for the affected service.",
            "Check service ownership, tier, SLO target, and rollback path before recommending any mutation.",
        ]
        if event.event_type == "pipeline_failure":
            return common + [
                "Identify failed pipeline stage and compare it against ARIA golden-path CI/CD standards.",
                "Check whether the failure blocks production promotion or only requires advisory remediation.",
            ]
        if event.event_type == "deployment_failure":
            return common + [
                "Check rollout status, pod events, image pull errors, probes, and deployment strategy.",
                "If users are impacted or SLO is burning, recommend rollback with approval gate.",
            ]
        if event.event_type == "slo_burn":
            return common + [
                "Calculate burn-rate severity and projected error-budget exhaustion.",
                "Correlate latency/error spikes with deployment, Kubernetes, Kafka, DNS, and Istio signals.",
            ]
        return common + ["Run focused RCA and rank safe remediation options."]

    def _recommended_actions(self, event: PlatformIssueEvent) -> List[Dict[str, Any]]:
        actions: List[Dict[str, Any]] = []
        if event.event_type == "pipeline_failure":
            actions.append({"type": "block_promotion", "summary": "Keep production promotion blocked until failed gate is fixed.", "safety": "no_mutation"})
            actions.append({"type": "create_pr", "summary": "Generate PR patch for missing/failed CI/CD standard if deterministic.", "safety": "dry_run"})
        elif event.event_type == "deployment_failure":
            actions.append({"type": "rollback_candidate", "summary": "Prepare rollback plan and require service-owner approval for production.", "safety": "approval_required"})
            actions.append({"type": "k8s_diagnostics", "summary": "Inspect rollout status, pod health, probes, HPA, PDB, and events.", "safety": "read_only"})
        elif event.event_type == "slo_burn":
            actions.append({"type": "incident_page", "summary": "Page service owner if fast burn or error budget exhaustion risk is high.", "safety": "notification"})
            actions.append({"type": "mitigation_plan", "summary": "Rank rollback, scale-out, traffic shift, or dependency mitigation based on evidence.", "safety": "approval_required"})
        elif event.event_type == "terraform_drift":
            actions.append({"type": "drift_review", "summary": "Review independent drift report before any remediation apply.", "safety": "approval_required"})
        else:
            actions.append({"type": "investigate", "summary": "Run RCA and generate a ranked remediation plan.", "safety": "read_only"})
        return actions

    def _rollback_recommended(self, event: PlatformIssueEvent) -> bool:
        signals = event.signals or {}
        return bool(
            event.event_type == "deployment_failure"
            or signals.get("rollback_signal")
            or signals.get("post_deploy_slo_burn")
            or signals.get("error_budget_remaining_percent", 100) < 5
        )
