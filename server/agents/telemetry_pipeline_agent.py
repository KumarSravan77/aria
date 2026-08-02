from __future__ import annotations

from server.agents.base import AgentResult, BaseAgent
from server.telemetry.pipeline_analyzer import PipelineAnalyzer


class TelemetryPipelineAgent(BaseAgent):
    name = "telemetry_pipeline"

    def __init__(self, analyzer: PipelineAnalyzer):
        self.analyzer = analyzer

    def run(self, incident: dict, context: dict | None = None) -> AgentResult:
        snapshot = self.analyzer.snapshot()
        return AgentResult(
            agent=self.name,
            available=bool(snapshot["available"]),
            summary=(
                f"Collected {snapshot['signals_available']}/{snapshot['signals_total']} pipeline signals"
                if snapshot["available"]
                else "Telemetry pipeline metrics are unavailable"
            ),
            evidence=[{"type": "telemetry-pipeline", "snapshot": snapshot}],
            recommendations=self.analyzer.recommend(snapshot),
        )
