from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from server.rag_types.simple_rag import SimpleOperationalRag

@dataclass
class AgenticOperationalRag:
    simple_rag: SimpleOperationalRag = field(default_factory=SimpleOperationalRag)

    def plan_queries(self, incident: dict[str, Any]) -> list[str]:
        service = incident.get("service", "")
        signals = " ".join(str(x) for x in incident.get("signals", []))
        severity = incident.get("severity", "")
        return [f"{service} {signals} runbook", f"{service} {signals} RCA", f"{service} {severity} remediation rollback scale restart"]

    def retrieve(self, incident: dict[str, Any], limit_per_query: int = 3) -> dict[str, Any]:
        merged = {}
        queries = self.plan_queries(incident)
        for q in queries:
            result = self.simple_rag.retrieve(q, service=incident.get("service"), domain=incident.get("domain"), limit=limit_per_query)
            for source in result["sources"]:
                merged[source["id"]] = source
        sources = sorted(merged.values(), key=lambda x: x.get("score", 0), reverse=True)
        return {"rag_type":"agentic","incident":incident,"queries":queries,"count":len(sources),"sources":sources,"safety_boundary":"Retrieval only; no execution."}
