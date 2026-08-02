from server.intake.alertmanager_parser import normalize_alertmanager_payload


def test_alertmanager_parser_normalizes_alerts():
    payload = {"status": "firing", "alerts": [{"labels": {"alertname": "HighLatency", "service": "checkout-api", "severity": "critical"}, "annotations": {"summary": "p95 latency high"}}]}
    items = normalize_alertmanager_payload(payload)
    assert len(items) == 1
    assert items[0]["service"] == "checkout-api"
    assert items[0]["severity"] == "P1"
    assert "high latency" in items[0]["symptoms"]
