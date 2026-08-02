from server.investigation.langgraph.graph import LangGraphInvestigationWorkflow
from server.investigation.langgraph.routing import GraphRouter
from server.investigation.kubernetes_troubleshooter.rules import KubernetesTroubleshootingRules
from server.investigation.kubernetes_troubleshooter.agent import KubernetesTroubleshooterAgent

def test_graph_routes_p1_to_broad_investigation():
    route = GraphRouter().route({"service": "checkout-api", "severity": "P1", "signals": ["latency"]})
    assert "metrics" in route
    assert "rag" in route
    assert "rca" in route

def test_graph_survival_mode_reduces_route():
    route = GraphRouter().route({"service": "checkout-api", "severity": "P1"}, active_incidents=100)
    assert route == ["metrics", "logs"]

def test_kubernetes_rules_detect_crashloop():
    mode = KubernetesTroubleshootingRules().classify({"signals": ["CrashLoopBackOff"]})
    assert mode == "CrashLoopBackOff"

def test_kubernetes_troubleshooter_returns_read_only_evidence():
    result = KubernetesTroubleshooterAgent().run({"service": "checkout-api", "signals": ["OOMKilled"]})
    assert result["node"] == "kubernetes_troubleshooter"
    assert "safety_boundary" in result

def test_langgraph_workflow_invokes_and_checkpoints():
    result = LangGraphInvestigationWorkflow().invoke({"service": "checkout-api", "severity": "P3"})
    assert result["summary"]["evidence_count"] >= 1
    assert result["state"]["checkpoints"]
