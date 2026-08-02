from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.agents.orchestrator import MultiAgentOrchestrator
from server.agents.base import AgentResult
from server.config import settings
from server.db.session import Base
from server.memory.operational_memory import OperationalMemory
from server.chaos.validation_engine import ChaosValidationEngine


class GoodAgent:
    name = "good"

    def run(self, incident, context=None):
        return AgentResult(agent=self.name, available=True, summary="ok", evidence=["e1"], recommendations=["r1"])


class BadAgent:
    name = "bad"

    def run(self, incident, context=None):
        raise RuntimeError("boom")


def make_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_chaos_disabled_by_default():
    assert settings.chaos_enabled is False


def test_multi_agent_orchestrator_preserves_order_and_failure_boundary():
    result = MultiAgentOrchestrator([GoodAgent(), BadAgent()]).investigate({"incident_id": "INC-1", "service": "checkout-api", "severity": "P1"})
    # Mode now includes degradation state: "multi-agent-normal-parallel" (was "deterministic")
    assert result["mode"].startswith("multi-agent-")
    assert result["agent_count"] == 2
    assert result["agents"][0]["agent"] == "good"
    assert result["agents"][1]["agent"] == "bad"
    assert result["agents"][1]["available"] is False
    assert "ReBAC" in result["safety_boundary"]


def test_operational_memory_persists_to_database():
    db = make_db()
    memory = OperationalMemory(db)
    stored = memory.record("checkout-api", "INC-1", "resolved", "scaled deployment", {"source": "test"})
    assert stored["backend"] == "database"
    recalled = memory.recall("checkout-api")
    assert recalled["backend"] == "database"
    assert recalled["count"] == 1
    assert recalled["items"][0]["incident_id"] == "INC-1"


def test_chaos_validation_explicit_contract():
    result = ChaosValidationEngine().validate(
        service="checkout-api",
        experiment="pod-delete",
        incident_created=True,
        alert_fired=True,
        healing_succeeded=True,
        rag_sources=2,
        mttr_seconds=45,
        slo_burn_observed=True,
    )
    assert result["status"] == "passed"
    assert result["resilience_score"] >= 90
