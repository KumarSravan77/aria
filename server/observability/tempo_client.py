from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class TempoClient:
    base_url: str = "http://localhost:3200"
    timeout_seconds: int = 10

    def search_service_traces(self, service: str) -> dict[str, Any]:
        # Tempo deployments differ by version; this is intentionally a thin adapter boundary.
        query = f'{{ resource.service.name = "{service}" }}'
        try:
            r = requests.get(f"{self.base_url.rstrip('/')}/api/search", params={"q": query}, timeout=self.timeout_seconds)
            r.raise_for_status()
            return {"available": True, "service": service, "result": r.json()}
        except Exception as exc:
            return {"available": False, "service": service, "error": str(exc), "result": None}
