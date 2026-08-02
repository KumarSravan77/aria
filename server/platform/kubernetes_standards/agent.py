from __future__ import annotations

from typing import Any, Dict, List

from server.platform.spec_harness.models import Evidence, Finding


class KubernetesStandardsAgent:
    """Checks a service profile against ARIA Kubernetes golden-path standards."""

    name = "kubernetes-standards-agent"

    def review(self, service_profile: Dict[str, Any]) -> List[Finding]:
        findings: List[Finding] = []
        k8s = service_profile.get("kubernetes", {}) or {}
        tier = (service_profile.get("tier") or service_profile.get("service_tier") or "tier2").lower()

        def evidence(path: str, observed: Any, expected: str) -> List[Evidence]:
            return [Evidence(source="service_profile", path=path, observed=str(observed), expected=expected, collector=self.name)]

        if not k8s.get("readinessProbe") or not k8s.get("livenessProbe"):
            findings.append(Finding(
                id="k8s-missing-probes",
                title="Kubernetes standards gap: missing liveness/readiness probes",
                category="kubernetes",
                severity="P1",
                evidence=evidence("kubernetes.readinessProbe/livenessProbe", {"readinessProbe": k8s.get("readinessProbe"), "livenessProbe": k8s.get("livenessProbe")}, "both true"),
                impact={"user_impact":"Traffic may be routed to unhealthy pods.","business_impact":"Availability and release safety may be reduced.","technical_impact":"Kubernetes cannot reliably detect startup or runtime health."},
                recommendation={"summary":"Add livenessProbe and readinessProbe to the workload template.","remediation_type":"auto_fix_candidate"},
                confidence={"score":0.9,"explanation":"Probe fields are missing or false in the service profile."},
            ))
        if not k8s.get("startupProbe") and tier in ("tier0", "tier1"):
            findings.append(Finding(
                id="k8s-missing-startup-probe",
                title="Kubernetes standards gap: missing startupProbe for critical service",
                category="kubernetes",
                severity="P2",
                evidence=evidence("kubernetes.startupProbe", k8s.get("startupProbe"), "true for tier0/tier1"),
                impact={"user_impact":"Cold starts may cause avoidable restarts.","business_impact":"Deployments can become unstable during traffic spikes.","technical_impact":"Liveness checks may kill slow-starting containers."},
                recommendation={"summary":"Add startupProbe for services with slow JVM/model/framework initialization.","remediation_type":"auto_fix_candidate"},
                confidence={"score":0.78,"explanation":"Critical service does not declare startupProbe."},
            ))
        if not k8s.get("pdb"):
            findings.append(Finding(
                id="k8s-missing-pdb",
                title="Kubernetes standards gap: missing PodDisruptionBudget",
                category="kubernetes",
                severity="P2" if tier not in ("tier0", "tier1") else "P1",
                evidence=evidence("kubernetes.pdb", k8s.get("pdb"), "true"),
                impact={"user_impact":"Voluntary disruptions may reduce availability.","business_impact":"Maintenance windows may carry higher downtime risk.","technical_impact":"No disruption guard exists for replicas during node drains."},
                recommendation={"summary":"Add a PDB aligned to service tier and replica count.","remediation_type":"auto_fix_candidate"},
                confidence={"score":0.82,"explanation":"PDB field missing from service profile."},
            ))
        resources = k8s.get("resources", {}) or {}
        if not resources.get("requests") or not resources.get("limits"):
            findings.append(Finding(
                id="k8s-missing-requests-limits",
                title="Kubernetes standards gap: CPU/memory requests or limits missing",
                category="kubernetes",
                severity="P1",
                evidence=evidence("kubernetes.resources", resources, "requests and limits configured"),
                impact={"user_impact":"Pods may be throttled, evicted, or starve other workloads.","business_impact":"Capacity planning and cost control are weaker.","technical_impact":"Scheduler and autoscaler signals are incomplete."},
                recommendation={"summary":"Set CPU/memory requests and limits using baseline load-test data.","remediation_type":"auto_fix_candidate"},
                confidence={"score":0.88,"explanation":"Requests or limits are not present."},
            ))
        if tier in ("tier0", "tier1") and not k8s.get("topologySpreadConstraints"):
            findings.append(Finding(
                id="k8s-missing-topology-spread",
                title="Kubernetes standards gap: topology spread not configured for critical service",
                category="kubernetes",
                severity="P2",
                evidence=evidence("kubernetes.topologySpreadConstraints", k8s.get("topologySpreadConstraints"), "configured for tier0/tier1"),
                impact={"user_impact":"Zone or node failures may impact more replicas.","business_impact":"High-availability expectations may not be met.","technical_impact":"Replicas may concentrate on the same failure domain."},
                recommendation={"summary":"Add topologySpreadConstraints or anti-affinity for critical replicas.","remediation_type":"auto_fix_candidate"},
                confidence={"score":0.76,"explanation":"Critical service lacks topology spreading metadata."},
            ))
        return findings
