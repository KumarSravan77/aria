from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class PrometheusClient:
    base_url: str = "http://localhost:9090"
    timeout_seconds: int = 10

    def query(self, promql: str) -> dict[str, Any]:
        try:
            r = requests.get(f"{self.base_url.rstrip('/')}/api/v1/query", params={"query": promql}, timeout=self.timeout_seconds)
            r.raise_for_status()
            return {"available": True, "query": promql, "result": r.json()}
        except Exception as exc:
            return {"available": False, "query": promql, "error": str(exc), "result": None}
