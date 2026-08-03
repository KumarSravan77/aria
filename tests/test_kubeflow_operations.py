from pathlib import Path

import yaml

from server.kubeflow.agent import KubeflowOperationsAgent
from server.kubeflow.client import KubeflowEvidenceClient


ROOT = Path(__file__).resolve().parents[1]


class FakeCustomObjectsApi:
    def get_namespaced_custom_object(self, group, version, namespace, plural, name):
        assert (group, version, plural) == ("trainer.kubeflow.org", "v1alpha1", "trainjobs")
        return {
            "metadata": {
                "name": name,
                "namespace": namespace,
                "uid": "uid-123",
                "generation": 7,
                "labels": {"team": "ml-platform"},
                "ownerReferences": [],
            },
            "spec": {
                "runtimeRef": {"name": "torch-distributed"},
                "env": [{"name": "TOKEN", "value": "must-not-escape"}],
            },
            "status": {
                "conditions": [
                    {
                        "type": "Running",
                        "status": "False",
                        "reason": "Unschedulable",
                        "message": "insufficient nvidia.com/gpu",
                    }
                ]
            },
        }


def test_client_reads_supported_trainjob_and_redacts_detailed_spec():
    result = KubeflowEvidenceClient(FakeCustomObjectsApi()).get(
        "TrainJob", "fraud-model-training", "ml-platform"
    )
    assert result["available"] is True
    assert result["api_version"] == "trainer.kubeflow.org/v1alpha1"
    assert result["resource"]["spec_summary"]["runtimeRef"]["name"] == "torch-distributed"
    assert "env" not in result["resource"]["spec_summary"]
    assert "must-not-escape" not in str(result)


def test_agent_classifies_gpu_scheduling_and_builds_headlamp_evidence():
    agent = KubeflowOperationsAgent(
        client=KubeflowEvidenceClient(FakeCustomObjectsApi()),
        headlamp_base_url="https://headlamp.example",
    )
    result = agent.run(
        {
            "resource_kind": "TrainJob",
            "resource_name": "fraud-model-training",
            "namespace": "ml-platform",
            "signals": ["Unschedulable: insufficient nvidia.com/gpu"],
        }
    )
    assert result.available is True
    assert "GPUScheduling" in result.summary
    assert result.evidence[2]["url"].startswith("https://headlamp.example/")
    assert all("delete" not in item.lower() for item in result.recommendations)


def test_agent_fails_closed_for_unsupported_resource():
    result = KubeflowOperationsAgent(client=KubeflowEvidenceClient(FakeCustomObjectsApi())).run(
        {"resource_kind": "Secret", "resource_name": "credentials", "namespace": "default"}
    )
    assert result.available is False
    assert result.error == "unsupported Kubeflow resource kind: Secret"


def test_kubeflow_scenario_runbook_and_read_only_rbac_contract():
    runbook = (ROOT / "docs/runbooks/kubeflow-training-workload-failure.md").read_text()
    for required in (
        "id: RB-ML-001",
        "service: ml-platform",
        "team: ml-platform",
        "doc_type: runbook",
        "## Evidence collection",
        "## Recovery validation",
        "## Evidence and audit record",
    ):
        assert required in runbook
    scenario = yaml.safe_load((ROOT / "specs/golden-scenarios/kubeflow-training-failure.yaml").read_text())
    assert scenario["expected"]["failure_mode"] == "GPUScheduling"
    assert scenario["safety"]["read_only"] is True
    documents = list(yaml.safe_load_all((ROOT / "platform/kubeflow/aria-reader-rbac.yaml").read_text()))
    role = next(item for item in documents if item["kind"] == "ClusterRole")
    assert all(set(rule["verbs"]) <= {"get", "list", "watch"} for rule in role["rules"])
    assert all("secrets" not in rule["resources"] for rule in role["rules"])


def test_api_router_is_wired():
    from server.api.main import app

    paths = {route.path for route in app.routes}
    assert "/kubeflow/resources" in paths
    assert "/kubeflow/investigate" in paths

