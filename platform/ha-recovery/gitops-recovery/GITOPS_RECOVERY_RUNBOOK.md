# GitOps Recovery Runbook

1. Confirm target cluster is reachable.
2. Reinstall Argo CD if needed.
3. Restore app manifests from Git.
4. Sync critical platform apps first: database, Redis, ChromaDB, API, worker.
5. Validate service health and ingress.
6. Re-run smoke tests and RAG retrieval tests.
