# Postgres Disaster Recovery Runbook

## Goal

Recover incident platform persistence with controlled RTO/RPO.

## Steps

1. Confirm primary database health.
2. Check latest backup timestamp.
3. Validate replication lag if replicas exist.
4. Restore to a clean standby when primary is unrecoverable.
5. Run Alembic migrations.
6. Start API and worker services.
7. Verify `/health`, incident creation, timeline writes, and approval workflow.
8. Record actual RTO/RPO in ARIA.

## Safety

Do not overwrite production data without incident commander approval.
