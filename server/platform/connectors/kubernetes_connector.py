from __future__ import annotations

from typing import Any, Dict, List


class KubernetesConnector:
    """Normalizes Kubernetes object snapshots into ARIA service profile fields."""

    def collect_from_objects(self, objects: List[Dict[str, Any]]) -> Dict[str, Any]:
        workloads = [o for o in objects if o.get("kind") in {"Deployment", "StatefulSet", "DaemonSet"}]
        services = [o for o in objects if o.get("kind") == "Service"]
        pdbs = [o for o in objects if o.get("kind") == "PodDisruptionBudget"]
        network_policies = [o for o in objects if o.get("kind") == "NetworkPolicy"]
        profile = {
            "workload_count": len(workloads),
            "service_count": len(services),
            "network_policy_count": len(network_policies),
            "readinessProbe": False,
            "livenessProbe": False,
            "startupProbe": False,
            "pdb": bool(pdbs),
            "resources": {},
            "topologySpreadConstraints": False,
            "securityContext": False,
        }
        for obj in workloads:
            spec = obj.get("spec", {}).get("template", {}).get("spec", {})
            containers = spec.get("containers", [])
            profile["topologySpreadConstraints"] = profile["topologySpreadConstraints"] or bool(spec.get("topologySpreadConstraints"))
            profile["securityContext"] = profile["securityContext"] or bool(spec.get("securityContext"))
            for container in containers:
                profile["readinessProbe"] = profile["readinessProbe"] or bool(container.get("readinessProbe"))
                profile["livenessProbe"] = profile["livenessProbe"] or bool(container.get("livenessProbe"))
                profile["startupProbe"] = profile["startupProbe"] or bool(container.get("startupProbe"))
                resources = container.get("resources", {})
                if resources.get("requests") or resources.get("limits"):
                    profile["resources"] = resources
        return {"status": "ok", "kubernetes": profile}
