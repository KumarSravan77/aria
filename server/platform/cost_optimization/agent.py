from __future__ import annotations

from typing import Any, Dict, List

from server.platform.spec_harness.models import Evidence, Finding


class CostOptimizationAgent:
    name = "cost-optimization-agent"

    def review(self, service_profile: Dict[str, Any]) -> List[Finding]:
        cost = service_profile.get("cost", {}) or {}
        obs = service_profile.get("observability", {}) or {}
        findings: List[Finding] = []
        if cost.get("monthly_spend_usd", 0) and not cost.get("owner_tag"):
            findings.append(Finding("cost-missing-owner-tag","Cost governance gap: owner tag missing","cost","P2",[Evidence("service_profile","cost.owner_tag",str(cost.get("owner_tag")),"defined",collector=self.name)],{"user_impact":"Cost attribution is unclear.","business_impact":"Chargeback/showback accuracy is reduced.","technical_impact":"Resource metadata is incomplete."},{"summary":"Add standard owner/application/environment tags.","remediation_type":"auto_fix_candidate"},{"score":0.8,"explanation":"Spend is present but owner tag missing."}))
        if obs.get("otel", {}).get("high_cardinality_attributes"):
            findings.append(Finding("cost-telemetry-cardinality-risk","Cost risk: high-cardinality telemetry attributes may increase observability spend","cost","P1",[Evidence("service_profile","observability.otel.high_cardinality_attributes",str(obs.get("otel", {}).get("high_cardinality_attributes")),"empty list",collector=self.name)],{"user_impact":"Dashboards and queries may become slower or noisier.","business_impact":"Telemetry cost may grow unexpectedly.","technical_impact":"Metric/span dimensions may create cardinality explosion."},{"summary":"Remove or filter high-cardinality dimensions at instrumentation or collector level.","remediation_type":"auto_fix_candidate"},{"score":0.86,"explanation":"High-cardinality attributes are declared."}))
        if not cost.get("budget_alerts"):
            findings.append(Finding("cost-missing-budget-alerts","Cost governance gap: budget alerts missing","cost","P3",[Evidence("service_profile","cost.budget_alerts",str(cost.get("budget_alerts")),"true",collector=self.name)],{"user_impact":"No direct user impact expected.","business_impact":"Unexpected spend may not be detected early.","technical_impact":"Cost monitoring control is missing."},{"summary":"Add budget and anomaly alerts for the service/environment.","remediation_type":"manual"},{"score":0.75,"explanation":"Budget alerts not declared."}))
        return findings
