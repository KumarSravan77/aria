from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from server.platform.service_review.reliability import ReliabilityAgent
from server.platform.spec_harness.models import Approval, Finding, Remediation, Score
from server.platform.kubernetes_standards.agent import KubernetesStandardsAgent
from server.platform.observability_standards.agent import ObservabilityStandardsAgent
from server.platform.otel_guardian.agent import OTelGuardianAgent
from server.platform.cicd_standards.agent import CICDStandardsAgent
from server.platform.security_governance.agent import SecurityGovernanceAgent
from server.platform.cost_optimization.agent import CostOptimizationAgent
from server.platform.runbook_quality.agent import RunbookQualityAgent
from server.platform.enterprise_event_bus.agent import EnterpriseEventBusAgent
from server.platform.transaction_risk_scoring.agent import TransactionRiskScoringAgent
from server.platform.devsecops.agent import DevSecOpsAgent


def _score_from_findings(name: str, findings: List[Finding]) -> Score:
    penalty = 0
    blockers: List[str] = []
    for finding in findings:
        if finding.severity == "P0":
            penalty += 35
            blockers.append(finding.id)
        elif finding.severity == "P1":
            penalty += 20
            blockers.append(finding.id)
        elif finding.severity == "P2":
            penalty += 10
        elif finding.severity == "P3":
            penalty += 5
    numeric = max(0, 100 - penalty)
    if numeric >= 90:
        grade = "A"
    elif numeric >= 75:
        grade = "B"
    elif numeric >= 60:
        grade = "C"
    elif numeric >= 45:
        grade = "D"
    else:
        grade = "F"
    return Score(name=name, grade=grade, numeric_score=numeric, rationale=f"{name} score from severity-weighted findings.", blockers=blockers)


@dataclass
class ServiceReviewReport:
    service_id: str
    environment: str
    executive_summary: str
    scores: Dict[str, Score]
    findings: List[Finding]
    remediation_backlog: List[Remediation]
    approval_required_actions: List[Approval]
    consumed_inputs: Dict[str, bool] = field(default_factory=dict)
    agents_run: List[str] = field(default_factory=list)
    agents_not_run: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_id": self.service_id,
            "environment": self.environment,
            "executive_summary": self.executive_summary,
            "scores": {k: v.to_dict() for k, v in self.scores.items()},
            "findings": [f.to_dict() for f in self.findings],
            "remediation_backlog": [r.to_dict() for r in self.remediation_backlog],
            "approval_required_actions": [a.to_dict() for a in self.approval_required_actions],
            "consumed_inputs": self.consumed_inputs,
            "agents_run": self.agents_run,
            "agents_not_run": self.agents_not_run,
        }


