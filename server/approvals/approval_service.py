from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import Session
from server.db.models import Approval, IncidentAction, AuditLog
from server.utils_time import utc_now

QUEUED = 'QUEUED'
RUNNING = 'RUNNING'
SUCCEEDED = 'SUCCEEDED'
FAILED = 'FAILED'

STUCK_RUNNING_THRESHOLD_SECONDS = 600  # 10 minutes

class ApprovalService:
    def __init__(self, db: Session):
        self.db = db

    def request_approval(self, incident_id: str, action: dict, requested_by: str = 'ai-teammate') -> dict:
        action_row = IncidentAction(
            incident_id=incident_id,
            action=action.get('action'),
            target=action.get('target', 'unknown'),
            namespace=action.get('namespace'),
            requested_by=requested_by,
            result={**action, 'execution_status': 'PENDING_APPROVAL'},
        )
        self.db.add(action_row)
        self.db.flush()
        approval = Approval(incident_id=incident_id, action_id=action_row.id, status='PENDING')
        self.db.add(approval)
        self.db.add(AuditLog(actor=requested_by, action='approval.requested', resource_type='incident', resource_id=incident_id, metadata_json=action))
        self.db.commit()
        self.db.refresh(approval)
        return {'approval_id': approval.id, 'action_id': action_row.id, 'status': approval.status}

    def decide(self, approval_id: int, approved: bool, approver: str, reason: str | None = None) -> dict:
        approval = self.db.get(Approval, approval_id)
        if not approval:
            raise KeyError(f'Approval not found: {approval_id}')
        if approval.status != 'PENDING':
            raise ValueError(f'Approval {approval_id} is already {approval.status}')
        action_row = self.db.get(IncidentAction, approval.action_id) if approval.action_id else None
        if approved and not action_row:
            raise ValueError(f'Approval {approval_id} is not linked to an action')
        if approved and action_row and action_row.requested_by == approver:
            raise ValueError('Approver cannot be the same as requester')
        approval.status = 'APPROVED' if approved else 'REJECTED'
        approval.approver = approver
        approval.reason = reason
        approval.decided_at = utc_now()
        if action_row:
            action_row.approved = approved
            payload = action_row.result or {}
            action_row.result = {**payload, 'execution_status': QUEUED if approved else 'REJECTED'}
        self.db.add(AuditLog(actor=approver, action='approval.decided', resource_type='approval', resource_id=str(approval_id), metadata_json={'approved': approved, 'reason': reason}))
        self.db.commit()
        self.db.refresh(approval)
        return {'approval_id': approval.id, 'action_id': approval.action_id, 'status': approval.status, 'approver': approval.approver}

    def get_approval_target(self, approval_id: int) -> str | None:
        """Return the healing target (deployment/service name) for a pending approval."""
        approval = self.db.get(Approval, approval_id)
        if not approval or not approval.action_id:
            return None
        action_row = self.db.get(IncidentAction, approval.action_id)
        return action_row.target if action_row else None

    def queue_execution(self, approval_id: int) -> dict:
        approval = self.db.get(Approval, approval_id)
        if not approval:
            raise KeyError(f'Approval not found: {approval_id}')
        if approval.status != 'APPROVED':
            raise ValueError(f'Approval {approval_id} is not APPROVED')
        action_row = self.db.get(IncidentAction, approval.action_id) if approval.action_id else None
        if not action_row:
            raise KeyError(f'Action not found for approval: {approval_id}')
        if action_row.executed:
            raise ValueError(f'Action {action_row.id} has already been executed')
        payload = action_row.result or {}
        status = payload.get('execution_status')
        if status == QUEUED:
            # Already queued — idempotent return; no duplicate commit or audit entry (M-3).
            return {'approval_id': approval.id, 'action_id': action_row.id, 'execution_status': QUEUED}
        if status == RUNNING:
            if action_row.executed:
                raise ValueError(f'Action {action_row.id} has already been executed')
            started_at_str = payload.get('execution_started_at')
            if started_at_str and (utc_now() - datetime.fromisoformat(started_at_str)).total_seconds() > STUCK_RUNNING_THRESHOLD_SECONDS:
                # Worker crashed mid-execution before marking executed=True; reset so the
                # action can be retried. Never reset a row that has already executed.
                action_row.result = {**payload, 'execution_status': QUEUED, 'execution_started_at': None}
                self.db.add(AuditLog(actor=approval.approver or 'system', action='healing.stale_running_reset', resource_type='incident_action', resource_id=str(action_row.id), metadata_json={'approval_id': approval_id, 'was_running_since': started_at_str}))
                self.db.commit()
                return {'approval_id': approval.id, 'action_id': action_row.id, 'execution_status': QUEUED}
            raise ValueError(f'Action {action_row.id} is already RUNNING')
        if status == SUCCEEDED:
            raise ValueError(f'Action {action_row.id} is already SUCCEEDED')
        action_row.result = {**payload, 'execution_status': QUEUED}
        self.db.add(AuditLog(actor=approval.approver or 'system', action='healing.execution_queued', resource_type='incident_action', resource_id=str(action_row.id), metadata_json={'approval_id': approval_id}))
        self.db.commit()
        return {'approval_id': approval.id, 'action_id': action_row.id, 'execution_status': QUEUED}

    def execute_approved_action(self, approval_id: int, executor) -> dict:
        approval = self.db.get(Approval, approval_id)
        if not approval:
            raise KeyError(f'Approval not found: {approval_id}')
        if approval.status != 'APPROVED':
            raise ValueError(f'Approval {approval_id} is not APPROVED')
        if not approval.action_id:
            raise ValueError(f'Approval {approval_id} is not linked to an action')
        # Lock the action row before checking/changing execution state. On DBs that
        # support row locks this prevents two Celery workers from both claiming the
        # same approved action. SQLite ignores FOR UPDATE, but production DBs honor it.
        action_row = (
            self.db.query(IncidentAction)
            .filter(IncidentAction.id == approval.action_id)
            .with_for_update()
            .one_or_none()
        )
        if not action_row:
            raise KeyError(f'Action not found for approval: {approval_id}')
        if action_row.executed:
            raise ValueError(f'Action {action_row.id} has already been executed')
        payload = action_row.result or {}
        if payload.get('execution_status') == RUNNING:
            raise ValueError(f'Action {action_row.id} is already RUNNING')
        action_row.result = {**payload, 'execution_status': RUNNING, 'execution_started_at': utc_now().isoformat()}
        self.db.add(AuditLog(actor=approval.approver or 'system', action='healing.execution_started', resource_type='incident_action', resource_id=str(action_row.id), metadata_json={'approval_id': approval_id}))
        self.db.commit()
        try:
            result = executor.execute(
                action_row.action,
                action_row.namespace or payload.get('namespace') or 'default',
                action_row.target,
                replicas=payload.get('replicas'),
                revision=payload.get('revision'),
            )
        except Exception as exc:
            failure = {'error': str(exc), 'execution_status': FAILED}
            action_row.result = {**(action_row.result or {}), **failure}
            self.db.add(AuditLog(actor=approval.approver or 'system', action='healing.execution_failed', resource_type='incident_action', resource_id=str(action_row.id), metadata_json=failure))
            self.db.commit()
            return {'approval_id': approval.id, 'action_id': action_row.id, 'executed': False, 'execution_status': FAILED, 'error': str(exc)}
        action_row.executed = True
        action_row.result = {**(action_row.result or {}), 'execution_result': result, 'execution_status': SUCCEEDED}
        self.db.add(AuditLog(actor=approval.approver or 'system', action='healing.executed_after_approval', resource_type='incident_action', resource_id=str(action_row.id), metadata_json=result))
        self.db.commit()
        return {'approval_id': approval.id, 'action_id': action_row.id, 'executed': True, 'execution_status': SUCCEEDED, 'result': result}
