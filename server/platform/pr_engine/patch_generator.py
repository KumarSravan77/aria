from __future__ import annotations

from typing import Any, Dict, List


class RemediationPatchGenerator:
    """Generates safe PR patch suggestions from ARIA findings.

    This does not write to Git. It returns patch candidates for review/approval.
    """

    def generate(self, review: Dict[str, Any]) -> Dict[str, Any]:
        candidates: List[Dict[str, Any]] = []
        for finding in review.get("findings", []):
            recommendation = finding.get("recommendation", {})
            if recommendation.get("remediation_type") not in {"auto_fix_candidate", "approval_required"}:
                continue
            fid = finding.get("id")
            if fid == "k8s-missing-probes":
                candidates.append({
                    "finding_id": fid,
                    "target": "helm/values.yaml or k8s/deployment.yaml",
                    "patch_type": "kubernetes_probe_baseline",
                    "requires_approval": finding.get("severity") in {"P0", "P1"},
                    "suggested_change": {
                        "readinessProbe": {"httpGet": {"path": "/health/ready", "port": "http"}, "initialDelaySeconds": 10, "periodSeconds": 10},
                        "livenessProbe": {"httpGet": {"path": "/health/live", "port": "http"}, "initialDelaySeconds": 30, "periodSeconds": 20},
                    },
                })
            elif fid == "k8s-missing-pdb":
                candidates.append({
                    "finding_id": fid,
                    "target": "k8s/pdb.yaml or helm/templates/pdb.yaml",
                    "patch_type": "pod_disruption_budget",
                    "requires_approval": finding.get("severity") in {"P0", "P1"},
                    "suggested_change": {"minAvailable": "50%"},
                })
            elif fid and fid.startswith("otel-"):
                candidates.append({
                    "finding_id": fid,
                    "target": "service deployment env / OTel Collector config",
                    "patch_type": "otel_standardization",
                    "requires_approval": finding.get("severity") in {"P0", "P1"},
                    "suggested_change": {"OTEL_SERVICE_NAME": review.get("service_id"), "OTEL_PROPAGATORS": "tracecontext,baggage"},
                })
            elif fid and fid.startswith("tf-drift"):
                candidates.append({
                    "finding_id": fid,
                    "target": "terraform module/state workflow",
                    "patch_type": "terraform_drift_remediation_plan",
                    "requires_approval": True,
                    "suggested_change": "Decide import vs revert vs update code; never auto-apply drift changes without approval.",
                })
        return {"service_id": review.get("service_id"), "patch_candidates": candidates, "mode": "dry_run"}
