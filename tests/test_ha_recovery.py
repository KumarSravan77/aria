from server.recovery.recovery_planner import RecoveryPlanner
from server.recovery.rto_rpo_tracker import RtoRpoTracker
from server.recovery.recovery_validator import RecoveryValidator
from server.platform.ha_recovery.pdb import generate_pdb
from server.platform.ha_recovery.topology_spread import generate_topology_spread
from server.platform.ha_recovery.velero import backup_schedule, restore_plan
from server.platform.ha_recovery.postgres_dr import streaming_replication_config, point_in_time_recovery
from server.platform.ha_recovery.gitops_recovery import cluster_bootstrap_plan, namespace_restore_plan
from server.platform.ha_recovery.istio_failover import traffic_failover_manifest
from server.platform.ha_recovery.regional_dr import regional_dr_plan, dr_readiness_checklist


def test_recovery_planner_returns_node_failure_steps():
    plan = RecoveryPlanner().plan("checkout-api", failure_type="node_failure")
    assert plan["service"] == "checkout-api"
    assert "node" in plan["strategy"]
    assert any("Karpenter" in step or "Cluster Autoscaler" in step for step in plan["recommended_steps"])
    assert "ReBAC" in plan["safety_boundary"]

def test_recovery_planner_covers_all_failure_types():
    for ft in ["pod", "node", "db", "cluster_failure", "regional-dr", "unknown"]:
        plan = RecoveryPlanner().plan("svc", failure_type=ft)
        assert len(plan["recommended_steps"]) >= 4
        assert "safety_boundary" in plan

def test_rto_rpo_tracker_pass_and_fail():
    ok = RtoRpoTracker().evaluate("checkout-api", 30, 15, 12, 2)
    assert ok["status"] == "PASS"
    assert ok["rto"]["met"] is True
    bad = RtoRpoTracker().evaluate("checkout-api", 30, 15, 45, 20)
    assert bad["status"] == "FAIL"
    assert bad["rto"]["variance_minutes"] == 15

def test_recovery_validator_scores_controls():
    result = RecoveryValidator().validate("checkout-api", replicas_ready=True, traffic_restored=False)
    assert result["score"] < 100
    assert result["status"] in {"DEGRADED", "FAIL"}

def test_recovery_validator_full_pass():
    assert RecoveryValidator().validate("checkout-api")["score"] == 100

def test_pdb_min_available():
    m = generate_pdb("checkout-api", min_available=1)
    assert m["kind"] == "PodDisruptionBudget"
    assert m["spec"]["minAvailable"] == 1
    assert "maxUnavailable" not in m["spec"]

def test_pdb_max_unavailable():
    m = generate_pdb("checkout-api", max_unavailable="25%")
    assert m["spec"]["maxUnavailable"] == "25%"

def test_topology_spread_has_zone_and_node_constraints():
    m = generate_topology_spread("checkout-api", replicas=3)
    keys = [c["topologyKey"] for c in m["spec"]["template"]["spec"]["topologySpreadConstraints"]]
    assert "topology.kubernetes.io/zone" in keys
    assert "kubernetes.io/hostname" in keys

def test_velero_backup_schedule():
    m = backup_schedule(namespace="demo")
    assert m["kind"] == "Schedule"
    assert m["spec"]["schedule"] == "0 2 * * *"

def test_velero_restore_requires_backup_name():
    assert restore_plan(backup_name="")["available"] is False

def test_velero_restore_has_safety_boundary():
    m = restore_plan(namespace="demo", backup_name="backup-001")
    assert m["kind"] == "Restore"
    assert "approval" in m["safety_boundary"].lower()

def test_postgres_replication_has_failover_steps():
    cfg = streaming_replication_config(replica_count=2)
    assert cfg["strategy"] == "streaming-replication"
    assert len(cfg["failover_steps"]) >= 4
    assert "safety_boundary" in cfg

def test_pitr_includes_target_time():
    plan = point_in_time_recovery(target_time="2026-05-16T10:00:00Z")
    assert "2026-05-16T10:00:00Z" in plan["recovery_steps"][1]

def test_cluster_bootstrap_has_argocd_step():
    plan = cluster_bootstrap_plan("incident-lab", git_repo="https://github.com/aria/gitops")
    assert any("Argo CD" in step for step in plan["steps"])
    assert "safety_boundary" in plan

def test_namespace_restore_has_velero_and_argocd():
    plan = namespace_restore_plan("demo", backup_name="demo-backup-001")
    assert any("velero restore" in s.lower() for s in plan["steps"])
    assert any("argocd app sync" in s.lower() for s in plan["steps"])

def test_istio_failover_manifests():
    result = traffic_failover_manifest("checkout-api", "us-east-1", "eu-west-1")
    assert result["virtual_service"]["kind"] == "VirtualService"
    assert result["destination_rule"]["kind"] == "DestinationRule"
    assert len(result["failover_steps"]) >= 3
    assert "approval" in result["safety_boundary"].lower()

def test_regional_dr_plan_covers_all_phases():
    plan = regional_dr_plan("checkout-api")
    assert all(k in plan["phases"] for k in ("detect", "data_recovery", "traffic_failover",
                                               "application_recovery", "validation"))

def test_dr_readiness_checklist_has_10_items():
    checklist = dr_readiness_checklist("checkout-api")
    assert len(checklist["checklist"]) == 10
    categories = {item["category"] for item in checklist["checklist"]}
    assert {"availability", "data", "people"}.issubset(categories)

def test_regional_dr_rto_rpo_objectives_present():
    plan = regional_dr_plan("checkout-api", rto_minutes=15, rpo_minutes=5)
    assert plan["objectives"]["rto_minutes"] == 15
    assert plan["objectives"]["rpo_minutes"] == 5

def test_topology_spread_has_anti_affinity():
    m = generate_topology_spread("checkout-api")
    affinity = m["spec"]["template"]["spec"].get("affinity", {})
    assert "podAntiAffinity" in affinity
