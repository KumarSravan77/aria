Read CLAUDE.md and AGENTS.md first.

Add a new self-healing action: <ACTION_NAME>

Requirements:
- Must be policy controlled
- Must not execute arbitrary shell commands
- Must use Kubernetes Python client if Kubernetes-related
- Must include validation behavior
- Must include tests
- Must update docs/sop/self-healing-policy.md
