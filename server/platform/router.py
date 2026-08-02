from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from server.api.security import require_auth
from server.authz.authorization_service import AuthorizationService
from server.models.schemas import UserContext
from server.platform.control_plane import ARIAPlatformControlPlane
from server.platform.spec_engine import SpecDrivenEvaluator, SpecLoader

router = APIRouter(prefix="/platform/self-service", tags=["ai-self-service-platform"])
control_plane = ARIAPlatformControlPlane()
spec_evaluator = SpecDrivenEvaluator(SpecLoader())
authz = AuthorizationService()


def _service_id_from(payload: dict) -> str | None:
    profile = payload.get("service_profile") if isinstance(payload, dict) else {}
    return (payload.get("service_id") or (profile or {}).get("service_id") or (profile or {}).get("name"))


def _require_service_access(payload: dict, user: UserContext) -> None:
    service_id = _service_id_from(payload)
    if service_id and not authz.can_access_service(user, service_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized for service: {service_id}")


def _require_platform_operator(user: UserContext) -> None:
    if user.role not in {"admin", "sre", "incident-commander"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform self-service operation requires operator privileges")


@router.post("/snapshot")
def build_snapshot(payload: dict, user: UserContext = Depends(require_auth)):
    _require_service_access(payload, user)
    return control_plane.build_snapshot(payload)


@router.post("/onboard")
def onboard_service(payload: dict, user: UserContext = Depends(require_auth)):
    # New service onboarding is allowed for platform operators. Existing services still honor ReBAC.
    service_id = _service_id_from(payload)
    if service_id and authz.can_access_service(user, service_id):
        return control_plane.onboard_service(payload)
    _require_platform_operator(user)
    return control_plane.onboard_service(payload)


@router.post("/service-review")
def service_review(payload: dict, user: UserContext = Depends(require_auth)):
    _require_service_access(payload, user)
    return control_plane.review_service(payload)


@router.post("/service-review/report")
def service_review_report(payload: dict, user: UserContext = Depends(require_auth)):
    _require_service_access(payload, user)
    return control_plane.generate_service_review_report(payload)


@router.post("/remediation/pr-plan")
def remediation_pr_plan(payload: dict, user: UserContext = Depends(require_auth)):
    _require_service_access(payload, user)
    return control_plane.generate_remediation_pr_plan(payload)


@router.post("/terraform-drift/analyze")
def terraform_drift(payload: dict, user: UserContext = Depends(require_auth)):
    _require_service_access(payload, user)
    return control_plane.run_terraform_drift(payload.get("terraform_plan", {"resource_changes": []}), payload.get("environment", "dev"))


@router.post("/terraform-drift/commands")
def terraform_drift_commands(payload: dict, user: UserContext = Depends(require_auth)):
    _require_platform_operator(user)
    return control_plane.terraform_drift_commands(payload.get("working_dir", "."))


@router.post("/specs/evaluate")
def evaluate_service_specs(payload: dict, user: UserContext = Depends(require_auth)):
    service_id = payload.get("service_id")
    if not service_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="service_id is required")
    _require_service_access(payload, user)
    profile_result = control_plane.ensure_service_profile(
        service_id, dict(payload.get("service_profile") or {})
    )
    result = spec_evaluator.evaluate_service(service_id).to_dict()
    result["profile_created"] = profile_result["created"]
    return result


@router.post("/secrets/lease")
def issue_secret_lease(payload: dict, user: UserContext = Depends(require_auth)):
    _require_service_access(payload, user)
    return control_plane.issue_secret_lease(payload)


@router.post("/secrets/review")
def review_secret_governance(payload: dict, user: UserContext = Depends(require_auth)):
    _require_service_access(payload, user)
    return control_plane.review_secret_governance(payload)


@router.post("/cicd/generate")
def generate_cicd_pipeline(payload: dict, user: UserContext = Depends(require_auth)):
    _require_service_access(payload, user)
    return control_plane.generate_cicd_pipeline(payload)


@router.post("/issue-event")
def handle_issue_event(payload: dict, user: UserContext = Depends(require_auth)):
    _require_service_access(payload, user)
    return control_plane.handle_issue_event(payload)
