from __future__ import annotations

from typing import Any, Dict, Optional

from server.platform.service_review.agent import AIServiceReviewAgent
from server.platform.terraform_drift.agent import TerraformDriftAgent
from server.platform.onboarding.templates import PlatformTemplateGenerator


class OnboardingAgent:
    """Self-service platform onboarding orchestrator.

    It is allowed to run Terraform Drift Agent to create a baseline and then
    run a service review using the baseline summary.
    """

    name = "onboarding-agent"

    def __init__(self) -> None:
        self.service_review = AIServiceReviewAgent()
        self.drift_agent = TerraformDriftAgent()
        self.template_generator = PlatformTemplateGenerator()

    def onboard(
        self,
        service_id: str,
        environment: str,
        service_profile: Dict[str, Any],
        slo_config: Optional[Dict[str, Any]] = None,
        telemetry_snapshot: Optional[Dict[str, Any]] = None,
        terraform_plan: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        drift_summary = self.drift_agent.analyze(terraform_plan or {"resource_changes": []}, environment)
        review = self.service_review.review(
            service_id=service_id,
            environment=environment,
            service_profile=service_profile,
            slo_config=slo_config,
            telemetry_snapshot=telemetry_snapshot,
            latest_drift_summary=drift_summary,
        )
        generated_artifacts = self.template_generator.generate(service_id, service_profile)
        return {
            "service_id": service_id,
            "environment": environment,
            "onboarding_status": "blocked" if review.approval_required_actions else "ready_with_conditions",
            "baseline": {
                "terraform_drift": drift_summary,
                "service_review": review.to_dict(),
            },
            "generated_platform_templates": list(generated_artifacts.keys()),
            "generated_artifacts": generated_artifacts,
        }
