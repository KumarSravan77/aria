from __future__ import annotations
from typing import Any


# Agent name sets per incident profile. None means "run all agents".
_ROUTES: dict[str, set[str] | None] = {
    "p3_low":     {"metrics", "logs"},
    "deployment": {"metrics", "rca", "remediation_ranker"},
    "kubernetes": {"k8s", "metrics", "traces", "rca"},
    "security":   {"k8s", "metrics", "logs", "rca"},
    "p2_default": {"metrics", "logs", "rag", "healing", "rca", "remediation_ranker"},
    "p1_full":    None,  # all agents
}


class AgentRouter:
    """Selects the minimal agent set relevant to an incident.

    Reduces orchestration fan-out, token usage, and threadpool pressure
    by skipping agents whose evidence would not add value for the current
    incident type and severity.
    """

    def select(self, incident: dict[str, Any], all_agents: list) -> tuple[list, str]:
        """Return (selected_agents, selection_reason)."""
        severity = (incident.get("severity") or "P2").upper()
        symptoms = [s.lower() for s in incident.get("symptoms", [])]
        signals = incident.get("signals", {}) or {}
        probable_cause = (incident.get("probable_cause") or "").lower()

        # P1 always runs everything
        if severity == "P1":
            return all_agents, "p1_full: all agents for critical incident"

        # Route by signal content
        if signals.get("recent_deployment") or "deployment" in probable_cause:
            profile = "deployment"
        elif any(w in " ".join(symptoms + [probable_cause]) for w in ("pod", "crashloop", "kubernetes", "k8s", "oom")):
            profile = "kubernetes"
        elif any(w in " ".join(symptoms + [probable_cause]) for w in ("security", "falco", "intrusion", "privilege")):
            profile = "security"
        elif severity in {"P3", "P4"}:
            profile = "p3_low"
        else:
            profile = "p2_default"

        names = _ROUTES[profile]
        if names is None:
            return all_agents, f"{profile}: all agents"

        selected = [a for a in all_agents if getattr(a, "name", "") in names]
        # Safety fallback: if profile would produce no agents, run everything.
        if not selected:
            return all_agents, f"{profile}: no profile matches — running all agents"
        skipped = [getattr(a, "name", "") for a in all_agents if a not in selected]
        return selected, f"{profile}: skipped={skipped}"
