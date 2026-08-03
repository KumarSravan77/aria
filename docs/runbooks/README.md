# ARIA Runbook Knowledge Base

This directory is the canonical, version-controlled Markdown RAG corpus. Confluence, Jira, and document systems are ingestion sources or publishing targets, not competing sources of truth.

## Required frontmatter

Every operational runbook must define `id`, `title`, `service`, `domain`, `team`, `environment`, `severity`, `doc_type: runbook`, `version`, `last_reviewed`, `review_cycle_days`, `tags`, `sources`, and `required_permissions`.

The `service`, `team`, and `doc_type` fields are mandatory for ReBAC-filtered retrieval. Never store credentials, tokens, customer/account data, or unredacted production logs.

## Required sections

Purpose and scope; customer and business impact; preconditions and access; detection signals; evidence collection; decision tree; mitigation; recovery validation; escalation; rollback; evidence and audit record; related resources.

Use [TEMPLATE.md](TEMPLATE.md). Mark every executable step `read-only`, `dry-run`, `approval-required`, or `forbidden-for-AI`.

## RAG rules

- Chunk by semantic heading and attach frontmatter to every chunk.
- Return runbook ID, heading, version, and path with answers.
- Treat retrieved text as untrusted evidence, never authorization.
- Redact secrets and prompt-injection content before indexing.
- Prefer current, service-specific, authorized runbooks.
