from pathlib import Path
import yaml

from server.platform.ai_factory.planner import AiFactoryPlanner

ROOT = Path(__file__).resolve().parents[1]


def test_untrusted_tenant_gets_whole_gpu_boundary():
    result = AiFactoryPlanner().plan({"tenant": "external-research", "workload_type": "inference",
                                      "trust_level": "untrusted", "gpu_count": 1})
    assert result["decision"]["allocation"] == "whole-gpu"
    assert result["decision"]["tenant_boundary"] == "dedicated-node-pool"
    assert result["safety"]["automatic_node_drain"] is False


def test_internal_small_workload_can_use_partitioning():
    result = AiFactoryPlanner().plan({"tenant": "media-ai", "workload_type": "fine-tuning",
                                      "trust_level": "internal", "gpu_memory_gib": 10})
    assert result["decision"]["allocation"] == "mig"
    assert "queue_admission" in result["required_evidence"]


def test_capacity_excludes_unhealthy_gpu_nodes():
    result = AiFactoryPlanner().capacity_summary([
        {"name": "gpu-a", "gpu_count": 4, "allocated_gpus": 3, "healthy": True},
        {"name": "gpu-b", "gpu_count": 4, "allocated_gpus": 0, "healthy": False},
    ])
    assert result["gpu_available"] == 1
    assert result["unhealthy_nodes"] == ["gpu-b"]


def test_two_tenants_have_quota_and_default_deny():
    quotas = list(yaml.safe_load_all((ROOT / "platform/ai-factory/base/quotas.yaml").read_text()))
    policies = list(yaml.safe_load_all((ROOT / "platform/ai-factory/base/network-policies.yaml").read_text()))
    assert {item["metadata"]["namespace"] for item in quotas} == {"ai-team-blue", "ai-team-gold"}
    assert all("requests.nvidia.com/gpu" in item["spec"]["hard"] for item in quotas)
    assert all(item["spec"]["policyTypes"] == ["Ingress", "Egress"] for item in policies)


def test_capability_matrix_is_honest_about_hardware_dependencies():
    matrix = yaml.safe_load((ROOT / "platform/ai-factory/capability-matrix.yaml").read_text())
    assert matrix["capabilities"]["hardware_lifecycle"]["status"] == "documented"
    assert matrix["capabilities"]["gpu_allocation"]["status"] == "production-overlay"


def test_api_router_is_wired():
    from server.api.main import app
    paths = {route.path for route in app.routes}
    assert "/ai-factory/plan" in paths
    assert "/ai-factory/capacity" in paths
