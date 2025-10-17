"""Add privacy consent and label training tables

Revision ID: 013_privacy_and_labels
Revises: 012_api_keys
Create Date: 2025-10-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '013_privacy_and_labels'
down_revision = '012_api_keys'
branch_labels = None
depends_on = None


def upgrade():
    """Add privacy consent and label training tables."""
    
    # Consent log table
    op.create_table(
        'consent_log',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('state', sa.String(20), nullable=False),  # 'opt_in', 'opt_out'
        sa.Column('actor', sa.String(255), nullable=True),  # user who changed it
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_consent_log_tenant_id', 'consent_log', ['tenant_id'])
    op.create_index('idx_consent_log_created_at', 'consent_log', ['created_at'])
    
    # Label salts for per-tenant redaction
    op.create_table(
        'label_salts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('salt', sa.String(64), nullable=False),  # hex-encoded salt
        sa.Column('rotated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_label_salts_tenant_id', 'label_salts', ['tenant_id'])
    
    # Label events - redacted training data
    op.create_table(
        'label_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('payload_redacted', sa.Text(), nullable=False),  # JSON string with redacted data
        sa.Column('approved_bool', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_label_events_tenant_id', 'label_events', ['tenant_id'])
    op.create_index('idx_label_events_created_at', 'label_events', ['created_at'])


def downgrade():
    """Remove privacy tables."""
    op.drop_table('label_events')
    op.drop_table('label_salts')
    op.drop_table('consent_log')

