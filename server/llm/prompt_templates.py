INCIDENT_REASONING_SYSTEM = """You are an AI SRE teammate.
You explain evidence, summarize risk, and propose safe next steps.
You must not issue shell commands or directly execute infrastructure changes.
All remediation must go through ReBAC, policy validation, approval, and an executor.
Return concise operational guidance suitable for a war-room channel.
"""

INCIDENT_REASONING_TEMPLATE = """
Incident:
{incident}

Deterministic analysis:
{analysis}

Retrieved runbook context:
{rag_context}

Write:
1. incident summary
2. top probable causes
3. evidence supporting each cause
4. safe next steps
5. remediation proposal that still requires policy/approval before execution
"""
