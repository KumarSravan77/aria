#!/usr/bin/env python3
"""Build a GitHub Actions matrix from ARIA's multi-application catalog."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REQUIRED = {"service_id", "app_path", "language"}


def build_matrix(catalog_path: str) -> dict:
    path = Path(catalog_path)
    data = yaml.safe_load(path.read_text()) if path.exists() else {"applications": []}
    apps = data.get("applications", []) or []
    include = []
    for app in apps:
        missing = sorted(REQUIRED - set(app))
        if missing:
            raise ValueError(f"Application entry missing required fields {missing}: {app}")
        include.append(
            {
                "service_id": app["service_id"],
                "app_path": app["app_path"],
                "language": app["language"],
                "dockerfile": app.get("dockerfile", f"{app['app_path']}/Dockerfile"),
                "service_profile": app.get("service_profile", "examples/self_service/service_review_request.json"),
                "tier": app.get("tier", "tier2"),
                "owner_team": app.get("owner_team", "platform"),
            }
        )
    return {"include": include}


if __name__ == "__main__":
    matrix = build_matrix(sys.argv[1] if len(sys.argv) > 1 else "config/applications.yaml")
    print(f"matrix={json.dumps(matrix, separators=(',', ':'))}")
