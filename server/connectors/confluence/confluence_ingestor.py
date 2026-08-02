from __future__ import annotations

from typing import Any
from server.connectors.confluence.metadata_mapper import infer_confluence_metadata


def chunk_text(text: str, size: int = 1200, overlap: int = 150) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks or [""]


def normalize_page_for_vector_store(page: dict[str, Any]) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    metadata = infer_confluence_metadata(page)
    body = page.get("body") or page.get("content") or ""
    text = f"# {metadata['title']}\n\n{body}"
    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict[str, Any]] = []
    for idx, chunk in enumerate(chunk_text(text)):
        ids.append(f"confluence::{metadata['page_id']}::{idx}")
        docs.append(chunk)
        metas.append({**metadata, "chunk": idx})
    return ids, docs, metas
