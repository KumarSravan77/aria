from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .loader import SpecLoader
from .models import ServiceSpecContext


GRADE_ORDER = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}


@dataclass
class SpecEvaluationResult:
    service_id: str
    golden_path: str
    required_capabilities: List[str]
    satisfied_capabilities: List[str]
    missing_capabilities: List[str]
    production_gates: Dict[str, Any]
    policy_gates: Dict[str, Any]
    decision_rules_loaded: int
    remediation_specs_loaded: int
    passed: bool
    findings: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_id": self.service_id,
            "golden_path": self.golden_path,
            "required_capabilities": self.required_capabilities,
            "satisfied_capabilities": self.satisfied_capabilities,
            "missing_capabilities": self.missing_capabilities,
            "production_gates": self.production_gates,
            "policy_gates": self.policy_gates,
            "decision_rules_loaded": self.decision_rules_loaded,
            "remediation_specs_loaded": self.remediation_specs_loaded,
            "passed": self.passed,
            "findings": self.findings,
        }


class SpecDrivenEvaluator:
    """Evaluates a service against golden-path and governance specs."""

    def __init__(self, loader: SpecLoader | None = None) -> None:
        self.loader = loader or SpecLoader()

    def build_context(self, service_id: str) -> ServiceSpecContext:
        service_profile = self.loader.load_service_profile(service_id)
        golden_path_name = service_profile.get("service", {}).get("golden_path")
        golden_path = self.loader.load_golden_path(golden_path_name)
        return ServiceSpecContext(
            service_profile=service_profile,
            golden_path=golden_path,
            capabilities=self.loader.load_collection("capabilities"),
            policies=self.loader.load_collection("policies"),
            decisions=self.loader.load_collection("decisions"),
            remediations=self.loader.load_collection("remediations"),
        )

    def evaluate_service(self, service_id: str) -> SpecEvaluationResult:
        ctx = self.build_context(service_id)
        gp = ctx.golden_path.get("golden_path", {})
        required = gp.get("required_capabilities", []) or ctx.golden_path.get("required_capabilities", [])
        available = {cap.get("capability", {}).get("name") for cap in ctx.capabilities}
        missing = [name for name in required if name not in available]
        satisfied = [name for name in required if name in available]
        findings: List[Dict[str, Any]] = []
        for name in missing:
            findings.append({
                "id": f"spec-missing-{name}",
                "title": f"Missing required platform capability: {name}",
                "category": "onboarding",
                "severity": "P1",
                "recommendation": "Add capability spec and implementation before production onboarding.",
            })
        policy_gates: Dict[str, Any] = {}
        for policy in ctx.policies:
            policy_name = policy.get("policy", {}).get("name", "unknown")
            policy_gates[policy_name] = {
                "mutation_rules": policy.get("mutation_rules", {}),
                "release_gates": policy.get("release_gates", {}),
            }
        return SpecEvaluationResult(
            service_id=ctx.service_id,
            golden_path=gp.get("name", "unknown"),
            required_capabilities=required,
            satisfied_capabilities=satisfied,
            missing_capabilities=missing,
            production_gates=gp.get("production_gates", {}) or ctx.golden_path.get("production_gates", {}),
            policy_gates=policy_gates,
            decision_rules_loaded=sum(len(spec.get("decisions", {})) for spec in ctx.decisions),
            remediation_specs_loaded=sum(len(spec.get("remediations", {})) for spec in ctx.remediations),
            passed=not missing,
            findings=findings,
        )
