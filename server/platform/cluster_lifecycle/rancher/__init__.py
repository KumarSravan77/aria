from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class RancherClient:
    """Rancher multi-cluster management API adapter."""
    base_url: str = ""
    token: str | None = None
    timeout_seconds: int = 10

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def clusters(self) -> dict[str, Any]:
        if not self.base_url or not self.token:
            return {
                "available": False,
                "message": "Set RANCHER_URL and RANCHER_TOKEN to enable multi-cluster management.",
            }
        try:
            r = requests.get(f"{self.base_url.rstrip('/')}/v3/clusters",
                             headers=self._headers(), timeout=self.timeout_seconds)
            r.raise_for_status()
            items = r.json().get("data", [])
            return {
                "available": True,
                "clusters": [{"id": c.get("id"), "name": c.get("name"),
                               "state": c.get("state")} for c in items],
            }
        except Exception as exc:
            return {"available": False, "error": str(exc)}
