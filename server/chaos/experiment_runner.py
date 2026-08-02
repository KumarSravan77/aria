from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from server.chaos.litmus_client import LitmusChaosClient
from server.chaos.validation_engine import ChaosValidationEngine
from server.chaos.chaos_reporter import ChaosReporter


@dataclass
class ChaosExperimentRunner:
    litmus: LitmusChaosClient
    validator: ChaosValidationEngine
    reporter: ChaosReporter

    def run(self, *, experiment: str, namespace: str, service: str, app_label: str, duration_seconds: int | None = None, dry_run: bool = True) -> dict[str, Any]:
        result = self.litmus.run_experiment(
            experiment=experiment,
            namespace=namespace,
            service=service,
            app_label=app_label,
            duration_seconds=duration_seconds,
            dry_run=dry_run,
        )
        return {
            "chaos": result,
            "next_steps": [
                "Confirm Prometheus alert fired for this failure mode.",
                "Confirm incident intake created or updated an incident.",
                "Run /chaos/validate with observed signals to calculate resilience score.",
                "Generate RCA or resilience report after recovery.",
            ],
        }
