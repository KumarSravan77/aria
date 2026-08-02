from server.correlation.incident_analyzer import IncidentAnalyzer
from server.collaboration.ai_teammate import AITeammate
from server.collaboration.rca_writer import generate_rca_draft


def test_analyzer_returns_canonical_and_legacy_keys():
    analysis = IncidentAnalyzer().analyze({
        "service": "checkout-api",
        "symptoms": ["high latency"],
        "signals": {"cpu_percent": 85, "error_rate_percent": 6, "recent_deployment": True},
    })

    assert analysis["evidence"]
    assert analysis["findings"] == analysis["evidence"]
    assert analysis["probable_cause"] == analysis["likely_cause"]
    assert analysis["summary"]


def test_ai_teammate_uses_analyzer_evidence():
    analysis = IncidentAnalyzer().analyze({
        "service": "checkout-api",
        "symptoms": ["high latency"],
        "signals": {"cpu_percent": 85},
    })

    message = AITeammate().investigation_update(analysis, {})

    assert "CPU saturation detected" in message
    assert "resource_saturation" in message


def test_rca_uses_analyzer_probable_cause_and_summary():
    analysis = IncidentAnalyzer().analyze({
        "service": "checkout-api",
        "symptoms": ["high latency"],
        "signals": {"cpu_percent": 85},
    })
    rca = generate_rca_draft(
        {"incident_id": "INC-1", "service": "checkout-api", "severity": "P1", "environment": "dev"},
        [],
        analysis,
    )

    assert "Incident investigation is in progress" not in rca
    assert "Unknown / pending confirmation" not in rca
    assert "resource_saturation" in rca
