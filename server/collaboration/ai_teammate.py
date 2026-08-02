from __future__ import annotations
from typing import Any, Dict, List


class AITeammate:
    """Formats AI teammate messages for incident war rooms."""

    def opening_update(self, incident: Dict[str, Any], channel: Dict[str, Any]) -> str:
        signals = incident.get("signals", {})
        symptoms = incident.get("symptoms", [])
        lines = [
            f"🚨 Incident Created: {incident.get('severity', 'P2')} - {incident.get('service')}",
            "",
            f"Incident ID: {incident.get('incident_id')}",
            f"Service: {incident.get('service')}",
            f"Environment: {incident.get('environment', 'dev')}",
            f"Channel: #{channel.get('channel_name')}",
            "",
            "Initial symptoms:",
        ]
        lines.extend([f"- {s}" for s in symptoms] or ["- No symptoms provided"])
        lines.append("")
        lines.append("Initial signals:")
        lines.extend([f"- {k}: {v}" for k, v in signals.items()] or ["- No signals provided"])
        lines.extend([
            "",
            "I am starting investigation now:",
            "1. Correlate metrics, logs, Kubernetes events, and deployment timing",
            "2. Retrieve matching runbooks and previous RCAs through RAG",
            "3. Recommend safe remediation with policy validation",
            "4. Keep this channel updated with timeline events",
        ])
        return "\n".join(lines)

    def investigation_update(self, analysis: Dict[str, Any], runbook_guidance: Dict[str, Any] | str) -> str:
        steps: List[str] = analysis.get("evidence") or analysis.get("findings") or []
        probable = analysis.get("probable_cause") or analysis.get("likely_cause") or "Unknown - needs more evidence"
        next_step = analysis.get("recommended_next_step", "Continue investigation")
        return "\n".join([
            "🤖 AI Investigation Update",
            "",
            f"Probable cause: {probable}",
            "Evidence:",
            *(f"- {s}" for s in steps),
            "",
            f"Recommended next step: {next_step}",
            "",
            "Runbook guidance retrieved and attached in the incident API response.",
        ])
