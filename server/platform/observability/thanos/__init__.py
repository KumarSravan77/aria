from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class ThanosClient:
    """Long-term and multi-cluster Prometheus metrics via Thanos Query API."""
    base_url: str = "http://localhost:10902"
    timeout_seconds: int = 15

    def query(self, promql: str) -> dict[str, Any]:
        try:
            r = requests.get(f"{self.base_url.rstrip('/')}/api/v1/query",
                             params={"query": promql}, timeout=self.timeout_seconds)
            r.raise_for_status()
            return {"available": True, "query": promql, "result": r.json()}
        except Exception as exc:
            return {"available": False, "query": promql, "error": str(exc), "result": None}

    def query_range(self, promql: str, start: str, end: str, step: str = "5m") -> dict[str, Any]:
        try:
            r = requests.get(f"{self.base_url.rstrip('/')}/api/v1/query_range",
                             params={"query": promql, "start": start, "end": end, "step": step},
                             timeout=self.timeout_seconds)
            r.raise_for_status()
            return {"available": True, "query": promql, "result": r.json()}
        except Exception as exc:
            return {"available": False, "query": promql, "error": str(exc), "result": None}
