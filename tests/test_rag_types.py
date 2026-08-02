from server.rag_types.simple_rag import SimpleOperationalRag
from server.rag_types.agentic_rag import AgenticOperationalRag
from server.rag_types.graph_rag import GraphOperationalRag

def test_simple_rag_retrieves_fraud_kafka():
    result = SimpleOperationalRag().retrieve("kafka consumer lag fraud", service="fraud-detection-engine")
    assert result["count"] >= 1

def test_agentic_rag_runs_multiple_queries():
    result = AgenticOperationalRag().retrieve({"service":"fraud-detection-engine","domain":"aml_fraud","severity":"P1","signals":["kafka","consumer lag"]})
    assert result["rag_type"] == "agentic"
    assert len(result["queries"]) == 3

def test_graph_rag_builds_graph():
    result = GraphOperationalRag().retrieve("kafka lag fraud", service="fraud-detection-engine", depth=1)
    assert result["rag_type"] == "graph"
    assert result["graph"]["node_count"] > 0
