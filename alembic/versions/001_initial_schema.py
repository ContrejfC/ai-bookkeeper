"""Initial schema baseline

Revision ID: 001_initial_schema
Revises: None
Create Date: 2025-10-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Initial schema baseline - placeholder for existing production tables.
    
    This migration establishes the baseline for the migration chain.
    If deploying to an existing database with tables already present,
    use: alembic stamp 001
    """
    # This is a placeholder baseline migration.
    # Actual tables were created via SQLAlchemy metadata.create_all() historically.
    # Subsequent migrations (002+) handle schema changes.
    pass


def downgrade():
    """Cannot downgrade from baseline."""
    pass

