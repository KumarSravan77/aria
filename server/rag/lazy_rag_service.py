from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class LazyRagService:
    """Fault-tolerant RAG wrapper.

    This wrapper delays construction of the heavy RagService until first use and
    returns structured unavailable responses instead of failing API startup when
    ChromaDB/SentenceTransformer is not available.
    """

    _service: Any = None
    _error: str | None = None

    def _get(self) -> Any:
        if self._service is not None:
            return self._service
        if self._error is not None:
            return None
        try:
            from server.rag.rag_service import RagService
            self._service = RagService()
            return self._service
        except Exception as exc:  # noqa: BLE001
            self._error = str(exc)
            return None

    def ask(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        service = self._get()
        if not service:
            return {
                "available": False,
                "mode": "rag_unavailable",
                "error": self._error,
                "answer": "RAG is unavailable; investigation continues with deterministic evidence.",
                "sources": [],
            }
        for method in ("answer", "ask", "query"):
            if hasattr(service, method):
                return getattr(service, method)(*args, **kwargs)
        return {"available": False, "mode": "rag_method_missing", "sources": []}

    def query(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.ask(*args, **kwargs)

    def answer(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.ask(*args, **kwargs)
