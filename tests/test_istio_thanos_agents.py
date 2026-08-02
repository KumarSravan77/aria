from server.agents.istio_agent import IstioAgent
from server.agents.thanos_agent import ThanosAgent
from server.investigation.langgraph.routing import GraphRouter
from server.investigation.langgraph.graph import LangGraphInvestigationWorkflow


def test_istio_agent_degrades_gracefully():
    result = IstioAgent().run({"service": "checkout-api", "signals": ["istio", "mtls"]})
    assert result["agent"] == "istio"
    assert "evidence" in result


def test_thanos_agent_degrades_without_url():
    result = ThanosAgent(thanos_url=None).run({"service": "checkout-api", "signals": ["historical"]})
    assert result["agent"] == "thanos"
    assert "latency" in result


def test_graph_routes_istio_signal():
    route = GraphRouter().route({"service": "checkout-api", "severity": "P2", "signals": ["mtls", "virtualservice"]})
    assert "istio" in route


def test_graph_routes_thanos_signal():
    route = GraphRouter().route({"service": "checkout-api", "severity": "P2", "signals": ["historical", "slo trend"]})
    assert "thanos" in route


def test_workflow_executes_istio_thanos_nodes():
    result = LangGraphInvestigationWorkflow().invoke({"service": "checkout-api", "severity": "P2", "signals": ["istio", "historical"]})
    assert "istio" in result["summary"]["route"]
    assert "thanos" in result["summary"]["route"]
