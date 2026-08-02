from __future__ import annotations
from collections import Counter
from datetime import timedelta
from typing import Any

from server.utils_time import utc_now


class TemporalClusterer:
    """Groups incidents for the same service within a rolling time window.

    Three or more incidents for the same service in a window indicate a cluster
    that likely shares a root cause and should be investigated together.
    """

    CLUSTER_THRESHOLD = 3

    def cluster(self, service: str, db: Any, window_seconds: int = 3600) -> dict[str, Any]:
        from server.db.models import Incident
        cutoff = utc_now() - timedelta(seconds=window_seconds)
        try:
            rows = (
                db.query(Incident)
                .filter(Incident.service == service, Incident.created_at >= cutoff)
                .order_by(Incident.created_at.asc())
                .all()
            )
        except Exception:
            rows = []

        size = len(rows)
        if size <= 1:
            return {
                "service": service,
                "cluster_size": size,
                "is_cluster": False,
                "probable_shared_cause": None,
                "incident_ids": [r.id for r in rows],
                "window_seconds": window_seconds,
                "recommendation": "No cluster detected.",
            }

        causes = [
            r.payload.get("analysis", {}).get("probable_cause", "unknown")
            for r in rows if r.payload
        ]
        most_common = Counter(causes).most_common(1)[0][0] if causes else "unknown"
        is_cluster = size >= self.CLUSTER_THRESHOLD

        return {
            "service": service,
            "cluster_size": size,
            "is_cluster": is_cluster,
            "probable_shared_cause": most_common if is_cluster else None,
            "incident_ids": [r.id for r in rows],
            "window_seconds": window_seconds,
            "recommendation": (
                f"Cluster detected ({size} incidents). Investigate shared root cause '{most_common}' "
                "before acting on each incident independently."
            ) if is_cluster else f"Minor cluster ({size} incidents); may be independent.",
        }
