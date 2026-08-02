from server.agents.orchestrator import MultiAgentOrchestrator
from server.agents.k8s_agent import KubernetesAgent
from server.chatops.command_parser import ChatOpsCommandParser
from server.slo.slo_engine import SloEngine
from server.deployment.deployment_intelligence import DeploymentIntelligence
from server.memory.operational_memory import OperationalMemory


def test_multi_agent_orchestrator_degrades_safely():
    # P1 ensures all agents run; router fallback also guarantees at least 1 agent
    result = MultiAgentOrchestrator([KubernetesAgent()]).investigate(
        {"incident_id": "INC-1", "service": "checkout-api", "severity": "P1"})
    assert result["agent_count"] == 1
    assert result["evidence_count"] >= 1
    assert "safety_boundary" in result


def test_slo_engine_calculates_burn_rate():
    result = SloEngine().evaluate("checkout-api", total_requests=10000, failed_requests=42, slo_target=99.9)
    assert result["service"] == "checkout-api"
    assert result["burn_rate"] > 1


def test_chatops_parser_accepts_safe_commands():
    parsed = ChatOpsCommandParser().parse("/approve-action 42")
    assert parsed["valid"] is True
    assert parsed["command"] == "/approve-action"


def test_deployment_intelligence_flags_related_deployments():
    result = DeploymentIntelligence().correlate({"service":"checkout-api","symptoms":["high latency"],"signals":{"recent_deployments":[{"service":"checkout-api","revision":"abc"}]}})
    assert result["deployment_correlation"] == "high"


def test_operational_memory_records_and_recalls():
    mem = OperationalMemory()
    mem.record("checkout-api", "INC-1", "mitigated", "scaled")
    assert mem.recall("checkout-api")["count"] == 1
