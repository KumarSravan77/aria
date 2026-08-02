from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class ArgoCDClient:
    base_url: str = "http://localhost:8082"
    token: str | None = None
    timeout_seconds: int = 20

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def list_apps(self) -> dict[str, Any]:
        try:
            r = requests.get(f"{self.base_url.rstrip('/')}/api/v1/applications", headers=self._headers(), timeout=self.timeout_seconds)
            r.raise_for_status()
            return {"available": True, "apps": r.json()}
        except Exception as exc:
            return {"available": False, "error": str(exc), "apps": []}

    def sync_app(self, app_name: str, revision: str | None = None, dry_run: bool = True) -> dict[str, Any]:
        if dry_run:
            return {"requested": "argocd_sync", "app": app_name, "revision": revision, "dry_run": True}
        body: dict[str, Any] = {"prune": False, "dryRun": False}
        if revision:
            body["revision"] = revision
        try:
            r = requests.post(f"{self.base_url.rstrip('/')}/api/v1/applications/{app_name}/sync", json=body, headers=self._headers(), timeout=self.timeout_seconds)
            r.raise_for_status()
            return {"requested": "argocd_sync", "app": app_name, "revision": revision, "dry_run": False, "result": r.json()}
        except Exception as exc:
            return {"requested": "argocd_sync", "app": app_name, "revision": revision, "dry_run": False, "error": str(exc)}
