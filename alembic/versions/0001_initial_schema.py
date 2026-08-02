"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-15
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'incidents',
        sa.Column('id', sa.String(length=80), primary_key=True),
        sa.Column('alert_name', sa.String(length=200), nullable=True),
        sa.Column('service', sa.String(length=120), nullable=False),
        sa.Column('environment', sa.String(length=60), nullable=False),
        sa.Column('severity', sa.String(length=40), nullable=False),
        sa.Column('source', sa.String(length=80), nullable=True),
        sa.Column('status', sa.String(length=40), nullable=True),
        sa.Column('channel_id', sa.String(length=200), nullable=True),
        sa.Column('channel_name', sa.String(length=200), nullable=True),
        sa.Column('dedupe_key', sa.String(length=250), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_incidents_service', 'incidents', ['service'])
    op.create_index('ix_incidents_environment', 'incidents', ['environment'])
    op.create_index('ix_incidents_severity', 'incidents', ['severity'])
    op.create_index('ix_incidents_status', 'incidents', ['status'])
    op.create_index('ix_incidents_dedupe_key', 'incidents', ['dedupe_key'])

    op.create_table(
        'incident_timeline',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('incident_id', sa.String(length=80), sa.ForeignKey('incidents.id'), nullable=False),
        sa.Column('event_type', sa.String(length=120), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_incident_timeline_incident_id', 'incident_timeline', ['incident_id'])
    op.create_index('ix_incident_timeline_event_type', 'incident_timeline', ['event_type'])

    op.create_table(
        'incident_actions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('incident_id', sa.String(length=80), nullable=False),
        sa.Column('action', sa.String(length=120), nullable=False),
        sa.Column('target', sa.String(length=200), nullable=False),
        sa.Column('namespace', sa.String(length=120), nullable=True),
        sa.Column('requested_by', sa.String(length=120), nullable=True),
        sa.Column('approved', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('executed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('result', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_incident_actions_incident_id', 'incident_actions', ['incident_id'])

    op.create_table(
        'incident_approvals',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('incident_id', sa.String(length=80), nullable=False),
        sa.Column('action_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('approver', sa.String(length=120), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_incident_approvals_incident_id', 'incident_approvals', ['incident_id'])

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('actor', sa.String(length=120), nullable=False),
        sa.Column('action', sa.String(length=180), nullable=False),
        sa.Column('resource_type', sa.String(length=80), nullable=False),
        sa.Column('resource_id', sa.String(length=120), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'])

    op.create_table(
        'incident_rca',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('incident_id', sa.String(length=80), nullable=False),
        sa.Column('markdown', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_incident_rca_incident_id', 'incident_rca', ['incident_id'])


def downgrade():
    op.drop_table('incident_rca')
    op.drop_table('audit_logs')
    op.drop_table('incident_approvals')
    op.drop_table('incident_actions')
    op.drop_table('incident_timeline')
    op.drop_table('incidents')
