from server.platform.kubernetes_internals.etcd_backup import EtcdBackupInspector
from server.platform.kubernetes_internals.cluster_restore_validator import ClusterRestoreValidator
from server.platform.kubernetes_internals.control_plane_health import ControlPlaneHealthInspector
from server.platform.kubernetes_internals.admission_health import AdmissionWebhookInspector
from server.platform.kubernetes_internals.coredns_health import CoreDnsHealthInspector
from server.platform.kubernetes_internals.cni_health import CniHealthInspector
from server.platform.kubernetes_internals.upgrade_readiness import UpgradeReadinessInspector

def test_etcd_backup_degrades_safely():
    result = EtcdBackupInspector().inspect_backups()
    assert "safety_boundary" in result
    assert result["backup_fresh"] is False

def test_etcd_recovery_plan_manual_only():
    result = EtcdBackupInspector().recovery_plan()
    assert result["manual_only"] is True
    assert result["approval_required"] is True

def test_restore_validator_plan_only():
    result = ClusterRestoreValidator().validate_restore_plan("latest")
    assert result["mode"] == "plan_only"
    assert result["manual_only"] is True

def test_control_plane_returns_checks():
    assert "checks" in ControlPlaneHealthInspector().inspect()

def test_admission_returns_available_key():
    assert "available" in AdmissionWebhookInspector().inspect()

def test_coredns_returns_checks():
    assert "checks" in CoreDnsHealthInspector().inspect()

def test_cni_returns_checks():
    assert "checks" in CniHealthInspector().inspect()

def test_upgrade_readiness_returns_checks():
    assert "checks" in UpgradeReadinessInspector().inspect()
