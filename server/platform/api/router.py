from __future__ import annotations

from typing import Any, Dict

from server.platform.control_plane import ARIAPlatformControlPlane
from server.platform.reports.markdown import MarkdownServiceReviewReport
from server.platform.spec_engine import SpecDrivenEvaluator, SpecLoader

try:
    from fastapi import APIRouter
except Exception:  # pragma: no cover
    APIRouter = None  # type: ignore


control_plane = ARIAPlatformControlPlane()
reporter = MarkdownServiceReviewReport()
spec_evaluator = SpecDrivenEvaluator(SpecLoader())

if APIRouter:
    router = APIRouter(prefix="/aria/platform", tags=["ARIA AI Self-Service Platform"])

    @router.post("/onboard")
    def onboard_service(request: Dict[str, Any]) -> Dict[str, Any]:
        return control_plane.onboard_service(request)

    @router.post("/service-review")
    def review_service(request: Dict[str, Any]) -> Dict[str, Any]:
        return control_plane.review_service(request)

    @router.post("/terraform-drift")
    def terraform_drift(request: Dict[str, Any]) -> Dict[str, Any]:
        return control_plane.run_terraform_drift(request.get("terraform_plan", {}), request.get("environment", "dev"))

    @router.post("/service-review/markdown")
    def service_review_markdown(request: Dict[str, Any]) -> Dict[str, str]:
        review = control_plane.review_service(request)
        return {"markdown": reporter.render(review)}

    @router.post("/cicd/generate")
    def generate_cicd_pipeline(request: Dict[str, Any]) -> Dict[str, Any]:
        return control_plane.generate_cicd_pipeline(request)

    @router.post("/issues/analyze")
    def analyze_issue_event(request: Dict[str, Any]) -> Dict[str, Any]:
        return control_plane.handle_issue_event(request)

    @router.post("/secrets/lease")
    def issue_secret_lease(request: Dict[str, Any]) -> Dict[str, Any]:
        return control_plane.issue_secret_lease(request)

    @router.post("/secrets/review")
    def review_secret_governance(request: Dict[str, Any]) -> Dict[str, Any]:
        return control_plane.review_secret_governance(request)


    @router.post("/transactions/score")
    def score_transaction(request: Dict[str, Any]) -> Dict[str, Any]:
        return control_plane.score_transaction_event(request)

    @router.post("/specs/evaluate")
    def evaluate_service_specs(request: Dict[str, Any]) -> Dict[str, Any]:
        service_id = request.get("service_id", "payments-api")
        return spec_evaluator.evaluate_service(service_id).to_dict()
else:
    router = None
