"""Add notification tables for email and Slack alerts

Revision ID: 005_notifications
Revises: 004_billing
Create Date: 2024-10-11 19:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '005_notifications'
down_revision = '004_billing'
branch_labels = None
depends_on = None


def upgrade():
    """Create notification tables."""
    
    # Tenant notification settings
    op.create_table(
        'tenant_notifications',
        sa.Column('tenant_id', sa.String(255), primary_key=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('slack_webhook_url', sa.Text(), nullable=True),
        sa.Column('alerts_json', JSONB, nullable=False, server_default='{}'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant_settings.tenant_id'])
    )
    
    op.create_index('idx_tenant_notifications_tenant', 'tenant_notifications', ['tenant_id'], unique=True)
    
    # Notification audit log (for debounce tracking)
    op.create_table(
        'notification_log',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),  # 'email' or 'slack'
        sa.Column('type', sa.String(100), nullable=False),     # e.g. 'psi_alert'
        sa.Column('payload_json', JSONB, nullable=False),
        sa.Column('sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    
    op.create_index('idx_notif_log_tenant_type', 'notification_log', ['tenant_id', 'type', 'created_at'])
    op.create_index('idx_notif_log_sent', 'notification_log', ['sent'])


def downgrade():
    """Drop notification tables."""
    op.drop_index('idx_notif_log_sent', 'notification_log')
    op.drop_index('idx_notif_log_tenant_type', 'notification_log')
    op.drop_table('notification_log')
    
    op.drop_index('idx_tenant_notifications_tenant', 'tenant_notifications')
    op.drop_table('tenant_notifications')

