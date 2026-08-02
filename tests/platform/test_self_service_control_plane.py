from server.platform.control_plane import ARIAPlatformControlPlane


def test_service_review_generates_report_and_patch_plan():
    cp = ARIAPlatformControlPlane()
    request = {
        "service_id": "payments-api",
        "environment": "prod",
        "service_profile": {
            "tier": "tier1",
            "kubernetes": {"readinessProbe": False, "livenessProbe": False, "pdb": False, "resources": {}},
            "observability": {"otel_enabled": True, "otel": {"service_name": "payments-api", "high_cardinality_attributes": ["user_id"]}},
            "cicd": {"sast": True, "container_scan": False, "rollback": False},
        },
        "slo_config": {"availability_target": 99.95, "latency_p95_target_ms": 300, "error_rate_target": 0.01},
        "telemetry_snapshot": {"availability": 99.9, "latency_p95_ms": 450, "error_rate": 0.02, "error_budget_remaining_percent": 4, "burn_rate": 5.0},
        "latest_drift_summary": {"status": "drift_detected", "severity": "P1"},
    }
    report = cp.generate_service_review_report(request)
    assert "markdown_report" in report
    assert "ARIA Service Review" in report["markdown_report"]
    assert report["review"]["agents_not_run"] == ["terraform-drift-agent"]

    pr_plan = cp.generate_remediation_pr_plan({"review": report["review"]})
    assert pr_plan["patch_plan"]["mode"] == "dry_run"
    assert pr_plan["approval_tickets"]


def test_snapshot_builder_normalizes_kubernetes_objects():
    cp = ARIAPlatformControlPlane()
    deployment = {
        "kind": "Deployment",
        "spec": {"template": {"spec": {"containers": [{"name": "api", "readinessProbe": {}, "resources": {}}]}}},
    }
    snapshot = cp.build_snapshot({"service_id": "checkout-api", "kubernetes_objects": [deployment]})
    assert snapshot["service_profile"]["kubernetes"]["workload_count"] == 1
    assert snapshot["source_status"]["kubernetes"] == "ok"


def test_terraform_drift_commands_are_dry_run_safe():
    cp = ARIAPlatformControlPlane()
    commands = cp.terraform_drift_commands("/tmp/service")
    assert commands["safety"]["apply_allowed"] is False
    assert any("plan" in cmd for command in commands["commands"] for cmd in command)
