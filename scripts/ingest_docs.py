import os
import re
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

DOCS_PATH = Path(os.getenv("DOCS_PATH", "docs"))
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma")

client = chromadb.PersistentClient(path=CHROMA_PATH)
embedder = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_or_create_collection(name="incident_runbooks", embedding_function=embedder)

def chunk_text(text, size=1200, overlap=150):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start+size])
        start += size - overlap
    return chunks or [""]

def first_match(text: str, patterns: list[str], default: str):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip().split(',')[0].strip().lower()
    return default

def infer_metadata(path: Path, raw: str):
    lower = raw.lower()
    team = first_match(lower, [r"team:\s*([a-zA-Z0-9_.-]+)", r"owner team:\s*([a-zA-Z0-9_.-]+)"], "platform")
    service = first_match(lower, [r"service:\s*([a-zA-Z0-9_.-]+)", r"services:\s*([a-zA-Z0-9_.-]+)"], "kubernetes-platform" if team == "platform" else "checkout-api")
    return team, service

ids, docs, metas = [], [], []
for path in DOCS_PATH.rglob("*.md"):
    raw = path.read_text(encoding="utf-8", errors="ignore")
    team, service = infer_metadata(path, raw)
    for idx, chunk in enumerate(chunk_text(raw)):
        ids.append(f"{path.as_posix()}::{idx}")
        docs.append(chunk)
        metas.append({
            "source": "repo",
            "path": path.as_posix(),
            "title": raw.splitlines()[0].replace("#", "").strip() if raw.splitlines() else path.name,
            "team": team,
            "service": service,
            "doc_type": path.parent.name,
        })
if ids:
    collection.upsert(ids=ids, documents=docs, metadatas=metas)
print(f"Ingested {len(ids)} chunks from {DOCS_PATH}")
