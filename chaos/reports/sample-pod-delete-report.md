# Sample Chaos Resilience Report

Use `make chaos-report EXPERIMENT=pod-delete` to generate a live report from observed signals.

Expected strong result:

- Incident created
- Alert fired
- ReBAC-filtered RAG found service runbooks
- Healing workflow succeeded or safely required approval
- MTTR captured
- SLO impact observed
