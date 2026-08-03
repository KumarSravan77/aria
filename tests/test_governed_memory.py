from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.db.models import InvestigationCheckpoint
from server.db.session import Base
from server.investigation.langgraph.graph import LangGraphInvestigationWorkflow
from server.memory.operational_memory import OperationalMemory


def make_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_candidate_memory_does_not_enter_verified_recall():
    db = make_db()
    memory = OperationalMemory(db)
    stored = memory.record(
        "payment-processing-api", "INC-1", "resolved", "revert image",
        team="payments-platform", environment="prod", root_cause="missing image tag",
        evidence_references=[{"source": "jenkins", "id": "build-42"}],
    )
    assert stored["item"]["verification_status"] == "candidate"
    assert memory.recall("payment-processing-api", team="payments-platform", verified_only=True)["count"] == 0


def test_verified_memory_is_scoped_and_recalled():
    db = make_db()
    memory = OperationalMemory(db)
    stored = memory.record(
        "payment-processing-api", "INC-2", "resolved", "revert image",
        team="payments-platform", environment="prod", incident_type="cicd",
        root_cause="missing image tag", evidence_references=[{"source": "jenkins", "id": "build-43"}],
        recovery_metrics={"error_rate": 0.0}, sensitivity="confidential",
    )
    verified = memory.verify(stored["item"]["id"], "commander-1")
    assert verified["item"]["verification_status"] == "verified"
    assert memory.recall("payment-processing-api", team="other", verified_only=True)["count"] == 0
    recalled = memory.recall("payment-processing-api", team="payments-platform", environment="prod", verified_only=True)
    assert recalled["count"] == 1
    assert recalled["items"][0]["root_cause"] == "missing image tag"


def test_verification_requires_grounded_evidence():
    db = make_db()
    memory = OperationalMemory(db)
    stored = memory.record("payment-processing-api", "INC-3", "resolved", "unknown")
    try:
        memory.verify(stored["item"]["id"], "commander-1")
    except ValueError as exc:
        assert "root cause and evidence" in str(exc)
    else:
        raise AssertionError("ungrounded memory was verified")


def test_langgraph_persists_bounded_checkpoint_state():
    db = make_db()
    result = LangGraphInvestigationWorkflow.persistent(db).invoke({
        "incident_id": "INC-4", "service": "payment-processing-api", "team": "payments-platform",
        "environment": "prod", "severity": "P3", "signals": ["ImagePullBackOff"],
    })
    rows = db.query(InvestigationCheckpoint).all()
    assert rows
    assert all(row.investigation_id == result["summary"]["investigation_id"] for row in rows)
    assert "incident" not in rows[0].state_json
    assert "evidence_count" in rows[0].state_json
