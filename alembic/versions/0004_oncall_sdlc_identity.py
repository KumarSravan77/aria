"""on-call SDLC event and identity tables"""
from alembic import op
import sqlalchemy as sa

revision = "0004_oncall"
down_revision = "0003_governed_memory_checkpoints"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("sdlc_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("event_id", sa.String(120), nullable=False), sa.Column("event_type", sa.String(80), nullable=False), sa.Column("service", sa.String(120), nullable=False), sa.Column("environment", sa.String(60), nullable=False), sa.Column("actor", sa.String(160), nullable=False), sa.Column("revision", sa.String(160)), sa.Column("occurred_at", sa.DateTime(), nullable=False), sa.Column("payload", sa.JSON(), nullable=False), sa.UniqueConstraint("event_id"))
    for column in ("event_id", "event_type", "service", "environment", "actor", "revision", "occurred_at"): op.create_index(f"ix_sdlc_events_{column}", "sdlc_events", [column])
    op.create_table("external_identities", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("aria_user_id", sa.String(120), nullable=False), sa.Column("provider", sa.String(40), nullable=False), sa.Column("external_user_id", sa.String(160), nullable=False), sa.Column("team", sa.String(120), nullable=False), sa.Column("verified", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    for column in ("aria_user_id", "provider", "external_user_id", "team"): op.create_index(f"ix_external_identities_{column}", "external_identities", [column])

def downgrade():
    op.drop_table("external_identities")
    op.drop_table("sdlc_events")
