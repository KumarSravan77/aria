from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_kyverno_policy_pack_exists():
    policy_dir = ROOT / "platform" / "security" / "kyverno" / "policies"
    assert (policy_dir / "require-resource-limits.yaml").exists()
    assert (policy_dir / "disallow-latest-tag.yaml").exists()
    assert (policy_dir / "restrict-privileged.yaml").exists()


def test_canary_rollout_assets_exist():
    assert (ROOT / "platform" / "gitops" / "rollouts" / "checkout-api-rollout.yaml").exists()
    assert (ROOT / "platform" / "gitops" / "rollouts" / "analysis-template.yaml").exists()
    assert (ROOT / "platform" / "mesh" / "istio" / "checkout-api-traffic.yaml").exists()


def test_security_tools_documented():
    for tool in ["falco", "gatekeeper", "trivy", "kubescape", "cert-manager"]:
        assert (ROOT / "platform" / "security" / tool / "README.md").exists()
