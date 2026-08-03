---
name: aria-author-runbook
description: Create or update secure, RAG-ready Markdown runbooks for ARIA services and incidents. Use for operational diagnosis, CI/CD failures, Kubernetes incidents, recovery procedures, escalation, validation, or the required runbook for a new scenario.
---

# Author an ARIA runbook

1. Read `docs/runbooks/README.md` and use `docs/runbooks/TEMPLATE.md`.
2. Require stable ID and ReBAC metadata: service, team and `doc_type: runbook`.
3. Put observable signals and deterministic evidence before mitigation.
4. Mark steps read-only, dry-run, approval-required, or forbidden-for-AI.
5. Include impact, integrity risk, escalation, rollback, validation and audit evidence.
6. Use semantic headings and short steps for RAG chunking.
7. Exclude secrets, customer/account data and unredacted logs.
8. Add payload, correlation rule, test, RAG coverage and docs required by `AGENTS.md`.
9. Apply [references/review-checklist.md](references/review-checklist.md).
