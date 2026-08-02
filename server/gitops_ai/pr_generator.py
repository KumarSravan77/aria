from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import os

@dataclass
class PullRequestGenerator:
    provider: str = "github"

    def create(self, title: str, body: str, files: list[dict[str, Any]], dry_run: bool = True) -> dict[str, Any]:
        live_enabled = os.getenv("GITOPS_PR_LIVE_ENABLED", "false").lower() == "true"
        if dry_run or not live_enabled:
            return {
                "created": False,
                "dry_run": True,
                "provider": self.provider,
                "title": title,
                "files": [f["file"] for f in files],
                "safety": "PR proposal only; merge requires human approval",
            }
        return {
            "created": False,
            "dry_run": False,
            "implemented": False,
            "message": "Live provider client not configured. Keep disabled until GitHub/GitLab token and repo are configured.",
        }
