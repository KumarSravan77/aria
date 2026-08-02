from __future__ import annotations
import os
from server.authz.authorization_service import AuthorizationService
from server.models.schemas import UserContext

class RagService:
    def __init__(self):
        try:
            import chromadb
            from chromadb.utils import embedding_functions
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "RagService requires optional dependency chromadb. "
                "Install server/requirements.txt or use LazyRagService fallback in lightweight test environments."
            ) from exc

        chroma_path = os.getenv("CHROMA_PATH", "./chroma")
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.embedder = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(
            name="incident_runbooks",
            embedding_function=self.embedder,
            metadata={"description": "Runbooks, RCA, SOP, incident docs, Confluence wiki pages"},
        )
        self.authz = AuthorizationService()

    def _allowed_filter(self, user: UserContext | None):
        return self.authz.vector_where_filter(user)

    def answer(self, question: str, user: UserContext | None = None):
        where = self._allowed_filter(user)
        query_args = {"query_texts": [question], "n_results": 5}
        if where:
            query_args["where"] = where
        results = self.collection.query(**query_args)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        if not docs:
            return {
                "answer": "No authorized runbook content was found for this query. ReBAC blocked all matching documents or no runbook exists yet.",
                "sources": [],
                "mode": "retrieval-only-rebac-filtered",
                "authz": {"allowed_services": self.authz.allowed_services(user)},
            }
        merged = "\n\n".join(docs[:3])
        answer = (
            "Based on authorized runbooks/wiki pages, start with these steps:\n"
            "1. Confirm the alert scope, service, namespace, and recent change window.\n"
            "2. Check latency, error rate, saturation, Kubernetes events, and service dependencies.\n"
            "3. Compare recent deployment time with the incident start time.\n"
            "4. Apply only policy-approved remediation such as scaling or restart.\n"
            "5. Validate recovery using metrics before closing the incident.\n\n"
            f"Relevant authorized context:\n{merged[:2500]}"
        )
        return {
            "answer": answer,
            "sources": [
                {
                    "title": m.get("title"),
                    "path": m.get("path"),
                    "source": m.get("source", "repo"),
                    "space": m.get("space"),
                    "team": m.get("team"),
                    "service": m.get("service"),
                    "doc_type": m.get("doc_type"),
                }
                for m in metas
            ],
            "mode": "retrieval-only-rebac-filtered",
            "authz": {"allowed_services": self.authz.allowed_services(user)},
        }
