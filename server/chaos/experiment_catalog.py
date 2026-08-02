from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class ChaosExperimentDefinition:
    name: str
    litmus_experiment: str
    description: str
    default_duration_seconds: int
    risk_level: str
    expected_signal: str
    runbook_query: str

    def to_dict(self) -> dict:
        return asdict(self)


CATALOG: dict[str, ChaosExperimentDefinition] = {
    "pod-delete": ChaosExperimentDefinition(
        name="pod-delete",
        litmus_experiment="pod-delete",
        description="Deletes one or more checkout-api pods to validate restart, alerting, and recovery workflows.",
        default_duration_seconds=30,
        risk_level="low",
        expected_signal="pod restart / temporary availability dip",
        runbook_query="checkout-api pod delete kubernetes recovery runbook",
    ),
    "cpu-hog": ChaosExperimentDefinition(
        name="cpu-hog",
        litmus_experiment="pod-cpu-hog",
        description="Consumes CPU inside target pods to validate HPA, latency alerts, and scaling recommendations.",
        default_duration_seconds=60,
        risk_level="medium",
        expected_signal="cpu saturation / p95 latency increase",
        runbook_query="checkout-api cpu saturation high latency runbook",
    ),
    "memory-hog": ChaosExperimentDefinition(
        name="memory-hog",
        litmus_experiment="pod-memory-hog",
        description="Consumes memory to validate OOM handling, restart detection, and memory pressure runbooks.",
        default_duration_seconds=60,
        risk_level="medium",
        expected_signal="memory pressure / possible OOMKilled event",
        runbook_query="checkout-api memory pressure OOMKilled runbook",
    ),
    "network-latency": ChaosExperimentDefinition(
        name="network-latency",
        litmus_experiment="pod-network-latency",
        description="Injects latency to validate timeout/retry behaviour, alerting, and RCA quality.",
        default_duration_seconds=60,
        risk_level="medium",
        expected_signal="p95/p99 latency increase / timeout logs",
        runbook_query="checkout-api network latency timeout runbook",
    ),
    "dns-failure": ChaosExperimentDefinition(
        name="dns-failure",
        litmus_experiment="pod-dns-error",
        description="Injects DNS lookup failures to validate service discovery runbooks and dependency impact analysis.",
        default_duration_seconds=45,
        risk_level="medium",
        expected_signal="DNS resolution errors / downstream call failures",
        runbook_query="checkout-api DNS failure service discovery runbook",
    ),
}


def list_experiments() -> list[dict]:
    return [item.to_dict() for item in CATALOG.values()]


def get_experiment(name: str) -> ChaosExperimentDefinition:
    try:
        return CATALOG[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported chaos experiment '{name}'. Supported: {', '.join(sorted(CATALOG))}") from exc
