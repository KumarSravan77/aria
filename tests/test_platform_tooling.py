from server.platform.canary_planner import CanaryPlanner
from server.platform.tool_registry import list_tools
from server.platform.observability.thanos import ThanosClient
from server.platform.mesh.istio import IstioClient
from server.platform.autoscaling.vpa import VPAClient
from server.platform.autoscaling.karpenter import KarpenterClient
from server.platform.autoscaling.cluster_autoscaler import ClusterAutoscalerClient
from server.platform.security.kyverno import KyvernoClient
from server.platform.security.gatekeeper import GatekeeperClient
from server.platform.security.trivy import TrivyClient
from server.platform.security.kubescape import KubescapeClient
from server.platform.security.cert_manager import CertManagerClient
from server.platform.cluster_lifecycle.cluster_api import ClusterAPIClient
from server.platform.cluster_lifecycle.kops import KopsClient
from server.platform.cluster_lifecycle.rancher import RancherClient
# Re-exports
from server.platform.gitops.argocd import ArgoCDClient
from server.platform.gitops.rollouts import RolloutService
from server.platform.autoscaling.keda import KedaClient
from server.platform.security.falco import FalcoParser


def test_canary_planner_has_safety_boundary():
    plan = CanaryPlanner().plan("checkout-api", namespace="demo")
    assert plan["available"] is True
    assert plan["strategy"] == "canary"
    assert "approval" in plan["safety_boundary"].lower()


def test_canary_planner_custom_steps():
    plan = CanaryPlanner().plan("checkout-api", traffic_steps=[20, 50, 100])
    assert plan["traffic_steps"] == [20, 50, 100]


def test_canary_planner_rejects_unsupported_strategy():
    plan = CanaryPlanner().plan("svc", strategy="rolling")
    assert plan["available"] is False


def test_tool_registry_all_20_tools():
    data = list_tools()
    assert len(data["tools"]) == 20


def test_tool_registry_folder_paths_use_underscores():
    tools = list_tools()["tools"]
    for tool in tools:
        assert "-" not in tool["folder"].split("/")[-1], \
            f"{tool['name']} folder uses hyphens: {tool['folder']}"


def test_tool_registry_default_stack_contains_primary_tools():
    stack = list_tools()["default_stack"]
    assert "Kyverno" in stack
    assert "Thanos" in stack
    assert "Argo Rollouts" in stack
    assert "Karpenter" in stack
    assert "cert-manager" in stack


# ── New adapter graceful-degradation tests ───────────────────────────────────

def test_thanos_degrades_gracefully():
    result = ThanosClient(base_url="http://localhost:1").query("up")
    assert result["available"] is False
    assert "error" in result


def test_istio_traffic_policy_returns_honest_stub():
    result = IstioClient().traffic_policy("checkout-api")
    assert result["available"] is False
    assert "Wire to Istio" in result["message"]


def test_vpa_degrades_gracefully():
    result = VPAClient().recommendations("checkout-api")
    assert result["available"] is False


def test_karpenter_degrades_gracefully():
    result = KarpenterClient().nodepools()
    assert result["available"] is False


def test_cluster_autoscaler_degrades_gracefully():
    result = ClusterAutoscalerClient(base_url="http://localhost:1").status()
    assert result["available"] is False


def test_kyverno_degrades_gracefully():
    result = KyvernoClient().policy_reports()
    assert result["available"] is False


def test_gatekeeper_degrades_gracefully():
    result = GatekeeperClient().violations()
    assert result["available"] is False
    assert "Kyverno is the primary" in result["message"]


def test_trivy_degrades_gracefully():
    result = TrivyClient().vulnerability_reports()
    assert result["available"] is False


def test_kubescape_degrades_without_config():
    result = KubescapeClient().posture_score()
    assert result["available"] is False
    assert "KUBESCAPE" in result["message"]


def test_cert_manager_degrades_gracefully():
    result = CertManagerClient().certificates()
    assert result["available"] is False


def test_cluster_api_degrades_gracefully():
    result = ClusterAPIClient().clusters()
    assert result["available"] is False


def test_kops_degrades_when_not_installed():
    result = KopsClient().list_clusters()
    assert result["available"] is False


def test_rancher_degrades_without_config():
    result = RancherClient().clusters()
    assert result["available"] is False
    assert "RANCHER_TOKEN" in result["message"]


# ── Re-export smoke tests ─────────────────────────────────────────────────────

def test_reexports_resolve_correctly():
    assert ArgoCDClient is not None
    assert RolloutService is not None
    assert KedaClient is not None
    assert FalcoParser is not None
