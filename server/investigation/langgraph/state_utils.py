from __future__ import annotations

from copy import deepcopy
from typing import Any
import time


def dedupe_evidence(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in evidence:
        key = (
            item.get("node"),
            item.get("type"),
            item.get("summary"),
            str(item.get("failure_mode") or item.get("hypothesis") or item.get("result", ""))[:200],
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def merge_state(state: dict[str, Any], patch: dict[str, Any], node: str | None = None) -> dict[str, Any]:
    next_state = deepcopy(state)
    for key, value in patch.items():
        if key in {"evidence", "hypotheses", "recommendations", "errors", "checkpoints"}:
            next_state.setdefault(key, [])
            if isinstance(value, list):
                next_state[key].extend(value)
            else:
                next_state[key].append(value)
        elif key == "metadata":
            next_state.setdefault("metadata", {})
            next_state["metadata"].update(value or {})
        else:
            next_state[key] = value

    next_state["evidence"] = dedupe_evidence(next_state.get("evidence", []))
    if node:
        next_state.setdefault("node_history", []).append({"node": node, "timestamp": time.time()})
    return next_state


def route_budget(route: list[str], max_specialists: int = 7) -> list[str]:
    priority = [
        "metrics", "logs", "traces",
        "kubernetes_troubleshooter",
        "kafka",
        "istio",
        "thanos",
        "rag",
        "security",
        "rca",
        "healing",
        "chatops",
    ]
    ordered = [node for node in priority if node in route]
    # keep core always if present, cap specialists before rca/healing/chatops
    core = [n for n in ordered if n in {"metrics", "logs", "rca"}]
    specialists = [n for n in ordered if n not in {"metrics", "logs", "rca", "healing", "chatops"}]
    tail = [n for n in ordered if n in {"healing", "chatops"}]
    final = []
    for n in core + specialists[:max_specialists] + tail:
        if n not in final:
            final.append(n)
    return final
