from __future__ import annotations
from enum import Enum
from typing import Any


class OrchestrationType(str, Enum):
    NORMAL   = "normal"    # all agents, forecasting, ranking, RCA
    DEGRADED = "degraded"  # metrics + logs only, cached memory, lightweight RCA
    SURVIVAL = "survival"  # incident creation only, no AI orchestration


# Agent names kept per mode
MODE_AGENT_ALLOWLIST: dict[OrchestrationType, set[str] | None] = {
    OrchestrationType.NORMAL:   None,                          # all
    OrchestrationType.DEGRADED: {"metrics", "logs"},
    OrchestrationType.SURVIVAL: set(),                         # none
}


class DegradationController:
    """Switches orchestration mode based on active-incident load thresholds.

    Thresholds are configurable so ops teams can tune per environment.
    Manual override is supported for drills and planned maintenance.
    """

    def __init__(
        self,
        degraded_threshold: int = 100,
        survival_threshold: int = 1000,
    ) -> None:
        self._manual: OrchestrationType | None = None
        self._degraded_threshold = degraded_threshold
        self._survival_threshold = survival_threshold

    def get_mode(self, active_incidents: int = 0) -> OrchestrationType:
        if self._manual is not None:
            return self._manual
        if active_incidents >= self._survival_threshold:
            return OrchestrationType.SURVIVAL
        if active_incidents >= self._degraded_threshold:
            return OrchestrationType.DEGRADED
        return OrchestrationType.NORMAL

    def set_manual(self, mode: OrchestrationType | None) -> None:
        self._manual = mode

    def filter_agents(self, agents: list, mode: OrchestrationType) -> list:
        names = MODE_AGENT_ALLOWLIST[mode]
        if names is None:
            return agents
        return [a for a in agents if getattr(a, "name", "") in names]

    def status(self) -> dict[str, Any]:
        return {
            "manual_override": self._manual,
            "degraded_threshold": self._degraded_threshold,
            "survival_threshold": self._survival_threshold,
        }
