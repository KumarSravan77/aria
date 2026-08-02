from __future__ import annotations
from typing import Any


def traffic_failover_manifest(service: str, primary_cluster: str, standby_cluster: str,
                               namespace: str = "demo") -> dict[str, Any]:
    return {
        "virtual_service": {
            "apiVersion": "networking.istio.io/v1beta1", "kind": "VirtualService",
            "metadata": {"name": f"{service}-failover", "namespace": namespace},
            "spec": {"hosts": [service], "http": [{"route": [
                {"destination": {"host": service, "subset": "primary"}, "weight": 100},
                {"destination": {"host": service, "subset": "standby"}, "weight": 0},
            ], "retries": {"attempts": 3, "perTryTimeout": "5s", "retryOn": "5xx,reset,connect-failure"}}]},
        },
        "destination_rule": {
            "apiVersion": "networking.istio.io/v1beta1", "kind": "DestinationRule",
            "metadata": {"name": f"{service}-dr", "namespace": namespace},
            "spec": {
                "host": service,
                "trafficPolicy": {"outlierDetection": {"consecutive5xxErrors": 5, "interval": "30s", "baseEjectionTime": "30s"}},
                "subsets": [{"name": "primary", "labels": {"cluster": primary_cluster}},
                            {"name": "standby", "labels": {"cluster": standby_cluster}}],
            },
        },
        "failover_steps": [
            f"Confirm {primary_cluster} is unhealthy via health checks and SLO burn",
            f"Update VirtualService weight: primary=0, standby=100",
            "Verify traffic is routed to standby cluster",
            f"Repair {primary_cluster} and validate before shifting traffic back",
        ],
        "safety_boundary": "Traffic failover affects all users. Requires ReBAC, approval, and war-room coordination.",
    }
