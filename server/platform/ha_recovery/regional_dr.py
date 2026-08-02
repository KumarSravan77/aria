from __future__ import annotations
from typing import Any


def regional_dr_plan(service: str, primary_region: str = "us-east-1",
                     standby_region: str = "eu-west-1",
                     rto_minutes: int = 30, rpo_minutes: int = 15) -> dict[str, Any]:
    return {
        "service": service, "primary_region": primary_region, "standby_region": standby_region,
        "objectives": {"rto_minutes": rto_minutes, "rpo_minutes": rpo_minutes},
        "phases": {
            "detect": ["Alertmanager/ARIA detects P1 in primary region",
                       "Confirm blast radius and customer impact",
                       "Declare regional incident and engage incident commander"],
            "data_recovery": [f"Verify Velero backup is current in {standby_region}",
                              f"Initiate Postgres PITR or replica promotion in {standby_region}",
                              "Validate data integrity before traffic shift"],
            "traffic_failover": [f"Update DNS/Route53/Cloudflare to {standby_region}",
                                 f"Update Istio VirtualService: {primary_region}=0, {standby_region}=100",
                                 "Validate health checks pass in standby region"],
            "application_recovery": [f"Bootstrap Argo CD in {standby_region} cluster if not already running",
                                     "Sync all application manifests from GitOps repo",
                                     "Validate all services reach Healthy status"],
            "validation": ["Run full smoke test suite against standby region",
                          "Confirm SLO burn rate recovers",
                          "Record actual RTO/RPO via ARIA /recovery/rto-rpo",
                          "Create incident RCA and update DR runbook"],
        },
        "safety_boundary": "Regional failover is a major operation. All steps require incident-commander approval and full audit logging.",
    }


def dr_readiness_checklist(service: str, namespace: str = "demo") -> dict[str, Any]:
    return {
        "service": service, "namespace": namespace,
        "checklist": [
            {"item": "Minimum 3 replicas with PDB configured", "category": "availability"},
            {"item": "Topology spread across 3+ availability zones", "category": "availability"},
            {"item": "Velero backup schedule active with cross-region replication", "category": "data"},
            {"item": "Postgres streaming replica in standby region", "category": "data"},
            {"item": "Argo CD app-of-apps GitOps repo ready for standby bootstrap", "category": "recovery"},
            {"item": "Istio VirtualService and DestinationRule configured for failover", "category": "traffic"},
            {"item": "DNS/Gateway failover tested in last 30 days", "category": "traffic"},
            {"item": "RTO/RPO targets documented and last measured", "category": "objectives"},
            {"item": "DR runbook reviewed and accessible in ARIA RAG", "category": "documentation"},
            {"item": "On-call escalation chain tested (no bottlenecks)", "category": "people"},
        ],
        "instructions": "Score each item as met/unmet. Run /recovery/validate after a DR drill to measure actual RTO/RPO.",
    }
