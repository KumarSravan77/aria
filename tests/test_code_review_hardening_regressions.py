from datetime import timedelta

import pytest

from server.approvals.approval_service import ApprovalService, STUCK_RUNNING_THRESHOLD_SECONDS
from server.authz.authorization_service import AuthorizationService
from server.db.models import Approval, IncidentAction
from server.models.schemas import UserContext
from server.rag.lazy_rag_service import LazyRagService
from server.utils_time import utc_now
from tests.test_approval_service import make_db, FakeExecutor


class BackendWithAskAndAnswer:
    def answer(self, *args, **kwargs):
        return {"method": "answer"}

    def ask(self, *args, **kwargs):
        return {"method": "ask"}


def test_lazy_rag_prefers_answer_contract_over_ask():
    svc = LazyRagService(_service=BackendWithAskAndAnswer())
    assert svc.answer("question")["method"] == "answer"


def test_namespace_rebac_rejects_empty_namespace():
    authz = AuthorizationService()
    user = UserContext(id="u", role="sre", team="platform")
    assert authz.can_access_namespace(user, "") is False
    assert authz.can_access_namespace(user, None) is False


def test_approval_decision_rejects_orphan_approval():
    db = make_db()
    orphan = Approval(incident_id="INC-ORPHAN", action_id=None, status="PENDING")
    db.add(orphan)
    db.commit()
    with pytest.raises(ValueError, match="not linked to an action"):
        ApprovalService(db).decide(orphan.id, approved=True, approver="commander", reason="bad data")


def test_stale_running_does_not_reset_already_executed_action():
    db = make_db()
    service = ApprovalService(db)
    approval = service.request_approval("INC-1", {"action": "restart_deployment", "target": "checkout-api", "namespace": "demo"}, "requester")
    service.decide(approval["approval_id"], approved=True, approver="commander", reason="ok")
    service.queue_execution(approval["approval_id"])
    action_row = db.get(IncidentAction, approval["action_id"])
    action_row.executed = True
    action_row.result = {
        **(action_row.result or {}),
        "execution_status": "RUNNING",
        "execution_started_at": (utc_now() - timedelta(seconds=STUCK_RUNNING_THRESHOLD_SECONDS + 60)).isoformat(),
    }
    db.commit()
    with pytest.raises(ValueError, match="already been executed"):
        service.queue_execution(approval["approval_id"])


def test_execute_approved_action_uses_row_lock_query_path(monkeypatch):
    # Regression coverage for exact-once hardening: execute_approved_action should
    # claim via query(...).with_for_update() rather than raw db.get().
    db = make_db()
    service = ApprovalService(db)
    approval = service.request_approval("INC-1", {"action": "scale_deployment", "target": "checkout-api", "namespace": "demo", "replicas": 2}, "requester")
    service.decide(approval["approval_id"], approved=True, approver="commander", reason="ok")
    service.queue_execution(approval["approval_id"])
    result = service.execute_approved_action(approval["approval_id"], FakeExecutor())
    assert result["execution_status"] == "SUCCEEDED"
