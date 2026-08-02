from __future__ import annotations

from typing import Any, Dict, Optional


class TelemetryConnector:
    """Normalizes telemetry snapshots from Prometheus/Dynatrace-style inputs.

    For now this accepts provided snapshots. Live Prometheus/Dynatrace clients can
    fill the same shape later.
    """

    def collect(self, snapshot: Optional[Dict[str, Any]] = None, slo_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        snapshot = snapshot or {}
        sli = snapshot.get("sli", snapshot)
        return {
            "status": "ok" if snapshot else "empty",
            "telemetry_snapshot": {
                "availability": sli.get("availability"),
                "latency_p95_ms": sli.get("latency_p95_ms"),
                "latency_p99_ms": sli.get("latency_p99_ms"),
                "error_rate": sli.get("error_rate"),
                "error_budget_remaining_percent": sli.get("error_budget_remaining_percent"),
                "burn_rate": sli.get("burn_rate"),
                "request_rate": sli.get("request_rate"),
                "saturation": sli.get("saturation", {}),
            },
            "slo_config": slo_config,
        }
