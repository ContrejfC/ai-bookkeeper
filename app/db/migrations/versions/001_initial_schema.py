"""Initial schema for AI Bookkeeper

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-10-11 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table('users',
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

    # Companies
    op.create_table('companies',
        sa.Column('company_id', sa.String(), nullable=False),
        sa.Column('company_name', sa.String(), nullable=False),
        sa.Column('tax_id', sa.String(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('fiscal_year_end', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('company_id')
    )

    # User-Company Links
    op.create_table('user_company_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('company_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_company_links_company_id'), 'user_company_links', ['company_id'], unique=False)
    op.create_index(op.f('ix_user_company_links_user_id'), 'user_company_links', ['user_id'], unique=False)

    # Transactions
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('txn_id', sa.String(), nullable=False),
        sa.Column('company_id', sa.String(), nullable=False),
        sa.Column('date', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('counterparty', sa.String(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('raw', sa.JSON(), nullable=True),
        sa.Column('source_type', sa.String(), nullable=True),
        sa.Column('source_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('txn_id')
    )
    op.create_index(op.f('ix_transactions_company_id'), 'transactions', ['company_id'], unique=False)
    op.create_index(op.f('ix_transactions_date'), 'transactions', ['date'], unique=False)

    # Chart of Accounts
    op.create_table('chart_of_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.String(), nullable=False),
        sa.Column('account_code', sa.String(), nullable=False),
        sa.Column('account_name', sa.String(), nullable=False),
        sa.Column('account_type', sa.String(), nullable=True),
        sa.Column('parent_account', sa.String(), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chart_of_accounts_company_id'), 'chart_of_accounts', ['company_id'], unique=False)

    # Journal Entries
    op.create_table('journal_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('je_id', sa.String(), nullable=False),
        sa.Column('company_id', sa.String(), nullable=False),
        sa.Column('transaction_id', sa.String(), nullable=True),
        sa.Column('date', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('lines', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('je_id')
    )
    op.create_index(op.f('ix_journal_entries_company_id'), 'journal_entries', ['company_id'], unique=False)

    # Reconciliation Matches
    op.create_table('reconciliation_matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.String(), nullable=False),
        sa.Column('transaction_id', sa.String(), nullable=True),
        sa.Column('journal_entry_id', sa.String(), nullable=True),
        sa.Column('match_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Open Data Ingestion Logs (Sprint 5)
    op.create_table('open_data_ingestion_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_name', sa.String(), nullable=False),
        sa.Column('source_type', sa.String(), nullable=True),
        sa.Column('record_count', sa.Integer(), nullable=True),
        sa.Column('records_imported', sa.Integer(), nullable=True),
        sa.Column('errors', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('ingestion_metadata', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Model Training Logs (Sprint 5)
    op.create_table('model_training_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('records_used', sa.Integer(), nullable=True),
        sa.Column('train_records', sa.Integer(), nullable=True),
        sa.Column('test_records', sa.Integer(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('precision_score', sa.Float(), nullable=True),
        sa.Column('recall', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('model_metadata', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Model Retrain Events (Sprint 7)
    op.create_table('model_retrain_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('reason_json', sa.JSON(), nullable=True),
        sa.Column('train_records', sa.Integer(), nullable=True),
        sa.Column('valid_records', sa.Integer(), nullable=True),
        sa.Column('acc_old', sa.Float(), nullable=True),
        sa.Column('acc_new', sa.Float(), nullable=True),
        sa.Column('f1_old', sa.Float(), nullable=True),
        sa.Column('f1_new', sa.Float(), nullable=True),
        sa.Column('promoted', sa.Integer(), nullable=True),
        sa.Column('artifact_path', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Rule Versions (Sprint 8)
    op.create_table('rule_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('author', sa.String(), nullable=True),
        sa.Column('path', sa.String(), nullable=False),
        sa.Column('rule_count', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version')
    )
    op.create_index(op.f('ix_rule_versions_created_at'), 'rule_versions', ['created_at'], unique=False)

    # Rule Candidates (Sprint 8)
    op.create_table('rule_candidates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vendor_normalized', sa.String(), nullable=False),
        sa.Column('pattern', sa.String(), nullable=True),
        sa.Column('suggested_account', sa.String(), nullable=False),
        sa.Column('obs_count', sa.Integer(), nullable=True),
        sa.Column('avg_confidence', sa.Float(), nullable=True),
        sa.Column('variance', sa.Float(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.Column('reasons_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('decided_by', sa.String(), nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rule_candidates_vendor_normalized'), 'rule_candidates', ['vendor_normalized'], unique=False)
    op.create_index(op.f('ix_rule_candidates_status'), 'rule_candidates', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_rule_candidates_status'), table_name='rule_candidates')
    op.drop_index(op.f('ix_rule_candidates_vendor_normalized'), table_name='rule_candidates')
    op.drop_table('rule_candidates')
    op.drop_index(op.f('ix_rule_versions_created_at'), table_name='rule_versions')
    op.drop_table('rule_versions')
    op.drop_table('model_retrain_events')
    op.drop_table('model_training_logs')
    op.drop_table('open_data_ingestion_logs')
    op.drop_table('reconciliation_matches')
    op.drop_index(op.f('ix_journal_entries_company_id'), table_name='journal_entries')
    op.drop_table('journal_entries')
    op.drop_index(op.f('ix_chart_of_accounts_company_id'), table_name='chart_of_accounts')
    op.drop_table('chart_of_accounts')
    op.drop_index(op.f('ix_transactions_date'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_company_id'), table_name='transactions')
    op.drop_table('transactions')
    op.drop_index(op.f('ix_user_company_links_user_id'), table_name='user_company_links')
    op.drop_index(op.f('ix_user_company_links_company_id'), table_name='user_company_links')
    op.drop_table('user_company_links')
    op.drop_table('companies')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
