import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from server.connectors.confluence.confluence_client import ConfluenceClient
from server.connectors.confluence.confluence_ingestor import normalize_page_for_vector_store

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
LOCAL_CONFLUENCE_FILE = Path(os.getenv("LOCAL_CONFLUENCE_FILE", "examples/confluence/pages.json"))
CONFLUENCE_SPACE = os.getenv("CONFLUENCE_SPACE")

client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
embedder = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_or_create_collection(name="incident_runbooks", embedding_function=embedder)
confluence = ConfluenceClient()

if CONFLUENCE_SPACE:
    pages = confluence.fetch_pages_from_space(CONFLUENCE_SPACE)
else:
    pages = confluence.load_local_pages(LOCAL_CONFLUENCE_FILE)

ids, docs, metas = [], [], []
for page in pages:
    page_ids, page_docs, page_metas = normalize_page_for_vector_store(page)
    ids.extend(page_ids)
    docs.extend(page_docs)
    metas.extend(page_metas)

if ids:
    collection.upsert(ids=ids, documents=docs, metadatas=metas)
print(f"Synced {len(pages)} Confluence/wiki pages as {len(ids)} chunks")
