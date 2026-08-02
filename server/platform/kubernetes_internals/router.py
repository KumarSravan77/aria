from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel

try:
    from server.api.security import require_auth
except Exception:
    def require_auth():
        return {"id": "local"}

from server.platform.kubernetes_internals.etcd_backup import EtcdBackupInspector
from server.platform.kubernetes_internals.control_plane_health import ControlPlaneHealthInspector
from server.platform.kubernetes_internals.admission_health import AdmissionWebhookInspector
from server.platform.kubernetes_internals.coredns_health import CoreDnsHealthInspector
from server.platform.kubernetes_internals.cni_health import CniHealthInspector
from server.platform.kubernetes_internals.cluster_restore_validator import ClusterRestoreValidator
from server.platform.kubernetes_internals.upgrade_readiness import UpgradeReadinessInspector

router = APIRouter(prefix="/kubernetes-internals", tags=["kubernetes-internals"])

class RestoreValidationRequest(BaseModel):
    backup_id: str | None = None
    sandbox: str = "non-prod-restore-sandbox"

@router.get("/control-plane/health")
def control_plane_health(_user=Depends(require_auth)):
    return ControlPlaneHealthInspector().inspect()

@router.get("/etcd/backups")
def etcd_backups(_user=Depends(require_auth)):
    return EtcdBackupInspector().inspect_backups()

@router.get("/etcd/recovery-plan")
def etcd_recovery_plan(_user=Depends(require_auth)):
    return EtcdBackupInspector().recovery_plan()

@router.post("/etcd/validate-restore")
def validate_restore(req: RestoreValidationRequest, _user=Depends(require_auth)):
    return ClusterRestoreValidator().validate_restore_plan(req.backup_id, req.sandbox)

@router.get("/admission/health")
def admission_health(_user=Depends(require_auth)):
    return AdmissionWebhookInspector().inspect()

@router.get("/dns/health")
def dns_health(_user=Depends(require_auth)):
    return CoreDnsHealthInspector().inspect()

@router.get("/cni/health")
def cni_health(_user=Depends(require_auth)):
    return CniHealthInspector().inspect()

@router.get("/upgrade/readiness")
def upgrade_readiness(_user=Depends(require_auth)):
    return UpgradeReadinessInspector().inspect()

@router.get("/summary")
def summary(_user=Depends(require_auth)):
    return {
        "control_plane": ControlPlaneHealthInspector().inspect(),
        "etcd": EtcdBackupInspector().inspect_backups(),
        "admission": AdmissionWebhookInspector().inspect(),
        "dns": CoreDnsHealthInspector().inspect(),
        "cni": CniHealthInspector().inspect(),
        "upgrade": UpgradeReadinessInspector().inspect(),
        "safety_boundary": "Kubernetes internals diagnostics are read-only; destructive restore/repair remains manual-only.",
    }
