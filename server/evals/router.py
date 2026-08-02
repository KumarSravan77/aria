from __future__ import annotations
from fastapi import APIRouter, Depends

try:
    from server.api.security import require_auth
except Exception:
    def require_auth():
        return {"id": "local"}

from server.evals.benchmark_runner import BenchmarkRunner
from server.evals.synthetic_incidents import SYNTHETIC_INCIDENTS

router = APIRouter(prefix="/evals", tags=["evals"])

@router.get("/synthetic-incidents")
def synthetic_incidents(_user=Depends(require_auth)):
    return {"count": len(SYNTHETIC_INCIDENTS), "incidents": SYNTHETIC_INCIDENTS}

@router.get("/benchmark")
def benchmark(_user=Depends(require_auth)):
    return BenchmarkRunner().run()
