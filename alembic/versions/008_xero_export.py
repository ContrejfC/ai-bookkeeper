"""xero export tables

Revision ID: 008_xero_export
Revises: 007_auth_hardening
Create Date: 2024-10-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_xero_export'
down_revision = '007_auth_hardening'
branch_labels = None
depends_on = None


def upgrade():
    # Xero account mappings
    op.create_table(
        'xero_account_mappings',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('internal_account', sa.String(100), nullable=False),
        sa.Column('xero_account_code', sa.String(100), nullable=False),
        sa.Column('xero_account_name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Index('idx_xero_mapping_tenant_internal', 'tenant_id', 'internal_account')
    )
    
    # Xero export log
    op.create_table(
        'xero_export_log',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('journal_entry_id', sa.String(255), nullable=False),
        sa.Column('external_id', sa.String(64), nullable=False),
        sa.Column('xero_journal_id', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('exported_at', sa.DateTime, server_default=sa.func.now()),
        sa.Index('idx_xero_export_tenant', 'tenant_id'),
        sa.Index('idx_xero_export_external_id', 'external_id')
    )


def downgrade():
    op.drop_table('xero_export_log')
    op.drop_table('xero_account_mappings')

