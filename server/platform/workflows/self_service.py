from __future__ import annotations

from typing import Any, Dict, Optional

from server.platform.control_plane import ARIAPlatformControlPlane
from server.platform.reports.markdown import MarkdownServiceReviewReport


class SelfServiceDevOpsWorkflow:
    """End-to-end self-service workflow for onboarding + review + report + approvals."""

    def __init__(self) -> None:
        self.control_plane = ARIAPlatformControlPlane()
        self.reporter = MarkdownServiceReviewReport()

    def build_context(
        self,
        service_id: str,
        environment: str,
        service_profile: Dict[str, Any],
        telemetry_metrics: Optional[Dict[str, Any]] = None,
        pipeline: Optional[Dict[str, Any]] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        profile = dict(service_profile or {})
        if pipeline:
            stages = set(pipeline.get("stages", []))
            profile.setdefault("cicd", {}).update({
                "provider": pipeline.get("provider"),
                "sast": "sast" in stages or "sonar" in stages,
                "sbom": "sbom" in stages,
                "rollback": "rollback" in stages,
                "container_scan": "container_scan" in stages or "trivy" in stages,
            })
        telemetry = None
        if telemetry_metrics:
            telemetry = {
                "availability": telemetry_metrics.get("availability"),
                "latency_p95_ms": telemetry_metrics.get("latency_p95_ms"),
                "error_rate": telemetry_metrics.get("error_rate", telemetry_metrics.get("error_rate_percent", 0) / 100),
                "error_budget_remaining_percent": telemetry_metrics.get("error_budget_remaining_percent"),
                "burn_rate": telemetry_metrics.get("burn_rate"),
            }
        return {
            "service_id": service_id,
            "environment": environment,
            "service_profile": profile,
            "telemetry_snapshot": telemetry,
            "slo_config": extra.get("slo_config", {"availability_target": 99.9, "latency_p95_target_ms": 500, "error_rate_target": 0.01}),
            **extra,
        }

    def onboard_and_review(self, context: Dict[str, Any], output_dir: Optional[str] = None) -> Dict[str, Any]:
        onboarding = self.control_plane.onboard_service(context)
        review = self.control_plane.review_service(context)
        markdown = self.reporter.render(review)
        written_report = self.reporter.write(review, output_dir) if output_dir else None
        approvals = self.control_plane.generate_remediation_pr_plan({"review": review}).get("approval_tickets", [])
        return {
            "onboarding": onboarding,
            "service_review": review,
            "markdown_report": markdown,
            "written_report": written_report,
            "approval_requests": approvals,
        }
