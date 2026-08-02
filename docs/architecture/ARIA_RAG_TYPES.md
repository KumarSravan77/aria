# ARIA — RAG Types

ARIA now includes three operational RAG patterns.

## Simple RAG
Endpoint: `POST /rag/simple`

Direct runbook/RCA lookup.

## Agentic RAG
Endpoint: `POST /rag/agentic`

Multi-step deterministic retrieval for incident context:
service runbook, RCA, remediation query.

## Graph RAG
Endpoint: `POST /rag/graph`

Relationship-based retrieval:
service → runbook/RCA → domain → tags.

## Safety
RAG is evidence only. It does not execute remediation.
All remediation still requires ReBAC, policy, approval, validation and audit.
