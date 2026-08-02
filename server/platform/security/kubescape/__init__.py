from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class KubescapeClient:
    """Kubescape security posture score via Kubescape Cloud or local scan API."""
    base_url: str = ""
    account_id: str | None = None
    timeout_seconds: int = 15

    def posture_score(self, cluster: str = "default") -> dict[str, Any]:
        if not self.base_url or not self.account_id:
            return {
                "available": False,
                "cluster": cluster,
                "message": "Set KUBESCAPE_URL and KUBESCAPE_ACCOUNT_ID, or run kubescape scan locally.",
            }
        try:
            r = requests.get(
                f"{self.base_url.rstrip('/')}/api/v1/posture/clustersOvertime",
                params={"customerGUID": self.account_id, "clusterName": cluster},
                timeout=self.timeout_seconds,
            )
            r.raise_for_status()
            return {"available": True, "cluster": cluster, "result": r.json()}
        except Exception as exc:
            return {"available": False, "cluster": cluster, "error": str(exc)}
