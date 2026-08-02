from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AgentFlowExporter:
    def export(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        nodes = []
        edges = []
        previous = None
        for event in events:
            node_id = event.get("event_id")
            label = event.get("node") or event.get("tool") or event.get("event_type")
            nodes.append({
                "id": node_id,
                "label": label,
                "type": event.get("event_type"),
                "status": event.get("status"),
                "duration_ms": event.get("duration_ms"),
            })
            if previous:
                edges.append({"source": previous, "target": node_id})
            previous = node_id
        return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}
