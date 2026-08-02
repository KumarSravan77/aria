from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from server.rag_types.knowledge_store import OperationalKnowledgeStore

@dataclass
class SimpleOperationalRag:
    store: OperationalKnowledgeStore = field(default_factory=OperationalKnowledgeStore)

    def retrieve(self, query: str, *, service: str | None = None, domain: str | None = None, limit: int = 5) -> dict[str, Any]:
        sources = self.store.search(query, service=service, domain=domain, limit=limit)
        return {"rag_type":"simple","query":query,"service":service,"domain":domain,"count":len(sources),"sources":sources}
