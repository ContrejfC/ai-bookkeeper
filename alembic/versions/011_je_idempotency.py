"""Add journal entry idempotency tracking table

Revision ID: 011_je_idempotency
Revises: 010_qbo_tokens
Create Date: 2025-10-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '011_je_idempotency'
down_revision = '010_qbo_tokens'
branch_labels = None
depends_on = None


def upgrade():
    """Add journal entry idempotency tracking table."""
    
    op.create_table(
        'je_idempotency',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('payload_hash', sa.String(64), nullable=False),  # SHA-256 hex
        sa.Column('qbo_doc_id', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Create unique composite index for idempotency
    op.create_index(
        'idx_je_idempotency_tenant_hash',
        'je_idempotency',
        ['tenant_id', 'payload_hash'],
        unique=True
    )
    op.create_index('idx_je_idempotency_tenant_id', 'je_idempotency', ['tenant_id'])
    op.create_index('idx_je_idempotency_qbo_doc_id', 'je_idempotency', ['qbo_doc_id'])


def downgrade():
    """Remove journal entry idempotency tracking table."""
    op.drop_table('je_idempotency')

