"""add governed memory and persistent checkpoints

Revision ID: 0003_governed_memory_checkpoints
Revises: 0002_operational_memory
Create Date: 2026-08-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_governed_memory_checkpoints"
down_revision = "0002_operational_memory"
branch_labels = None
depends_on = None


def upgrade():
    columns = [
        sa.Column("team", sa.String(120), nullable=False, server_default="unknown"),
        sa.Column("environment", sa.String(60), nullable=False, server_default="unknown"),
        sa.Column("incident_type", sa.String(120), nullable=False, server_default="unknown"),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("evidence_references", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("runbook_id", sa.String(120), nullable=True),
        sa.Column("runbook_version", sa.String(40), nullable=True),
        sa.Column("model_version", sa.String(120), nullable=True),
        sa.Column("prompt_version", sa.String(120), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("verification_status", sa.String(40), nullable=False, server_default="candidate"),
        sa.Column("verified_by", sa.String(120), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("remediation_result", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("recovery_metrics", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("sensitivity", sa.String(40), nullable=False, server_default="internal"),
        sa.Column("retention_until", sa.DateTime(), nullable=True),
        sa.Column("superseded_by", sa.Integer(), nullable=True),
    ]
    for column in columns:
        op.add_column("operational_memory", column)
    for name in ["team", "environment", "incident_type", "verification_status", "sensitivity"]:
        op.create_index(f"ix_operational_memory_{name}", "operational_memory", [name])

    op.create_table(
        "investigation_checkpoints",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("checkpoint_id", sa.String(80), nullable=False, unique=True),
        sa.Column("investigation_id", sa.String(80), nullable=False),
        sa.Column("incident_id", sa.String(80), nullable=False),
        sa.Column("service", sa.String(120), nullable=False),
        sa.Column("team", sa.String(120), nullable=False, server_default="unknown"),
        sa.Column("environment", sa.String(60), nullable=False, server_default="unknown"),
        sa.Column("node", sa.String(120), nullable=False),
        sa.Column("mode", sa.String(80), nullable=True),
        sa.Column("state_json", sa.JSON(), nullable=False),
        sa.Column("sensitivity", sa.String(40), nullable=False, server_default="internal"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for name in ["checkpoint_id", "investigation_id", "incident_id", "service", "team", "environment"]:
        op.create_index(f"ix_investigation_checkpoints_{name}", "investigation_checkpoints", [name])


def downgrade():
    op.drop_table("investigation_checkpoints")
    for name in ["sensitivity", "verification_status", "incident_type", "environment", "team"]:
        op.drop_index(f"ix_operational_memory_{name}", table_name="operational_memory")
    for name in ["superseded_by", "retention_until", "sensitivity", "recovery_metrics", "remediation_result", "verified_at", "verified_by", "verification_status", "confidence", "prompt_version", "model_version", "runbook_version", "runbook_id", "evidence_references", "root_cause", "incident_type", "environment", "team"]:
        op.drop_column("operational_memory", name)
