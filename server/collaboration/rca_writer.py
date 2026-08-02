from datetime import datetime, timezone
from typing import Any, Dict, List


def generate_rca_draft(incident: Dict[str, Any], timeline: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
    """Generate a markdown RCA draft from incident context and timeline."""
    lines = [
        f"# RCA Draft: {incident.get('incident_id')} - {incident.get('service')}",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Severity: {incident.get('severity')}",
        f"Environment: {incident.get('environment')}",
        "",
        "## Executive Summary",
        analysis.get("summary") or _build_summary_fallback(incident, analysis),
        "",
        "## Probable Cause",
        analysis.get("probable_cause") or analysis.get("likely_cause") or "Unknown / pending confirmation.",
        "",
        "## Timeline",
    ]
    for event in timeline:
        lines.append(f"- {event['timestamp']} [{event['event_type']}] {event['message']}")
    lines.extend([
        "",
        "## Customer Impact",
        "TBD - update after impact analysis.",
        "",
        "## Mitigation",
        analysis.get("recommended_next_step", "TBD"),
        "",
        "## Follow-up Actions",
        "- Add or update runbook if missing.",
        "- Add alert tuning if signal/noise was poor.",
        "- Add regression test or chaos scenario if applicable.",
    ])
    return "\n".join(lines)


def _build_summary_fallback(incident: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    evidence = analysis.get("evidence") or analysis.get("findings") or []
    service = incident.get("service", "unknown service")
    if evidence:
        return f"{service} investigation found: " + "; ".join(str(item) for item in evidence) + "."
    return "Incident investigation is in progress."
