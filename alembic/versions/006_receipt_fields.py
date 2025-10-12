"""Add receipt fields table for bounding boxes

Revision ID: 006_receipt_fields
Revises: 005_notifications
Create Date: 2024-10-11 20:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_receipt_fields'
down_revision = '005_notifications'
branch_labels = None
depends_on = None


def upgrade():
    """Create receipt_fields table for bounding box coordinates."""
    op.create_table(
        'receipt_fields',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('receipt_id', sa.String(255), nullable=False),
        sa.Column('field', sa.String(50), nullable=False),  # date, amount, vendor, total
        sa.Column('page', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('x', sa.Float(), nullable=False),  # Normalized 0-1
        sa.Column('y', sa.Float(), nullable=False),  # Normalized 0-1
        sa.Column('w', sa.Float(), nullable=False),  # Normalized 0-1
        sa.Column('h', sa.Float(), nullable=False),  # Normalized 0-1
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    
    op.create_index('idx_receipt_fields_receipt', 'receipt_fields', ['receipt_id'])
    op.create_index('idx_receipt_fields_field', 'receipt_fields', ['field'])


def downgrade():
    """Drop receipt_fields table."""
    op.drop_index('idx_receipt_fields_field', 'receipt_fields')
    op.drop_index('idx_receipt_fields_receipt', 'receipt_fields')
    op.drop_table('receipt_fields')

