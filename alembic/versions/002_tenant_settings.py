"""Add tenant_settings table for Wave-2 Phase 1

Revision ID: 002_tenant_settings
Revises: 001
Create Date: 2024-10-11 15:00:00

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '002_tenant_settings'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """Add tenant_settings and user_tenants tables."""
    
    # Create tenant_settings table
    op.create_table(
        'tenant_settings',
        sa.Column('tenant_id', sa.String(255), primary_key=True),
        sa.Column('autopost_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('autopost_threshold', sa.Float(), nullable=False, server_default='0.90'),
        sa.Column('llm_tenant_cap_usd', sa.Float(), nullable=False, server_default='50.0'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    
    # Create indexes for tenant_settings
    op.create_index('idx_tenant_settings_updated_at', 'tenant_settings', ['updated_at'])
    
    # Create user_tenants table for RBAC
    op.create_table(
        'user_tenants',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    
    # Create indexes for user_tenants
    op.create_index('idx_user_tenants_user_id', 'user_tenants', ['user_id'])
    op.create_index('idx_user_tenants_tenant_id', 'user_tenants', ['tenant_id'])
    op.create_index('idx_user_tenants_user_tenant', 'user_tenants', ['user_id', 'tenant_id'], unique=True)
    
    # Seed default tenant settings for existing tenants
    op.execute("""
        INSERT INTO tenant_settings (tenant_id, autopost_enabled, autopost_threshold, llm_tenant_cap_usd)
        VALUES 
            ('pilot-acme-corp-082aceed', false, 0.90, 50.0),
            ('pilot-beta-accounting-inc-31707447', true, 0.92, 100.0),
            ('pilot-gamma-llc-abc123', false, 0.90, 50.0)
        ON CONFLICT (tenant_id) DO NOTHING;
    """)


def downgrade():
    """Remove tenant_settings and user_tenants tables."""
    op.drop_index('idx_user_tenants_user_tenant', 'user_tenants')
    op.drop_index('idx_user_tenants_tenant_id', 'user_tenants')
    op.drop_index('idx_user_tenants_user_id', 'user_tenants')
    op.drop_table('user_tenants')
    
    op.drop_index('idx_tenant_settings_updated_at', 'tenant_settings')
    op.drop_table('tenant_settings')

