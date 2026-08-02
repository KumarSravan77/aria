from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class OpenFGAClient:
    api_url: str = "http://localhost:8081"
    store_id: str | None = None
    authorization_model_id: str | None = None
    token: str | None = None
    timeout_seconds: int = 10

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def check(self, user: str, relation: str, object_: str) -> dict[str, Any]:
        if not self.store_id:
            return {"available": False, "allowed": False, "error": "OPENFGA_STORE_ID is not configured"}
        payload: dict[str, Any] = {"tuple_key": {"user": user, "relation": relation, "object": object_}}
        if self.authorization_model_id:
            payload["authorization_model_id"] = self.authorization_model_id
        try:
            r = requests.post(
                f"{self.api_url.rstrip('/')}/stores/{self.store_id}/check",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout_seconds,
            )
            r.raise_for_status()
            data = r.json()
            return {"available": True, "allowed": bool(data.get("allowed")), "raw": data}
        except Exception as exc:
            return {"available": False, "allowed": False, "error": str(exc)}
