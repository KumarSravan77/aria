from dataclasses import dataclass

@dataclass
class SloResult:
    service: str
    slo_target: float
    availability: float
    error_budget_remaining: float
    burn_rate: float
    severity: str

class SloEngine:
    def evaluate(self, service: str, total_requests: int = 10000, failed_requests: int = 0, slo_target: float = 99.9) -> dict:
        if total_requests <= 0:
            availability = 100.0
        else:
            availability = max(0.0, 100.0 * (total_requests - failed_requests) / total_requests)
        allowed_error = max(0.0001, 100.0 - slo_target)
        actual_error = max(0.0, 100.0 - availability)
        burn_rate = round(actual_error / allowed_error, 2)
        remaining = round(max(0.0, 100.0 - (actual_error / allowed_error * 100.0)), 2)
        severity = "critical" if burn_rate >= 10 else "warning" if burn_rate >= 2 else "healthy"
        return SloResult(service, slo_target, round(availability, 4), remaining, burn_rate, severity).__dict__
