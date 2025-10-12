"""Add users table for JWT auth

Revision ID: 003_auth_users
Revises: 002_tenant_settings
Create Date: 2024-10-11 16:00:00

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '003_auth_users'
down_revision = '002_tenant_settings'
branch_labels = None
depends_on = None


def upgrade():
    """Add users table for authentication."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('user_id', sa.String(255), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=True),  # NULL for magic link only
        sa.Column('role', sa.String(50), nullable=False),  # 'owner' or 'staff'
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(), nullable=True)
    )
    
    # Create indexes for users
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_role', 'users', ['role'])
    
    # Seed default users
    op.execute("""
        INSERT INTO users (user_id, email, role)
        VALUES 
            ('user-admin-001', 'admin@example.com', 'owner'),
            ('user-staff-001', 'staff@acmecorp.com', 'staff'),
            ('user-staff-002', 'staff@betainc.com', 'staff')
        ON CONFLICT (user_id) DO NOTHING;
    """)
    
    # Seed staff tenant assignments
    op.execute("""
        INSERT INTO user_tenants (user_id, tenant_id)
        VALUES
            ('user-staff-001', 'pilot-acme-corp-082aceed'),
            ('user-staff-002', 'pilot-beta-accounting-inc-31707447')
        ON CONFLICT (user_id, tenant_id) DO NOTHING;
    """)


def downgrade():
    """Remove users table."""
    op.drop_index('idx_users_role', 'users')
    op.drop_index('idx_users_email', 'users')
    op.drop_table('users')

