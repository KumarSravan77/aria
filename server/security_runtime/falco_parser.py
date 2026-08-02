from __future__ import annotations

from typing import Any


class FalcoParser:
    """Normalize Falco runtime security alerts into incident-style payloads."""

    def normalize(self, payload: dict[str, Any]) -> dict[str, Any]:
        output = payload.get("output") or payload.get("rule") or "Falco security event"
        priority = payload.get("priority", "Warning")
        service = payload.get("k8s", {}).get("pod_name") or payload.get("service", "security-runtime")
        return {
            "source": "falco",
            "alert_name": payload.get("rule", "falco-runtime-alert"),
            "service": service,
            "severity": "P1" if str(priority).lower() in {"critical", "emergency"} else "P2",
            "symptoms": [output],
            "signals": payload,
        }
