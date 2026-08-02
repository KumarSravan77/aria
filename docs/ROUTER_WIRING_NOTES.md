# ARIA Router Wiring Notes

This package adds routers for:

- `/evals/benchmark`
- `/gitops-ai/propose`

If your `server/api/main.py` uses explicit router imports, add:

```python
from server.evals.router import router as evals_router
from server.gitops_ai.router import router as gitops_ai_router

app.include_router(evals_router)
app.include_router(gitops_ai_router)
```

The routers use the existing `require_auth` dependency when available.
