from __future__ import annotations
import math
from typing import Any


class RLOptimizer:
    """UCB1 bandit for remediation action selection.

    State: (service, probable_cause, severity_bucket)
    Action: remediation action string
    Reward: function of success + MTTR
    UCB score = mean_reward + sqrt(2 * ln(total_trials) / action_trials)
    """

    def __init__(self) -> None:
        # {state_key: {action: [total_reward, count]}}
        self._table: dict[str, dict[str, list[float]]] = {}
        self._total_trials: int = 0

    def _state_key(self, service: str, probable_cause: str, severity: str) -> str:
        bucket = "high" if severity in {"P1", "critical", "emergency"} else "normal"
        return f"{service}|{probable_cause}|{bucket}"

    def update(self, service: str, probable_cause: str, severity: str,
               action: str, success: bool, mttr_seconds: int | None = None) -> None:
        key = self._state_key(service, probable_cause, severity)
        self._table.setdefault(key, {}).setdefault(action, [0.0, 0])
        base = 1.0 if success else -0.5
        mttr_bonus = 0.0
        if mttr_seconds is not None:
            if mttr_seconds <= 60:
                mttr_bonus = 0.5
            elif mttr_seconds <= 300:
                mttr_bonus = 0.2
            elif mttr_seconds > 600:
                mttr_bonus = -0.3
        reward = max(-1.0, min(1.5, base + mttr_bonus))
        self._table[key][action][0] += reward
        self._table[key][action][1] += 1
        self._total_trials += 1

    def recommend(self, service: str, probable_cause: str, severity: str,
                  allowed_actions: list[str]) -> list[dict[str, Any]]:
        key = self._state_key(service, probable_cause, severity)
        state = self._table.get(key, {})
        log_total = math.log(max(1, self._total_trials))
        scored = []
        for action in allowed_actions:
            if action in state and state[action][1] > 0:
                mean = state[action][0] / state[action][1]
                n = state[action][1]
                ucb = mean + math.sqrt(2 * log_total / n)
                scored.append({"action": action, "ucb_score": round(ucb, 3),
                                "mean_reward": round(mean, 3), "trials": n})
            else:
                scored.append({"action": action, "ucb_score": 99.0,
                                "mean_reward": 0.0, "trials": 0})
        scored.sort(key=lambda x: -x["ucb_score"])
        return scored

    def state_count(self) -> int:
        return len(self._table)
