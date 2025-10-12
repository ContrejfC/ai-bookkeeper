"""multi-tenant support

Revision ID: 002
Revises: 001
Create Date: 2025-10-09

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=True),
        sa.Column('is_superuser', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create companies table
    op.create_table(
        'companies',
        sa.Column('company_id', sa.String(), nullable=False),
        sa.Column('company_name', sa.String(), nullable=False),
        sa.Column('tax_id', sa.String(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('fiscal_year_end', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('company_id')
    )
    
    # Create user_company_links table
    op.create_table(
        'user_company_links',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('company_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.company_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_company', 'user_company_links', ['user_id', 'company_id'], unique=True)
    
    # Add company_id to transactions (allow nullable for migration)
    op.add_column('transactions', sa.Column('company_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_transactions_company_id'), 'transactions', ['company_id'])
    op.create_foreign_key('fk_transactions_company_id', 'transactions', 'companies', ['company_id'], ['company_id'])
    
    # Add company_id to journal_entries
    op.add_column('journal_entries', sa.Column('company_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_journal_entries_company_id'), 'journal_entries', ['company_id'])
    op.create_foreign_key('fk_journal_entries_company_id', 'journal_entries', 'companies', ['company_id'], ['company_id'])


def downgrade() -> None:
    # Remove company_id from journal_entries
    op.drop_constraint('fk_journal_entries_company_id', 'journal_entries', type_='foreignkey')
    op.drop_index(op.f('ix_journal_entries_company_id'), table_name='journal_entries')
    op.drop_column('journal_entries', 'company_id')
    
    # Remove company_id from transactions
    op.drop_constraint('fk_transactions_company_id', 'transactions', type_='foreignkey')
    op.drop_index(op.f('ix_transactions_company_id'), table_name='transactions')
    op.drop_column('transactions', 'company_id')
    
    # Drop tables
    op.drop_index('idx_user_company', table_name='user_company_links')
    op.drop_table('user_company_links')
    op.drop_table('companies')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

