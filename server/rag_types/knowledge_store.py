from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json, math, re

DEFAULT_KNOWLEDGE = Path("datasets/rag/operational_knowledge.json")

def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_/-]+", text.lower()))

@dataclass
class OperationalKnowledgeStore:
    path: Path = DEFAULT_KNOWLEDGE

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text())

    def search(self, query: str, *, service: str | None = None, domain: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
        q = tokenize(query)
        results = []
        for doc in self.load():
            if service and doc.get("service") != service:
                continue
            if domain and doc.get("domain") != domain:
                continue
            text = " ".join([doc.get("title",""), doc.get("content",""), " ".join(doc.get("tags",[])), doc.get("service",""), doc.get("domain","")])
            d = tokenize(text)
            overlap = len(q & d)
            score = overlap / math.sqrt(max(len(q), 1) * max(len(d), 1)) if d else 0
            if score > 0:
                item = dict(doc)
                item["score"] = round(score, 4)
                results.append(item)
        return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]
