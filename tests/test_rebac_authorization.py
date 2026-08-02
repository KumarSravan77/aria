from server.authz.authorization_service import AuthorizationService
from server.models.schemas import UserContext


def test_rebac_allows_team_supported_service():
    authz = AuthorizationService()
    user = UserContext(id="test-sre", role="sre", team="platform")
    assert authz.can_access_service(user, "checkout-api")
    assert "checkout-api" in authz.allowed_services(user)


def test_rebac_denies_unrelated_service():
    authz = AuthorizationService()
    user = UserContext(id="payments-sre", role="sre", team="payments")
    assert not authz.can_access_service(user, "hr-payroll")


def test_rebac_vector_filter_uses_allowed_services():
    authz = AuthorizationService()
    user = UserContext(id="payments-sre", role="sre", team="payments")
    where = authz.vector_where_filter(user)
    assert "service" in where
    assert "checkout-api" in str(where)
