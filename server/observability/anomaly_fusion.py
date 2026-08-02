from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AnomalyFusion:
    def fuse(self, metrics: dict[str, Any] | None = None, logs: dict[str, Any] | None = None, traces: dict[str, Any] | None = None) -> dict[str, Any]:
        signals = []
        for name, payload in [("metrics", metrics), ("logs", logs), ("traces", traces)]:
            if payload:
                signals.append({"source": name, "payload": payload})
        return {
            "signal_count": len(signals),
            "signals": signals,
            "fusion_quality": "high" if len(signals) >= 3 else "partial" if signals else "none",
        }
