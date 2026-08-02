from __future__ import annotations
from typing import Any


def generate_topology_spread(service: str, replicas: int = 3, max_skew: int = 1) -> dict[str, Any]:
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": service, "labels": {"app": service, "app.kubernetes.io/managed-by": "aria"}},
        "spec": {
            "replicas": replicas,
            "selector": {"matchLabels": {"app": service}},
            "template": {
                "metadata": {"labels": {"app": service}},
                "spec": {
                    "topologySpreadConstraints": [
                        {"maxSkew": max_skew, "topologyKey": "topology.kubernetes.io/zone",
                         "whenUnsatisfiable": "DoNotSchedule",
                         "labelSelector": {"matchLabels": {"app": service}}},
                        {"maxSkew": max_skew, "topologyKey": "kubernetes.io/hostname",
                         "whenUnsatisfiable": "ScheduleAnyway",
                         "labelSelector": {"matchLabels": {"app": service}}},
                    ],
                    "affinity": {"podAntiAffinity": {"preferredDuringSchedulingIgnoredDuringExecution": [
                        {"weight": 100, "podAffinityTerm": {
                            "labelSelector": {"matchLabels": {"app": service}},
                            "topologyKey": "kubernetes.io/hostname"}}
                    ]}},
                    "containers": [{"name": service, "image": f"{service}:latest"}],
                },
            },
        },
    }
