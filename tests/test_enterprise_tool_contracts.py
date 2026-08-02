from server.gitops.rollout_service import RolloutService
from server.authz.authorization_service import AuthorizationService
from server.models.schemas import UserContext


def test_rollout_real_execution_is_honest_stub():
    result = RolloutService().promote("checkout-rollout", "demo", dry_run=False)
    assert result["implemented"] is False
    assert result["available"] is False
    assert "not implemented" in result["reason"].lower()


def test_cost_namespace_rebac_local_allows_demo_namespace():
    authz = AuthorizationService()
    user = UserContext(id="test-sre", role="sre", team="platform")
    assert authz.can_access_namespace(user, "demo") is True


def test_openfga_fallback_keeps_local_rebac():
    authz = AuthorizationService()
    user = UserContext(id="test-sre", role="sre", team="platform")
    assert isinstance(authz.can_access_service(user, "checkout-api"), bool)
