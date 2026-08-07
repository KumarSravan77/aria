from server.recovery.auto_recovery import AutoRecoveryCoordinator, RecoveryObservation


def observation(failure_type: str, **overrides) -> RecoveryObservation:
    values = {
        "service": "checkout-api",
        "failure_type": failure_type,
        "environment": "production",
        "desired_replicas": 3,
        "ready_replicas": 1,
        "available_zones": 2,
        "traffic_healthy": False,
        "data_healthy": True,
        "alerts_resolved": False,
    }
    values.update(overrides)
    return RecoveryObservation(**values)


def test_pod_recovery_is_left_to_kubernetes_controller():
    result = AutoRecoveryCoordinator().coordinate(observation("pod_failure"))
    assert result["recovery_lane"] == "kubernetes-controller"
    assert result["approval_required"] is False
    assert result["execution"] == "not_started"


def test_regional_recovery_requires_approval():
    result = AutoRecoveryCoordinator().coordinate(observation("region_failure"))
    assert result["recovery_lane"] == "regional-failover"
    assert result["approval_required"] is True


def test_healthy_service_needs_no_recovery():
    result = AutoRecoveryCoordinator().coordinate(
        observation(
            "pod_failure",
            ready_replicas=3,
            traffic_healthy=True,
            alerts_resolved=True,
        )
    )
    assert result["state"] == "healthy"


def test_ready_replicas_in_one_zone_are_still_degraded():
    result = AutoRecoveryCoordinator().coordinate(
        observation(
            "pod_failure",
            ready_replicas=3,
            available_zones=1,
            traffic_healthy=True,
            alerts_resolved=True,
        )
    )
    assert result["recovery_lane"] == "zone-capacity-restoration"
