from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from server.rag_types.knowledge_store import OperationalKnowledgeStore

@dataclass
class OperationalGraph:
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[dict[str, str]] = field(default_factory=list)

    def add_node(self, node_id: str, **attrs: Any) -> None:
        self.nodes.setdefault(node_id, {"id": node_id})
        self.nodes[node_id].update(attrs)

    def add_edge(self, source: str, target: str, relation: str) -> None:
        edge = {"source": source, "target": target, "relation": relation}
        if edge not in self.edges:
            self.edges.append(edge)

    def neighbors(self, node_id: str) -> list[dict[str, Any]]:
        out = []
        for e in self.edges:
            if e["source"] == node_id:
                out.append({"edge": e, "node": self.nodes.get(e["target"], {"id": e["target"]})})
            elif e["target"] == node_id:
                out.append({"edge": e, "node": self.nodes.get(e["source"], {"id": e["source"]})})
        return out

@dataclass
class GraphOperationalRag:
    store: OperationalKnowledgeStore = field(default_factory=OperationalKnowledgeStore)

    def build_graph(self) -> OperationalGraph:
        graph = OperationalGraph()
        for doc in self.store.load():
            doc_id, service, domain = doc["id"], doc.get("service","unknown"), doc.get("domain","unknown")
            graph.add_node(doc_id, type=doc.get("type"), title=doc.get("title"), service=service, domain=domain)
            graph.add_node(service, type="service", domain=domain)
            graph.add_node(domain, type="domain")
            graph.add_edge(service, doc_id, "has_knowledge")
            graph.add_edge(domain, service, "owns_domain_service")
            for tag in doc.get("tags", []):
                tag_id = f"tag:{tag}"
                graph.add_node(tag_id, type="tag", value=tag)
                graph.add_edge(doc_id, tag_id, "tagged_with")
        return graph

    def retrieve(self, query: str, *, service: str | None = None, domain: str | None = None, depth: int = 1, limit: int = 5) -> dict[str, Any]:
        graph = self.build_graph()
        direct = self.store.search(query, service=service, domain=domain, limit=limit)
        expanded = {d["id"]: d for d in direct}
        frontier = [d["id"] for d in direct]
        for _ in range(depth):
            next_frontier = []
            for node_id in frontier:
                for n in graph.neighbors(node_id):
                    nid = n["node"]["id"]
                    match = next((d for d in self.store.load() if d["id"] == nid), None)
                    if match:
                        expanded[nid] = match
                    next_frontier.append(nid)
            frontier = next_frontier
        return {"rag_type":"graph","query":query,"service":service,"domain":domain,"depth":depth,"direct_count":len(direct),"expanded_count":len(expanded),"sources":list(expanded.values()),"graph":{"node_count":len(graph.nodes),"edge_count":len(graph.edges)}}
