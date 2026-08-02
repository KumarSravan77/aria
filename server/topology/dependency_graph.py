from __future__ import annotations
from typing import Any

# Default graph — override via YAML/DB in production.
DEFAULT_GRAPH: dict[str, list[str]] = {
    "checkout-api":         ["payment-api", "inventory-api", "recommendation-engine"],
    "payment-api":          ["fraud-detection", "ledger-service"],
    "inventory-api":        ["warehouse-service"],
    "kubernetes-platform":  ["checkout-api", "payment-api", "order-api", "inventory-api"],
    "order-api":            ["payment-api", "inventory-api"],
    "aria": [],
}


class ServiceDependencyGraph:
    """Directed service dependency graph.

    Edges represent "this service calls / depends on" relationships.
    `downstream(s)` = services that s depends on.
    `upstream(s)` = services that call s.
    """

    def __init__(self, graph: dict[str, list[str]] | None = None) -> None:
        self._graph: dict[str, list[str]] = graph if graph is not None else DEFAULT_GRAPH

    def downstream(self, service: str) -> list[str]:
        return list(self._graph.get(service, []))

    def upstream(self, service: str) -> list[str]:
        return sorted(s for s, deps in self._graph.items() if service in deps)

    def all_affected(self, service: str, max_depth: int = 5) -> list[str]:
        """BFS over downstream graph to find all transitively affected services."""
        visited: set[str] = set()
        queue = list(self._graph.get(service, []))
        depth = 0
        while queue and depth < max_depth:
            next_q: list[str] = []
            for s in queue:
                if s not in visited:
                    visited.add(s)
                    next_q.extend(self._graph.get(s, []))
            queue = next_q
            depth += 1
        return sorted(visited)

    def add_edge(self, from_service: str, to_service: str) -> None:
        self._graph.setdefault(from_service, [])
        if to_service not in self._graph[from_service]:
            self._graph[from_service].append(to_service)

    def to_dict(self) -> dict[str, Any]:
        return {
            "services": sorted(self._graph.keys()),
            "edges": [{"from": s, "to": dep} for s, deps in self._graph.items() for dep in deps],
            "total_services": len(self._graph),
            "total_edges": sum(len(v) for v in self._graph.values()),
        }
