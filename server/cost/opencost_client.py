from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class OpenCostClient:
    base_url: str = "http://localhost:9003"
    timeout_seconds: int = 10

    def allocation(self, namespace: str | None = None) -> dict[str, Any]:
        params = {"window": "1d"}
        if namespace:
            params["filter"] = f"namespace:{namespace}"
        try:
            r = requests.get(f"{self.base_url.rstrip('/')}/model/allocation", params=params, timeout=self.timeout_seconds)
            r.raise_for_status()
            return {"available": True, "namespace": namespace, "result": r.json()}
        except Exception as exc:
            return {"available": False, "namespace": namespace, "error": str(exc)}
