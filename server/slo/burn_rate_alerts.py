from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from server.slo.slo_engine import SloEngine

@dataclass
class SloBurnRateAlertEngine:
    """Converts SLO evaluation into actionable alert payloads."""
    slo_engine: SloEngine

    def evaluate(self, service: str, total_requests: int, failed_requests: int, slo_target: float = 99.9, window_minutes: int = 30) -> dict:
        result = self.slo_engine.evaluate(service, total_requests, failed_requests, slo_target)
        burn_rate = float(result.get("burn_rate", 0.0))
        severity = self._severity(burn_rate)
        alert = severity in {"critical", "warning"}
        return {
            "service": service,
            "window_minutes": window_minutes,
            "alert": alert,
            "severity": severity,
            "slo": result,
            "alertmanager_payload": self._alertmanager_payload(service, severity, result) if alert else None,
            "recommended_channel_update": self._message(service, severity, result),
        }

    def _severity(self, burn_rate: float) -> str:
        if burn_rate >= 14.0:
            return "critical"
        if burn_rate >= 6.0:
            return "warning"
        return "normal"

    def _message(self, service: str, severity: str, result: dict) -> str:
        return (
            f"SLO burn update for {service}: severity={severity}, "
            f"burn_rate={result.get('burn_rate')}, error_budget_remaining={result.get('error_budget_remaining')}%."
        )

    def _alertmanager_payload(self, service: str, severity: str, result: dict) -> dict:
        return {
            "receiver": "aria-slo",
            "status": "firing",
            "alerts": [{
                "labels": {"alertname": "SLOBurnRate", "service": service, "severity": severity},
                "annotations": {"summary": self._message(service, severity, result)},
            }],
        }
