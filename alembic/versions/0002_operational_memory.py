"""add operational memory

Revision ID: 0002_operational_memory
Revises: 0001_initial_schema
Create Date: 2026-05-16
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_operational_memory'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'operational_memory',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('service', sa.String(length=120), nullable=False),
        sa.Column('incident_id', sa.String(length=80), nullable=False),
        sa.Column('outcome', sa.String(length=120), nullable=False),
        sa.Column('remediation', sa.Text(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_operational_memory_service', 'operational_memory', ['service'])
    op.create_index('ix_operational_memory_incident_id', 'operational_memory', ['incident_id'])
    op.create_index('ix_operational_memory_outcome', 'operational_memory', ['outcome'])


def downgrade():
    op.drop_index('ix_operational_memory_outcome', table_name='operational_memory')
    op.drop_index('ix_operational_memory_incident_id', table_name='operational_memory')
    op.drop_index('ix_operational_memory_service', table_name='operational_memory')
    op.drop_table('operational_memory')
