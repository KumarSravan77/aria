from __future__ import annotations

SCENARIOS = [
    {
        "id": "cm-trade-latency",
        "domain": "capital_markets",
        "service": "trade-execution-api",
        "severity": "P1",
        "signals": ["latency", "trading_hours", "slo_burn", "tempo_trace_spike"],
        "expected_agents": ["metrics", "traces", "rag", "rca"],
        "business_impact": "order execution latency during trading window",
    },
    {
        "id": "bank-payment-timeout",
        "domain": "retail_banking",
        "service": "payment-processing-api",
        "severity": "P1",
        "signals": ["database", "timeout", "payment_latency", "slo_burn"],
        "expected_agents": ["metrics", "logs", "traces", "rag", "rca"],
        "business_impact": "customer payment failures",
    },
    {
        "id": "wealth-ai-latency",
        "domain": "wealth_management",
        "service": "investment-recommendation-engine",
        "severity": "P2",
        "signals": ["model_latency", "ai_ml_workload", "historical"],
        "expected_agents": ["metrics", "thanos", "rag", "rca"],
        "business_impact": "advisor recommendation delay",
    },
    {
        "id": "fraud-kafka-lag",
        "domain": "aml_fraud",
        "service": "fraud-detection-engine",
        "severity": "P1",
        "signals": ["kafka_lag", "streaming", "fraud_detection_delay"],
        "expected_agents": ["metrics", "logs", "rag", "rca"],
        "business_impact": "delayed fraud decisions",
    },
    {
        "id": "insurance-doc-ai-failure",
        "domain": "insurance",
        "service": "document-processing-ai",
        "severity": "P2",
        "signals": ["job_failure", "pod_crashloop", "ai_pipeline"],
        "expected_agents": ["metrics", "logs", "kubernetes_troubleshooter", "rag"],
        "business_impact": "claims document processing delay",
    },
    {
        "id": "retail-checkout-canary",
        "domain": "retail_ecommerce",
        "service": "checkout-api",
        "severity": "P1",
        "signals": ["canary", "istio", "latency", "5xx"],
        "expected_agents": ["metrics", "logs", "istio", "rag", "rca"],
        "business_impact": "checkout failures and revenue impact",
    },
    {
        "id": "aml-model-drift",
        "domain": "aml_fraud",
        "service": "aml-feature-pipeline",
        "severity": "P1",
        "signals": ["model_drift", "feature_distribution_shift", "false_negative_rate_increase"],
        "expected_agents": ["metrics", "logs", "rag", "rca"],
        "business_impact": "increased undetected fraud transactions",
    },
]


def list_scenarios(domain: str | None = None) -> list[dict]:
    if not domain:
        return SCENARIOS
    return [s for s in SCENARIOS if s["domain"] == domain]
