from __future__ import annotations
from dataclasses import dataclass

@dataclass
class PatchGenerator:
    def helm_values_patch(self, service: str, issue: str) -> dict:
        if "latency" in issue.lower() or "scale" in issue.lower():
            patch = {
                "replicaCount": 3,
                "resources": {
                    "requests": {"cpu": "250m", "memory": "256Mi"},
                    "limits": {"cpu": "500m", "memory": "512Mi"},
                },
            }
        else:
            patch = {"annotations": {"aria/review-required": "true"}}
        return {"file": f"charts/{service}/values.yaml", "patch": patch}

    def rollback_patch(self, service: str, previous_revision: str = "previous-stable") -> dict:
        return {
            "file": f"overlays/prod/{service}/kustomization.yaml",
            "patch": {"images": [{"name": service, "newTag": previous_revision}]},
        }
