"""Add billing tables for Stripe integration

Revision ID: 004_billing
Revises: 003_auth_users
Create Date: 2024-10-11 18:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '004_billing'
down_revision = '003_auth_users'
branch_labels = None
depends_on = None


def upgrade():
    """Create billing tables."""
    
    # Subscriptions table
    op.create_table(
        'billing_subscriptions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(255), nullable=False, unique=True),
        sa.Column('plan', sa.String(50), nullable=False),  # starter, pro, firm
        sa.Column('status', sa.String(50), nullable=False),  # active, past_due, canceled, trialing
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant_settings.tenant_id'])
    )
    
    op.create_index('idx_billing_subs_tenant', 'billing_subscriptions', ['tenant_id'], unique=True)
    op.create_index('idx_billing_subs_status', 'billing_subscriptions', ['status'])
    op.create_index('idx_billing_subs_stripe_customer', 'billing_subscriptions', ['stripe_customer_id'])
    
    # Webhook events audit log
    op.create_table(
        'billing_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('stripe_event_id', sa.String(255), nullable=True, unique=True),
        sa.Column('payload_json', JSONB, nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    
    op.create_index('idx_billing_events_type', 'billing_events', ['type'])
    op.create_index('idx_billing_events_processed', 'billing_events', ['processed'])
    op.create_index('idx_billing_events_stripe_id', 'billing_events', ['stripe_event_id'], unique=True)


def downgrade():
    """Drop billing tables."""
    op.drop_index('idx_billing_events_stripe_id', 'billing_events')
    op.drop_index('idx_billing_events_processed', 'billing_events')
    op.drop_index('idx_billing_events_type', 'billing_events')
    op.drop_table('billing_events')
    
    op.drop_index('idx_billing_subs_stripe_customer', 'billing_subscriptions')
    op.drop_index('idx_billing_subs_status', 'billing_subscriptions')
    op.drop_index('idx_billing_subs_tenant', 'billing_subscriptions')
    op.drop_table('billing_subscriptions')

