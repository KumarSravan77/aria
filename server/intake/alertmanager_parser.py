from hashlib import sha1
from server.utils_time import utc_now


def normalize_alertmanager_payload(payload: dict) -> list[dict]:
    alerts = payload.get("alerts", []) or []
    normalized = []
    for idx, alert in enumerate(alerts):
        labels = alert.get("labels", {}) or {}
        annotations = alert.get("annotations", {}) or {}
        alertname = labels.get("alertname", "UnknownAlert")
        service = labels.get("service") or labels.get("app") or labels.get("deployment") or "unknown-service"
        environment = labels.get("environment") or labels.get("env") or "dev"
        severity = labels.get("severity", "warning")
        now = utc_now()
        starts_at = alert.get("startsAt") or now.isoformat()
        raw_key = f"{alertname}:{service}:{environment}:{severity}"
        dedupe_key = sha1(raw_key.encode()).hexdigest()[:16]
        incident_id = f"INC-{now.strftime('%Y%m%d')}-{dedupe_key[:6]}"
        normalized.append({
            "incident_id": incident_id,
            "source": "alertmanager",
            "alert_name": alertname,
            "service": service,
            "environment": environment,
            "severity": "P1" if severity in {"critical", "page", "p1"} else "P2",
            "status": payload.get("status", "firing"),
            "starts_at": starts_at,
            "summary": annotations.get("summary") or annotations.get("description") or alertname,
            "description": annotations.get("description", ""),
            "labels": labels,
            "annotations": annotations,
            "dedupe_key": dedupe_key,
            "symptoms": _infer_symptoms(alertname, annotations),
            "signals": {},
            "user": {"role": "sre", "team": labels.get("team", "platform")},
        })
    return normalized


def _infer_symptoms(alertname: str, annotations: dict) -> list[str]:
    text = f"{alertname} {annotations}".lower()
    symptoms = []
    if "latency" in text or "p95" in text: symptoms.append("high latency")
    if "5xx" in text or "error" in text: symptoms.append("increased errors")
    if "cpu" in text: symptoms.append("high cpu")
    if "memory" in text or "oom" in text: symptoms.append("memory pressure")
    if "crash" in text: symptoms.append("pod crash")
    return symptoms or ["alert fired"]
