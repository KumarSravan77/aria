SYNTHETIC_INCIDENTS = [
    {
        "id": "syn-001",
        "service": "checkout-api",
        "scenario": "deployment_regression",
        "symptoms": ["latency_spike", "5xx_increase", "recent_deployment"],
        "expected_root_cause": "deployment_regression",
        "safe_remediation": "rollback_or_pause_rollout",
    },
    {
        "id": "syn-002",
        "service": "payment-api",
        "scenario": "database_timeout",
        "symptoms": ["db_timeout", "slow_trace_span", "slo_burn"],
        "expected_root_cause": "database_connection_pool_exhaustion",
        "safe_remediation": "scale_pool_or_rollback",
    },
    {
        "id": "syn-003",
        "service": "checkout-api",
        "scenario": "dns_failure",
        "symptoms": ["dns_errors", "connection_failures"],
        "expected_root_cause": "service_discovery_failure",
        "safe_remediation": "fix_service_dns_or_restart_coredns",
    },
]
