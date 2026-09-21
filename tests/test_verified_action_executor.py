from server.executors.action_executor import ActionExecutor


class FakeKubernetes:
    def __init__(self, states):
        self.states = iter(states)
        self.scales = []

    def deployment_state(self, namespace, target):
        return next(self.states)

    def execute(self, action, namespace, target, replicas=None):
        return {"status": "ok", "action": action, "replicas": replicas}

    def scale_deployment(self, namespace, target, replicas):
        self.scales.append(replicas)
        return {"status": "ok", "replicas": replicas}


class FakeArgo:
    pass


def test_verified_action_succeeds_when_workload_recovers():
    k8s = FakeKubernetes([
        {"available": True, "healthy": True, "desired_replicas": 2},
        {"available": True, "healthy": True, "desired_replicas": 4, "ready_replicas": 4},
    ])
    result = ActionExecutor(k8s, FakeArgo(), 1, 0).execute("scale_deployment", "demo", "api", replicas=4)
    assert result["status"] == "ok"
    assert result["verification"]["healthy"] is True


def test_failed_scale_is_automatically_rolled_back_when_declared():
    k8s = FakeKubernetes([
        {"available": True, "healthy": True, "desired_replicas": 2},
        {"available": True, "healthy": False, "desired_replicas": 4, "ready_replicas": 1},
        {"available": True, "healthy": True, "desired_replicas": 2, "ready_replicas": 2},
    ])
    result = ActionExecutor(k8s, FakeArgo(), 1, 0).execute(
        "scale_deployment", "demo", "api", replicas=4, rollback="restore previous replica count")
    assert result["status"] == "rolled_back"
    assert result["rollback_verification"]["healthy"] is True
    assert k8s.scales == [2]


def test_failed_restart_escalates_when_no_safe_inverse_exists():
    k8s = FakeKubernetes([
        {"available": True, "healthy": True, "desired_replicas": 2},
        {"available": True, "healthy": False, "desired_replicas": 2, "ready_replicas": 0},
    ])
    result = ActionExecutor(k8s, FakeArgo(), 1, 0).execute("restart_deployment", "demo", "api")
    assert result["status"] == "verification_failed"
    assert result["requires_escalation"] is True
