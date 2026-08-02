ALLOWED_TRANSITIONS = {
    "TRIGGERED": {"ACKNOWLEDGED", "INVESTIGATING", "MITIGATED", "RESOLVED"},
    "ACKNOWLEDGED": {"INVESTIGATING", "MITIGATED", "RESOLVED"},
    "INVESTIGATING": {"MITIGATED", "RESOLVED", "ESCALATED"},
    "ESCALATED": {"INVESTIGATING", "MITIGATED", "RESOLVED"},
    "MITIGATED": {"RESOLVED", "INVESTIGATING"},
    "RESOLVED": {"RCA_PENDING", "CLOSED"},
    "RCA_PENDING": {"CLOSED"},
    "CLOSED": set(),
}

def can_transition(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())

def require_transition(current: str, target: str):
    if not can_transition(current, target):
        raise ValueError(f"Invalid incident status transition: {current} -> {target}")
