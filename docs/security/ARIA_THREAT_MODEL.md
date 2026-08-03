# ARIA Threat Model

## Threat Controls

### Spoofed webhook
Control: HMAC-SHA256 signature + X-Timestamp (±5 min tolerance) + X-Nonce (Redis SET nx ex, single-use).
Residual: replay within tolerance window if nonce store unavailable.

### Prompt Injection via incident payload
Control: LLMGuardrails blocks ungrounded responses; agents return structured AgentResult, not free text.
ReBAC gates all mutation paths independently of LLM output.

### Privilege escalation via approval bypass
Control: 4-eyes enforcement (requester != approver); ApprovalService.decide() checks status==PENDING; ReBAC validates approver team scope.

### Unauthorized cross-team data access
Control: ReBAC (local YAML + OpenFGA-ready) on every read endpoint; RAG ChromaDB queries scoped via vector_where_filter.

### Chaos experiment misuse
Control: CHAOS_ENABLED=false by default; chaos endpoints require ReBAC + namespace check; dry_run=true default.

### GitOps PR merge without approval
Control: PullRequestGenerator.create_pr() requires GITOPS_PR_LIVE_ENABLED=true; PR creation is advisory only by default.

### Agent direct execution
Control: BaseAgent.run() returns AgentResult only; no agent has write access to Kubernetes, ArgoCD, or Git.

### Memory poisoning
Control: model-produced outcomes are stored as candidates; only incident-commanders/admins can promote entries with root-cause and evidence references. Only verified, non-superseded, ReBAC-scoped entries influence agents. Promotion is audited.

### Sensitive checkpoint persistence
Control: persistent graph checkpoints contain bounded counts, routing and status metadata, not raw telemetry, prompts, logs, secrets, customer records or financial payloads.
