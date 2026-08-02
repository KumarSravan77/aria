from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel

try:
    from server.api.security import require_auth
except Exception:
    def require_auth():
        return {"id": "local"}

from server.rag_types.simple_rag import SimpleOperationalRag
from server.rag_types.agentic_rag import AgenticOperationalRag
from server.rag_types.graph_rag import GraphOperationalRag

router = APIRouter(prefix="/rag", tags=["rag-types"])

class SimpleRagRequest(BaseModel):
    query: str
    service: str | None = None
    domain: str | None = None
    limit: int = 5

class AgenticRagRequest(BaseModel):
    incident: dict

class GraphRagRequest(BaseModel):
    query: str
    service: str | None = None
    domain: str | None = None
    depth: int = 1
    limit: int = 5

@router.post("/simple")
def simple(req: SimpleRagRequest, _user=Depends(require_auth)):
    return SimpleOperationalRag().retrieve(req.query, service=req.service, domain=req.domain, limit=req.limit)

@router.post("/agentic")
def agentic(req: AgenticRagRequest, _user=Depends(require_auth)):
    return AgenticOperationalRag().retrieve(req.incident)

@router.post("/graph")
def graph(req: GraphRagRequest, _user=Depends(require_auth)):
    return GraphOperationalRag().retrieve(req.query, service=req.service, domain=req.domain, depth=req.depth, limit=req.limit)
