from server.workers.celery_app import celery_app
from server.db.session import SessionLocal, init_db
from server.incidents.repository import IncidentRepository
from server.correlation.incident_analyzer import IncidentAnalyzer
from server.rag.lazy_rag_service import LazyRagService as RagService
from server.approvals.approval_service import ApprovalService
from server.executors.action_executor import ActionExecutor
from server.db.models import Approval

@celery_app.task(name="server.workers.tasks.run_async_investigation")
def run_async_investigation(incident_id: str):
    init_db()
    db = SessionLocal()
    try:
        repo = IncidentRepository(db)
        incident = repo.get(incident_id)
        if not incident:
            return {"error": "incident not found", "incident_id": incident_id}
        payload = incident.payload
        analysis = IncidentAnalyzer().analyze(payload)
        rag_answer = RagService().answer(analysis["rag_query"], user=payload.get("user"))
        repo.add_timeline(incident_id, "async_ai_analysis", "Async investigation completed", {"analysis": analysis, "rag": rag_answer})
        return {"incident_id": incident_id, "analysis": analysis, "rag": rag_answer}
    finally:
        db.close()

@celery_app.task(name="server.workers.tasks.execute_approved_healing_action")
def execute_approved_healing_action(approval_id: int):
    init_db()
    db = SessionLocal()
    try:
        service = ApprovalService(db)
        result = service.execute_approved_action(approval_id, ActionExecutor())
        try:
            approval = db.get(Approval, approval_id)
            if approval:
                IncidentRepository(db).add_timeline(
                    approval.incident_id,
                    "healing_execution_completed",
                    f"Approved healing action completed with status {result.get('execution_status')}",
                    result,
                )
        except Exception:
            # Timeline updates must not mask the execution result.
            pass
        return result
    finally:
        db.close()

@celery_app.task(name="server.workers.tasks.plan_weekly_chaos_drill")
def plan_weekly_chaos_drill(service: str = "checkout-api", namespace: str = "demo"):
    from server.chaos.scheduler import ChaosScheduler
    return ChaosScheduler().plan_weekly(service=service, namespace=namespace)

@celery_app.task(name="server.workers.tasks.record_resilience_score")
def record_resilience_score(service: str, incident_id: str, score: float, outcome: str = "chaos_validated"):
    from server.memory.operational_memory import OperationalMemory
    init_db()
    db = SessionLocal()
    try:
        return OperationalMemory(db).record(
            service=service,
            incident_id=incident_id,
            outcome=outcome,
            remediation="resilience-validation",
            metadata={"resilience_score": score, "source": "celery"},
        )
    finally:
        db.close()
