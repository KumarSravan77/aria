from __future__ import annotations

from dataclasses import dataclass
import hashlib


@dataclass
class TraceSamplingPolicy:
    p1_sample_rate: float = 1.0
    p2_sample_rate: float = 0.5
    default_sample_rate: float = 0.1

    def should_trace(self, incident_id: str, severity: str = "P3") -> bool:
        severity = severity.upper()
        rate = self.default_sample_rate
        if severity in {"P1", "CRITICAL"}:
            rate = self.p1_sample_rate
        elif severity == "P2":
            rate = self.p2_sample_rate
        bucket = int(hashlib.sha256(incident_id.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        return bucket <= rate
