from server.agents.kafka_agent import KafkaAgent
from server.platform.streaming.kafka.analyzers import KafkaLagAnalyzer, KafkaRebalanceAnalyzer, KafkaPartitionSkewAnalyzer
from server.investigation.langgraph.routing import GraphRouter
from server.investigation.langgraph.graph import LangGraphInvestigationWorkflow


def test_kafka_agent_degrades_gracefully_without_bootstrap():
    result = KafkaAgent().run({"service": "fraud-detection-engine", "signals": ["kafka", "consumer lag"]})
    assert result["agent"] == "kafka"
    assert "consumer_lag" in result
    assert "safety_boundary" in result


def test_kafka_lag_analyzer_detects_lag():
    result = KafkaLagAnalyzer().analyze(["consumer lag", "backpressure"])
    assert "consumer_lag_growth" in result["hypotheses"]


def test_kafka_rebalance_analyzer_detects_deployment_rebalance():
    result = KafkaRebalanceAnalyzer().analyze(["rebalance", "deployment"])
    assert "consumer_group_rebalance_storm" in result["hypotheses"]


def test_kafka_partition_skew_analyzer_detects_hot_partition():
    result = KafkaPartitionSkewAnalyzer().analyze(["hot partition"])
    assert "partition_skew_or_hot_key" in result["hypotheses"]


def test_graph_routes_kafka_signal():
    route = GraphRouter().route({"service": "fraud-detection-engine", "severity": "P1", "signals": ["kafka", "consumer lag"]})
    assert "kafka" in route


def test_workflow_executes_kafka_node():
    result = LangGraphInvestigationWorkflow().invoke({"service": "fraud-detection-engine", "severity": "P1", "signals": ["kafka", "consumer lag"]})
    assert "kafka" in result["summary"]["route"]
