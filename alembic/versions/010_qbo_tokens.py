"""Add QuickBooks Online OAuth tokens table

Revision ID: 010_qbo_tokens
Revises: 009_billing_entitlements
Create Date: 2025-10-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '010_qbo_tokens'
down_revision = '009_billing_entitlements'
branch_labels = None
depends_on = None


def upgrade():
    """Add QuickBooks Online OAuth tokens table."""
    
    op.create_table(
        'qbo_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('realm_id', sa.String(255), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('scope', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('idx_qbo_tokens_tenant_id', 'qbo_tokens', ['tenant_id'], unique=True)
    op.create_index('idx_qbo_tokens_realm_id', 'qbo_tokens', ['realm_id'])
    op.create_index('idx_qbo_tokens_expires_at', 'qbo_tokens', ['expires_at'])


def downgrade():
    """Remove QuickBooks Online OAuth tokens table."""
    op.drop_table('qbo_tokens')

