"""Add billing entitlements and usage tracking

Revision ID: 009_billing_entitlements
Revises: 008_xero_export
Create Date: 2025-10-17
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '009_billing_entitlements'
down_revision = '008_xero_export'
branch_labels = None
depends_on = None


def upgrade():
    """Add billing entitlements and usage tracking tables."""
    
    # Add Stripe fields to tenant_settings table (if it exists)
    # Using try/except to handle if table doesn't exist or columns already exist
    try:
        with op.batch_alter_table('tenant_settings', schema=None) as batch_op:
            batch_op.add_column(sa.Column('stripe_customer_id', sa.String(255), nullable=True))
            batch_op.add_column(sa.Column('stripe_subscription_id', sa.String(255), nullable=True))
    except Exception:
        pass
    
    # Create entitlements table
    op.create_table(
        'entitlements',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('plan', sa.String(50), nullable=False),  # starter, pro, firm
        sa.Column('active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tx_cap', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('bulk_approve', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('included_companies', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('trial_ends_at', sa.DateTime(), nullable=True),
        sa.Column('subscription_status', sa.String(50), nullable=True),  # active, trialing, past_due, canceled
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for entitlements
    op.create_index('idx_entitlements_tenant_id', 'entitlements', ['tenant_id'])
    op.create_index('idx_entitlements_active', 'entitlements', ['active'])
    op.create_index('idx_entitlements_plan', 'entitlements', ['plan'])
    
    # Create usage_monthly table
    op.create_table(
        'usage_monthly',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('year_month', sa.String(7), nullable=False),  # Format: YYYY-MM
        sa.Column('tx_analyzed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tx_posted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_reset_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Create unique constraint for tenant_id + year_month
    op.create_index('idx_usage_monthly_tenant_month', 'usage_monthly', ['tenant_id', 'year_month'], unique=True)
    op.create_index('idx_usage_monthly_year_month', 'usage_monthly', ['year_month'])
    
    # Create usage_daily table for free tier limits
    op.create_table(
        'usage_daily',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('analyze_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('explain_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Create unique constraint for tenant_id + date
    op.create_index('idx_usage_daily_tenant_date', 'usage_daily', ['tenant_id', 'date'], unique=True)
    op.create_index('idx_usage_daily_date', 'usage_daily', ['date'])


def downgrade():
    """Remove billing entitlements and usage tracking tables."""
    
    # Drop tables
    op.drop_table('usage_daily')
    op.drop_table('usage_monthly')
    op.drop_table('entitlements')
    
    # Remove Stripe fields from tenant_settings (if needed)
    try:
        with op.batch_alter_table('tenant_settings', schema=None) as batch_op:
            batch_op.drop_column('stripe_subscription_id')
            batch_op.drop_column('stripe_customer_id')
    except Exception:
        pass