class AIServiceReviewAgent:
    """Main ARIA operational readiness review orchestrator.

    Important boundary:
    - It DOES run reliability, K8s, OTel/observability, CI/CD, security, cost, and runbook checks.
    - It DOES NOT run terraform drift directly.
    - It MAY consume the latest terraform drift summary if an independent drift scan already exists.
    """

    name = "ai-service-review-agent"

    def __init__(self) -> None:
        self.reliability_agent = ReliabilityAgent()
        self.kubernetes_agent = KubernetesStandardsAgent()
        self.observability_agent = ObservabilityStandardsAgent()
        self.otel_guardian_agent = OTelGuardianAgent()
        self.cicd_agent = CICDStandardsAgent()
        self.security_agent = SecurityGovernanceAgent()
        self.cost_agent = CostOptimizationAgent()
        self.runbook_agent = RunbookQualityAgent()
        self.enterprise_event_bus_agent = EnterpriseEventBusAgent()
        self.transaction_risk_scoring_agent = TransactionRiskScoringAgent()
        self.devsecops_agent = DevSecOpsAgent()

    def review(
        self,
        service_id: str,
        environment: str,
        service_profile: Dict[str, Any],
        slo_config: Optional[Dict[str, Any]] = None,
        telemetry_snapshot: Optional[Dict[str, Any]] = None,
        incident_history: Optional[List[Dict[str, Any]]] = None,
        latest_drift_summary: Optional[Dict[str, Any]] = None,
    ) -> ServiceReviewReport:
        findings: List[Finding] = []
        scores: Dict[str, Score] = {}
        agents_run = [
            "reliability-agent",
            "kubernetes-standards-agent",
            "observability-standards-agent",
            "otel-guardian-agent",
            "cicd-standards-agent",
            "security-governance-agent",
            "cost-optimization-agent",
            "runbook-quality-agent",
            "enterprise-event-bus-agent",
            "transaction-risk-scoring-agent",
            "devsecops-agent",
        ]
        agents_not_run = ["terraform-drift-agent"]

        if slo_config and telemetry_snapshot:
            reliability = self.reliability_agent.review(slo_config, telemetry_snapshot)
            findings.extend(reliability.findings)
            scores["reliability"] = reliability.score
        else:
            scores["reliability"] = Score(
                name="reliability",
                grade="C",
                numeric_score=65,
                rationale="Reliability data incomplete; provide SLO config and telemetry snapshot for full review.",
                blockers=["missing_slo_or_telemetry"],
            )

        # Specialist platform standards agents. These are deterministic now and can
        # later be backed by live Git, Kubernetes, CI/CD, and telemetry connectors.
        k8s_findings = self.kubernetes_agent.review(service_profile)
        findings.extend(k8s_findings)
        scores["kubernetes"] = _score_from_findings("kubernetes", k8s_findings)

        obs_findings = self.observability_agent.review(service_profile)
        otel_result = self.otel_guardian_agent.review(service_profile)
        obs_all_findings = obs_findings + otel_result["findings"]
        findings.extend(obs_all_findings)
        scores["observability"] = _score_from_findings("observability", obs_all_findings)
        scores["otel_guardian"] = otel_result["score"]

        cicd_findings = self.cicd_agent.review(service_profile)
        findings.extend(cicd_findings)
        scores["cicd"] = _score_from_findings("cicd", cicd_findings)

        security_findings = self.security_agent.review(service_profile)
        findings.extend(security_findings)
        scores["security"] = _score_from_findings("security", security_findings)

        cost_findings = self.cost_agent.review(service_profile)
        findings.extend(cost_findings)
        scores["cost"] = _score_from_findings("cost", cost_findings)

        runbook_findings = self.runbook_agent.review(service_profile)
        findings.extend(runbook_findings)
        scores["runbook"] = _score_from_findings("runbook", runbook_findings)

        eventing_findings = self.enterprise_event_bus_agent.review(service_profile)
        findings.extend(eventing_findings)
        scores["eventing"] = _score_from_findings("eventing", eventing_findings)

        risk_findings = self.transaction_risk_scoring_agent.review(service_profile)
        findings.extend(risk_findings)
        scores["risk_scoring"] = _score_from_findings("risk_scoring", risk_findings)

        devsecops_findings = self.devsecops_agent.review(service_profile)
        findings.extend(devsecops_findings)
        scores["devsecops"] = _score_from_findings("devsecops", devsecops_findings)

        # Drift result is consumed only if available.
        if latest_drift_summary and latest_drift_summary.get("status") == "drift_detected":
            findings.append(Finding(
                id="tf-drift-summary-risk",
                title="Terraform drift detected in latest independent scan",
                category="terraform",
                severity=latest_drift_summary.get("severity", "P2"),
                evidence=[],
                impact={
                    "user_impact": "Runtime behavior may differ from declared platform baseline.",
                    "business_impact": "Compliance and audit confidence may be reduced.",
                    "technical_impact": "Cloud state differs from Terraform desired state.",
                },
                recommendation={
                    "summary": "Review the independent Terraform Drift Agent report and approve remediation PR if safe.",
                    "remediation_type": "approval_required",
                },
                confidence={"score": 0.86, "explanation": "Consumed latest drift summary; service review did not execute drift scan."},
            ))

        scores["operational_readiness"] = _score_from_findings("operational_readiness", findings)

        approvals = [
            Approval(
                required=True,
                reason=finding.title,
                approver_role="service-owner",
                risk_level="high" if finding.severity in ("P0", "P1") else "medium",
            )
            for finding in findings
            if finding.recommendation.get("remediation_type") == "approval_required"
        ]

        remediations = [
            Remediation(
                id=f"remediate-{finding.id}",
                finding_id=finding.id,
                type="pull_request" if finding.recommendation.get("remediation_type") == "auto_fix_candidate" else "manual",
                safety={
                    "dry_run_required": True,
                    "approval_required": finding.severity in ("P0", "P1"),
                    "rollback_required": finding.category in ("kubernetes", "cicd", "terraform", "reliability"),
                },
                steps=[finding.recommendation.get("summary", "Review finding and remediate.")],
            )
            for finding in findings
        ]

        summary = (
            f"Operational readiness review completed for {service_id} in {environment}. "
            f"{len(findings)} findings identified; {len(approvals)} actions require approval."
        )

        return ServiceReviewReport(
            service_id=service_id,
            environment=environment,
            executive_summary=summary,
            scores=scores,
            findings=findings,
            remediation_backlog=remediations,
            approval_required_actions=approvals,
            consumed_inputs={
                "slo_config": slo_config is not None,
                "telemetry_snapshot": telemetry_snapshot is not None,
                "incident_history": incident_history is not None,
                "latest_drift_summary": latest_drift_summary is not None,
            },
            agents_run=agents_run,
            agents_not_run=agents_not_run,
        )

    def _review_kubernetes_profile(self, service_profile: Dict[str, Any]) -> List[Finding]:
        findings: List[Finding] = []
        k8s = service_profile.get("kubernetes", {})
        if not k8s.get("readinessProbe") or not k8s.get("livenessProbe"):
            findings.append(Finding(
                id="k8s-missing-probes",
                title="Kubernetes standards gap: missing liveness/readiness probes",
                category="kubernetes",
                severity="P1",
                evidence=[],
                impact={
                    "user_impact": "Traffic may be routed to unhealthy pods.",
                    "business_impact": "Availability and release safety may be reduced.",
                    "technical_impact": "Kubernetes cannot reliably detect startup or runtime health.",
                },
                recommendation={
                    "summary": "Add livenessProbe and readinessProbe to the workload template.",
                    "remediation_type": "auto_fix_candidate",
                },
                confidence={"score": 0.9, "explanation": "Probe fields missing from service profile."},
            ))
        if not k8s.get("pdb"):
            findings.append(Finding(
                id="k8s-missing-pdb",
                title="Kubernetes standards gap: missing PodDisruptionBudget",
                category="kubernetes",
                severity="P2",
                evidence=[],
                impact={
                    "user_impact": "Voluntary disruptions may reduce availability.",
                    "business_impact": "Maintenance windows may carry higher downtime risk.",
                    "technical_impact": "No disruption guard exists for replicas during node drains.",
                },
                recommendation={
                    "summary": "Add a PDB aligned to service tier and replica count.",
                    "remediation_type": "auto_fix_candidate",
                },
                confidence={"score": 0.82, "explanation": "PDB field missing from service profile."},
            ))
        return findings

    def _review_observability_profile(self, service_profile: Dict[str, Any]) -> List[Finding]:
        findings: List[Finding] = []
        obs = service_profile.get("observability", {})
        if not obs.get("otel_enabled"):
            findings.append(Finding(
                id="obs-otel-disabled",
                title="Observability standards gap: OpenTelemetry not enabled",
                category="observability",
                severity="P1",
                evidence=[],
                impact={
                    "user_impact": "Incidents may take longer to diagnose.",
                    "business_impact": "MTTR and auditability may be worse.",
                    "technical_impact": "Distributed traces and context propagation may be unavailable.",
                },
                recommendation={
                    "summary": "Enable OpenTelemetry instrumentation using the service language golden path.",
                    "remediation_type": "auto_fix_candidate",
                },
                confidence={"score": 0.87, "explanation": "otel_enabled is false or absent."},
            ))
        return findings

    def _review_cicd_profile(self, service_profile: Dict[str, Any]) -> List[Finding]:
        findings: List[Finding] = []
        cicd = service_profile.get("cicd", {})
        if not cicd.get("rollback"):
            findings.append(Finding(
                id="cicd-missing-rollback",
                title="CI/CD standards gap: rollback automation missing",
                category="cicd",
                severity="P1",
                evidence=[],
                impact={
                    "user_impact": "Bad releases may affect users for longer.",
                    "business_impact": "Recovery time and incident impact may increase.",
                    "technical_impact": "Pipeline cannot safely revert failed deployments.",
                },
                recommendation={
                    "summary": "Add rollback or automated deployment reversal to the pipeline template.",
                    "remediation_type": "auto_fix_candidate",
                },
                confidence={"score": 0.86, "explanation": "rollback is false or absent in CI/CD profile."},
            ))
        return findings
