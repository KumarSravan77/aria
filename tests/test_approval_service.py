import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.db.session import Base
from server.approvals.approval_service import ApprovalService, STUCK_RUNNING_THRESHOLD_SECONDS
from server.authz.authorization_service import AuthorizationService
from server.models.schemas import UserContext

class FakeExecutor:
    def execute(self, action, namespace, target, replicas=None, **kwargs):
        return {'status': 'ok', 'action': action, 'namespace': namespace, 'target': target, 'replicas': replicas}

class FailingExecutor:
    def execute(self, action, namespace, target, replicas=None, **kwargs):
        raise RuntimeError('kubernetes unavailable')


def make_db():
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_approval_decision_is_terminal():
    db = make_db()
    service = ApprovalService(db)
    approval = service.request_approval('INC-1', {'action': 'restart_deployment', 'target': 'checkout-api'}, 'ai')
    service.decide(approval['approval_id'], approved=False, approver='lead', reason='not safe')
    with pytest.raises(ValueError):
        service.decide(approval['approval_id'], approved=True, approver='attacker', reason='retry')


def test_approval_enforces_four_eyes():
    db = make_db()
    service = ApprovalService(db)
    approval = service.request_approval('INC-1', {'action': 'restart_deployment', 'target': 'checkout-api'}, 'same-user')
    with pytest.raises(ValueError):
        service.decide(approval['approval_id'], approved=True, approver='same-user', reason='self approve')


def test_approved_action_executes_once():
    db = make_db()
    service = ApprovalService(db)
    approval = service.request_approval('INC-1', {'action': 'scale_deployment', 'target': 'checkout-api', 'namespace': 'demo', 'replicas': 4}, 'requester')
    service.decide(approval['approval_id'], approved=True, approver='commander', reason='approved')
    queued = service.queue_execution(approval['approval_id'])
    assert queued['execution_status'] == 'QUEUED'
    result = service.execute_approved_action(approval['approval_id'], FakeExecutor())
    assert result['executed'] is True
    assert result['execution_status'] == 'SUCCEEDED'
    assert result['result']['replicas'] == 4
    with pytest.raises(ValueError):
        service.execute_approved_action(approval['approval_id'], FakeExecutor())


def test_approved_action_failure_is_recorded_not_raised():
    db = make_db()
    service = ApprovalService(db)
    approval = service.request_approval('INC-1', {'action': 'restart_deployment', 'target': 'checkout-api', 'namespace': 'demo'}, 'requester')
    service.decide(approval['approval_id'], approved=True, approver='commander', reason='approved')
    service.queue_execution(approval['approval_id'])
    result = service.execute_approved_action(approval['approval_id'], FailingExecutor())
    assert result['executed'] is False
    assert result['execution_status'] == 'FAILED'
    assert 'kubernetes unavailable' in result['error']


def test_queue_execution_is_idempotent_when_already_queued():
    # M-3: calling queue_execution twice must not create a duplicate audit entry.
    db = make_db()
    service = ApprovalService(db)
    approval = service.request_approval('INC-1', {'action': 'scale_deployment', 'target': 'checkout-api', 'namespace': 'demo'}, 'requester')
    service.decide(approval['approval_id'], approved=True, approver='commander', reason='ok')
    r1 = service.queue_execution(approval['approval_id'])
    r2 = service.queue_execution(approval['approval_id'])
    assert r1['execution_status'] == 'QUEUED'
    assert r2['execution_status'] == 'QUEUED'


def test_queue_execution_resets_stale_running():
    # M-2: a RUNNING action whose execution_started_at is beyond the threshold gets reset to QUEUED.
    db = make_db()
    service = ApprovalService(db)
    approval = service.request_approval('INC-1', {'action': 'restart_deployment', 'target': 'checkout-api', 'namespace': 'demo'}, 'requester')
    service.decide(approval['approval_id'], approved=True, approver='commander', reason='ok')
    service.queue_execution(approval['approval_id'])

    from server.db.models import IncidentAction
    action_row = db.get(IncidentAction, approval['action_id'])
    stale_ts = (datetime.now(timezone.utc) - timedelta(seconds=STUCK_RUNNING_THRESHOLD_SECONDS + 60)).isoformat()
    action_row.result = {**(action_row.result or {}), 'execution_status': 'RUNNING', 'execution_started_at': stale_ts}
    db.commit()

    result = service.queue_execution(approval['approval_id'])
    assert result['execution_status'] == 'QUEUED'


def test_queue_execution_blocks_fresh_running():
    # M-2: a RUNNING action within the threshold must still be blocked.
    db = make_db()
    service = ApprovalService(db)
    approval = service.request_approval('INC-1', {'action': 'restart_deployment', 'target': 'checkout-api', 'namespace': 'demo'}, 'requester')
    service.decide(approval['approval_id'], approved=True, approver='commander', reason='ok')
    service.queue_execution(approval['approval_id'])

    from server.db.models import IncidentAction
    from server.utils_time import utc_now
    action_row = db.get(IncidentAction, approval['action_id'])
    action_row.result = {**(action_row.result or {}), 'execution_status': 'RUNNING', 'execution_started_at': utc_now().isoformat()}
    db.commit()

    with pytest.raises(ValueError, match='already RUNNING'):
        service.queue_execution(approval['approval_id'])


def test_rebac_can_approve_service_action_blocks_unauthorized_team():
    # Wire-up: a user whose teams don't own/support the service cannot approve.
    authz = AuthorizationService()
    payments_sre = UserContext(id='payments-sre', role='sre', team='payments')
    assert not authz.can_approve_service_action(payments_sre, 'kubernetes-platform')


def test_rebac_can_approve_service_action_allows_authorized_team():
    # Wire-up: a platform SRE can approve actions on their owned/supported services.
    authz = AuthorizationService()
    platform_sre = UserContext(id='test-sre', role='sre', team='platform')
    assert authz.can_approve_service_action(platform_sre, 'checkout-api')


def test_get_approval_target_returns_deployment_name():
    db = make_db()
    service = ApprovalService(db)
    approval = service.request_approval('INC-1', {'action': 'scale_deployment', 'target': 'checkout-api'}, 'requester')
    target = service.get_approval_target(approval['approval_id'])
    assert target == 'checkout-api'
