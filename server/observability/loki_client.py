from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class LokiClient:
    base_url: str = "http://localhost:3100"
    timeout_seconds: int = 10

    def query(self, logql: str) -> dict[str, Any]:
        try:
            r = requests.get(f"{self.base_url.rstrip('/')}/loki/api/v1/query", params={"query": logql}, timeout=self.timeout_seconds)
            r.raise_for_status()
            return {"available": True, "query": logql, "result": r.json()}
        except Exception as exc:
            return {"available": False, "query": logql, "error": str(exc), "result": None}
