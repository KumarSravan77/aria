from __future__ import annotations

from server.platform.connectors.kubernetes_connector import KubernetesConnector as _KubernetesConnector


class KubernetesConnector(_KubernetesConnector):
    """Compatibility wrapper exposing normalize_resources()."""

    def normalize_resources(self, resources: list[dict]) -> dict:
        collected = self.collect_from_objects(resources).get("kubernetes", {})
        kinds = {r.get("kind") for r in resources}
        return {
            "has_deployment": "Deployment" in kinds,
            "has_statefulset": "StatefulSet" in kinds,
            "has_daemonset": "DaemonSet" in kinds,
            "has_hpa": "HorizontalPodAutoscaler" in kinds,
            "has_service": "Service" in kinds,
            "has_pdb": "PodDisruptionBudget" in kinds or bool(collected.get("pdb")),
            "probes_configured": bool(collected.get("readinessProbe") and collected.get("livenessProbe")),
            "startup_probe_configured": bool(collected.get("startupProbe")),
            "resources_configured": bool(collected.get("resources")),
            "topology_spread_configured": bool(collected.get("topologySpreadConstraints")),
            "raw": collected,
        }
