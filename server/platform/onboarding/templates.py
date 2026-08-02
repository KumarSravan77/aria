from __future__ import annotations

from typing import Any, Dict


class PlatformTemplateGenerator:
    """Generates self-service golden-path artifacts as deterministic text blocks."""

    def generate(self, service_id: str, service_profile: Dict[str, Any]) -> Dict[str, str]:
        language = service_profile.get("language", "unknown")
        tier = service_profile.get("tier", "tier2")
        return {
            "kubernetes/helm-values.yaml": f"""service:\n  name: {service_id}\n  tier: {tier}\n  language: {language}\nprobes:\n  liveness: /health/live\n  readiness: /health/ready\nresources:\n  requests:\n    cpu: 250m\n    memory: 512Mi\n  limits:\n    cpu: 1000m\n    memory: 1Gi\npdb:\n  enabled: true\nautoscaling:\n  enabled: true\n  minReplicas: 2\n  maxReplicas: 10\n""",
            "cicd/pipeline-template.yaml": f"""service: {service_id}\nstages:\n  - build\n  - unit_tests\n  - security_scan\n  - sbom\n  - image_sign\n  - deploy_canary\n  - rollback_guard\n""",
            "observability/otel-collector.yaml": f"""service:\n  telemetry:\n    otel: true\n    serviceName: {service_id}\n    propagation: tracecontext,baggage\nprocessors:\n  batch: {{}}\n  memory_limiter: {{}}\n  attributes/drop_high_cardinality: {{}}\n""",
            "slo/service-slo.yaml": f"""service: {service_id}\nobjectives:\n  availability: 99.9\n  latency_p95_ms: 300\n  error_rate_percent: 0.1\nburn_rates:\n  fast: 2_percent_in_1h\n  medium: 5_percent_in_6h\n  slow: 10_percent_in_3d\n""",
            "runbooks/operational-runbook.md": f"""# {service_id} Operational Runbook\n\n## Owners\nTBD\n\n## Dashboards\nTBD\n\n## Common Failure Modes\n- CrashLoopBackOff\n- High 5xx\n- Latency regression\n- Dependency failure\n\n## Rollback\nUse the approved pipeline rollback stage.\n""",
        }
