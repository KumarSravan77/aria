"""Static project context used by AI workflows.

This file is intentionally simple. It gives API routes, prompts, or future
agent workflows a single place to load project rules without scraping the
entire repository.
"""

PROJECT_CONTEXT = {
    "name": "ARIA — Autonomous Resilience Intelligence Assistant",
    "purpose": "AI-native SRE incident investigation and self-healing platform",
    "core_components": [
        "FastAPI investigator API",
        "correlation engine",
        "RAG runbook retrieval",
        "policy validator",
        "Kubernetes self-healing executor",
        "Prometheus/Grafana observability",
        "GoAlert paging",
    ],
    "safety_rules": [
        "LLM must not execute arbitrary shell commands",
        "All remediation must pass policy validation",
        "High-risk actions require approval",
        "No destructive autonomous actions",
        "Every incident type needs runbook, payload, and tests",
    ],
}
