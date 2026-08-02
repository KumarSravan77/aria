from __future__ import annotations
from typing import Any


def generate_pdb(service: str, namespace: str = "demo",
                 min_available: int | None = None,
                 max_unavailable: str | None = None) -> dict[str, Any]:
    spec: dict[str, Any] = {"selector": {"matchLabels": {"app": service}}}
    if max_unavailable is not None:
        spec["maxUnavailable"] = max_unavailable
    else:
        spec["minAvailable"] = min_available if min_available is not None else 1
    return {
        "apiVersion": "policy/v1",
        "kind": "PodDisruptionBudget",
        "metadata": {"name": f"{service}-pdb", "namespace": namespace,
                     "labels": {"app.kubernetes.io/managed-by": "aria"}},
        "spec": spec,
    }
