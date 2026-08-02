from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from server.platform.connectors.snapshot_builder import ServiceSnapshotBuilder
from server.platform.onboarding.agent import OnboardingAgent
from server.platform.service_review.agent import AIServiceReviewAgent
from server.platform.terraform_drift.agent import TerraformDriftAgent
from server.platform.reports import MarkdownServiceReviewReportGenerator
from server.platform.pr_engine import RemediationPatchGenerator
from server.platform.approvals import ApprovalWorkflow
from server.platform.cicd_pipeline import CICDPipelineGenerator
from server.platform.issue_response import AIIssueResponseAgent
from server.platform.secrets import SecretBroker, SecretGovernanceAgent
from server.platform.secrets.broker import SecretRequest
from server.platform.transaction_risk_scoring import score_transaction


class ARIAPlatformControlPlane:
    """Self-service entry point for ARIA platform workflows.

    This is the API-safe control plane used by self-service onboarding, service
    review, Terraform drift scans, approval ticket generation, report generation,
    and dry-run remediation patch generation.
    """

    def __init__(self) -> None:
        self.onboarding_agent = OnboardingAgent()
        self.service_review_agent = AIServiceReviewAgent()
        self.terraform_drift_agent = TerraformDriftAgent()
        self.snapshot_builder = ServiceSnapshotBuilder()
        self.report_generator = MarkdownServiceReviewReportGenerator()
        self.patch_generator = RemediationPatchGenerator()
        self.approvals = ApprovalWorkflow()
        self.cicd_generator = CICDPipelineGenerator()
        self.issue_response_agent = AIIssueResponseAgent()
        self.secret_governance_agent = SecretGovernanceAgent()
        self.secret_broker = SecretBroker()

    def build_snapshot(self, request: Dict[str, Any]) -> Dict[str, Any]:
        snapshot = self.snapshot_builder.build(
            service_id=request["service_id"],
            environment=request.get("environment", "dev"),
            service_profile=request.get("service_profile", {}),
            repo_path=request.get("repo_path"),
            kubernetes_objects=request.get("kubernetes_objects"),
            slo_config=request.get("slo_config"),
            telemetry_snapshot=request.get("telemetry_snapshot"),
            incident_history=request.get("incident_history"),
            latest_drift_summary=request.get("latest_drift_summary"),
        )
        return snapshot.to_dict()

    def _default_golden_path(self, service_profile: Dict[str, Any]) -> str:
        language = str(service_profile.get("language") or service_profile.get("runtime") or "").lower()
        tier = str(service_profile.get("tier") or "").lower()
        workload = str(service_profile.get("workload_type", "")).lower()
        framework = str(service_profile.get("framework", "")).lower()
        if "mlops" in workload or "data-pipeline" in workload or "feature" in workload:
            return "python-aml-mlops"
        if "python" in language or "ai" in workload:
            return "python-ai-service"
        if "java" in language or "spring" in framework or tier == "tier1":
            return "java-springboot-tier1"
        return "java-springboot-tier1"

    def ensure_service_profile(self, service_id: str, service_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Create/update a filesystem service profile used by the spec engine.

        This makes onboarding truly self-service: the platform no longer requires
        a human to pre-create specs/service-profiles/<service>.yaml before an app
        can be evaluated. Existing files are preserved unless overwrite_profile=True
        is supplied by the caller.
        """
        profile_dir = Path("specs/service-profiles")
        profile_dir.mkdir(parents=True, exist_ok=True)
        path = profile_dir / f"{service_id}.yaml"
        if path.exists() and not service_profile.get("overwrite_profile"):
            return {"created": False, "path": str(path), "profile": yaml.safe_load(path.read_text()) or {}}
        service_block = {
            "id": service_id,
            "name": service_profile.get("name", service_id),
            "owner_team": service_profile.get("owner_team") or service_profile.get("team") or "platform",
            "tier": service_profile.get("tier", "tier2"),
            "language": service_profile.get("language", "unknown"),
            "framework": service_profile.get("framework", "unknown"),
            "runtime": service_profile.get("runtime", service_profile.get("language", "unknown")),
            "golden_path": service_profile.get("golden_path") or self._default_golden_path(service_profile),
            "deployment_target": service_profile.get("deployment", {}).get("target") if isinstance(service_profile.get("deployment"), dict) else service_profile.get("deployment_target", "kubernetes"),
            "environment": service_profile.get("environment", "dev"),
        }
        if service_profile.get("compliance"):
            service_block["compliance"] = service_profile["compliance"]
        if service_profile.get("slo"):
            service_block["slo"] = service_profile["slo"]
        document = {"service": service_block}
        path.write_text(yaml.safe_dump(document, sort_keys=False))
        return {"created": True, "path": str(path), "profile": document}

    def onboard_service(self, request: Dict[str, Any]) -> Dict[str, Any]:
        profile_result = self.ensure_service_profile(request["service_id"], dict(request.get("service_profile", {}) or {}))
        snapshot = self.snapshot_builder.build(
            service_id=request["service_id"],
            environment=request.get("environment", "dev"),
            service_profile=request.get("service_profile", {}),
            repo_path=request.get("repo_path"),
            kubernetes_objects=request.get("kubernetes_objects"),
            slo_config=request.get("slo_config"),
            telemetry_snapshot=request.get("telemetry_snapshot"),
            incident_history=request.get("incident_history"),
        )
        onboarding = self.onboarding_agent.onboard(
            service_id=snapshot.service_id,
            environment=snapshot.environment,
            service_profile=snapshot.service_profile,
            slo_config=snapshot.slo_config,
            telemetry_snapshot=snapshot.telemetry_snapshot,
            terraform_plan=request.get("terraform_plan"),
        )
        onboarding["service_profile_spec"] = profile_result
        onboarding["secret_governance"] = self.secret_governance_agent.review(request)
        return onboarding

    def review_service(self, request: Dict[str, Any]) -> Dict[str, Any]:
        snapshot = self.snapshot_builder.build(
            service_id=request["service_id"],
            environment=request.get("environment", "prod"),
            service_profile=request.get("service_profile", {}),
            repo_path=request.get("repo_path"),
            kubernetes_objects=request.get("kubernetes_objects"),
            slo_config=request.get("slo_config"),
            telemetry_snapshot=request.get("telemetry_snapshot"),
            incident_history=request.get("incident_history"),
            latest_drift_summary=request.get("latest_drift_summary"),
        )
        review = self.service_review_agent.review(**snapshot.to_review_request()).to_dict()
        review["source_status"] = snapshot.source_status
        review["secret_governance"] = self.secret_governance_agent.review(request)
        return review

    def generate_service_review_report(self, request: Dict[str, Any]) -> Dict[str, Any]:
        review = self.review_service(request)
        markdown = self.report_generator.generate(review)
        return {"review": review, "markdown_report": markdown}

    def generate_remediation_pr_plan(self, request: Dict[str, Any]) -> Dict[str, Any]:
        review = request.get("review") or self.review_service(request)
        patches = self.patch_generator.generate(review)
        approvals = self.approvals.create_from_review(review)
        return {"review_summary": review.get("executive_summary"), "patch_plan": patches, "approval_tickets": approvals}

    def run_terraform_drift(self, terraform_plan: Dict[str, Any], environment: str) -> Dict[str, Any]:
        return self.terraform_drift_agent.analyze(terraform_plan, environment)

    def terraform_drift_commands(self, working_dir: str) -> Dict[str, Any]:
        return self.terraform_drift_agent.plan_commands(working_dir)

    def generate_cicd_pipeline(self, request: Dict[str, Any]) -> Dict[str, Any]:
        profile = dict(request.get("service_profile", {}) or {})
        profile.setdefault("service_id", request.get("service_id", profile.get("name", "unknown-service")))
        if request.get("language"):
            profile.setdefault("language", request["language"])
        if request.get("cicd_provider"):
            profile.setdefault("cicd", {})["provider"] = request["cicd_provider"]
        if request.get("deployment_target"):
            profile.setdefault("deployment", {})["target"] = request["deployment_target"]
        result = self.cicd_generator.generate(profile).to_dict()
        output_dir = request.get("output_dir")
        if request.get("write_files") and output_dir:
            written = []
            base = Path(output_dir)
            for relative_path, content in result.get("generated_files", {}).items():
                target = base / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
                written.append(str(target))
            result["written_files"] = written
        return result

    def handle_issue_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return self.issue_response_agent.analyze(event)


    def issue_secret_lease(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return self.secret_broker.request_secret_lease(SecretRequest(
            service_id=request.get("service_id", ""),
            environment=request.get("environment", ""),
            secret_ref=request.get("secret_ref", ""),
            purpose=request.get("purpose", "runtime"),
            requester=request.get("requester", "aria"),
        ))

    def review_secret_governance(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return self.secret_governance_agent.review(request)

    def score_transaction_event(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Score one transaction event using the deterministic AML demo scorer."""
        return score_transaction(transaction)
