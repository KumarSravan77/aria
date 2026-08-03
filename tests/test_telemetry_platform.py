from server.agents.telemetry_pipeline_agent import TelemetryPipelineAgent
from server.telemetry.capacity import capacity_plan
from server.telemetry.pipeline_analyzer import PipelineAnalyzer


class FakeMetrics:
    def __init__(self, available=True):
        self.available = available

    def query(self, promql):
        return {"available": self.available, "query": promql, "result": []}


def test_capacity_plan_is_explicit_about_100tb_assumptions():
    plan = capacity_plan(100, peak_multiplier=3, replication_factor=3)
    assert plan["design_peak_mbps"] > plan["average_ingest_mbps"]
    assert plan["minimum_log_partitions"] >= 3
    assert plan["design_peak_events_per_second"] > plan["average_events_per_second"]
    assert plan["minimum_collector_replicas"] >= 2
    assert plan["minimum_gateway_replicas"] >= 3
    assert plan["estimated_archive_storage_tb"] > plan["estimated_hot_storage_tb"]
    assert "Planning estimate" in plan["disclaimer"]


def test_pipeline_analyzer_collects_all_signals():
    result = PipelineAnalyzer(FakeMetrics()).snapshot()
    assert result["available"] is True
    assert result["signals_available"] == len(PipelineAnalyzer.QUERIES)


def test_pipeline_agent_fails_closed_without_metrics():
    result = TelemetryPipelineAgent(PipelineAnalyzer(FakeMetrics(False))).run({})
    assert result.available is False
    assert "Restore Prometheus" in result.recommendations[0]
