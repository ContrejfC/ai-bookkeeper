"""Create admin user with password

Revision ID: 004_create_admin_user
Revises: 003_auth_users
Create Date: 2024-10-14 02:00:00

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '004_create_admin_user'
down_revision = '003_auth_users'
branch_labels = None
depends_on = None


def upgrade():
    """Create admin user with password hash."""
    
    # Create admin user with password hash
    # Password hash for 'admin123' using bcrypt
    password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/9Yz8x2e'
    
    op.execute(f"""
        INSERT INTO users (user_id, email, password_hash, role, is_active, created_at)
        VALUES (
            'user-admin-001',
            'admin@example.com',
            '{password_hash}',
            'owner',
            true,
            NOW()
        )
        ON CONFLICT (email) DO UPDATE SET
            password_hash = EXCLUDED.password_hash,
            is_active = EXCLUDED.is_active;
    """)


def downgrade():
    """Remove admin user password."""
    op.execute("""
        UPDATE users 
        SET password_hash = NULL 
        WHERE email = 'admin@example.com';
    """)
