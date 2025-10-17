"""Add API keys table for GPT Actions authentication

Revision ID: 012_api_keys
Revises: 011_je_idempotency
Create Date: 2025-10-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012_api_keys'
down_revision = '011_je_idempotency'
branch_labels = None
depends_on = None


def upgrade():
    """Add API keys table for GPT Actions authentication."""
    
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False),  # SHA-256 hex
        sa.Column('name', sa.String(255), nullable=True),  # Optional description
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
    )
    
    # Create indexes
    op.create_index('idx_api_keys_tenant_id', 'api_keys', ['tenant_id'])
    op.create_index('idx_api_keys_token_hash', 'api_keys', ['token_hash'], unique=True)
    op.create_index('idx_api_keys_revoked_at', 'api_keys', ['revoked_at'])


def downgrade():
    """Remove API keys table."""
    op.drop_table('api_keys')

