from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ChaosReporter:
    """Produces human-readable resilience reports for chaos validations."""

    def markdown(self, validation: dict[str, Any]) -> str:
        checks = validation.get("checks", {})
        lines = [
            f"# Chaos Resilience Report: {validation.get('service')} / {validation.get('experiment')}",
            "",
            f"Status: **{validation.get('status')}**",
            f"Resilience score: **{validation.get('resilience_score')} / 100**",
            f"Validated at: {validation.get('validated_at')}",
            "",
            "## Checks",
        ]
        for name, passed in checks.items():
            lines.append(f"- {'✅' if passed else '❌'} {name}")
        lines.extend(["", "## Recommendations"])
        for rec in validation.get("recommendations", []):
            lines.append(f"- {rec}")
        return "\n".join(lines)
