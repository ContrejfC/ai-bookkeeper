"""Database models (SQLAlchemy ORM)."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class TenantSettingsDB(Base):
    """Tenant settings for Wave-2 Phase 1 (de-mocked)."""
    __tablename__ = 'tenant_settings'
    
    tenant_id = Column(String(255), primary_key=True)
    autopost_enabled = Column(Boolean, nullable=False, server_default='false')
    autopost_threshold = Column(Float, nullable=False, server_default='0.90')
    llm_tenant_cap_usd = Column(Float, nullable=False, server_default='50.0')
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_tenant_settings_updated_at', 'updated_at'),
    )


class UserDB(Base):
    """User accounts for JWT authentication (Wave-2 Phase 1)."""
    __tablename__ = 'users'
    
    user_id = Column(String(255), primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=True)  # NULL for magic link only
    role = Column(String(50), nullable=False)  # 'owner' or 'staff'
    is_active = Column(Boolean, nullable=False, server_default='true')
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    last_login_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_users_email', 'email', unique=True),
        Index('idx_users_role', 'role'),
    )


class UserTenantDB(Base):
    """User-tenant assignment for RBAC (Wave-2 Phase 1)."""
    __tablename__ = 'user_tenants'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False)
    tenant_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_user_tenants_user_id', 'user_id'),
        Index('idx_user_tenants_tenant_id', 'tenant_id'),
        Index('idx_user_tenants_user_tenant', 'user_id', 'tenant_id', unique=True),
    )


class BillingSubscriptionDB(Base):
    """Billing subscriptions (Phase 2a - Billing)."""
    __tablename__ = 'billing_subscriptions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(255), nullable=False, unique=True)
    plan = Column(String(50), nullable=False)  # starter, pro, firm
    status = Column(String(50), nullable=False)  # active, past_due, canceled, trialing
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, nullable=False, server_default='false')
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_billing_subs_tenant', 'tenant_id', unique=True),
        Index('idx_billing_subs_status', 'status'),
        Index('idx_billing_subs_stripe_customer', 'stripe_customer_id'),
    )


class BillingEventDB(Base):
    """Billing webhook events audit log (Phase 2a - Billing)."""
    __tablename__ = 'billing_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(100), nullable=False)
    stripe_event_id = Column(String(255), nullable=True, unique=True)
    payload_json = Column(JSON, nullable=False)
    processed = Column(Boolean, nullable=False, server_default='false')
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_billing_events_type', 'type'),
        Index('idx_billing_events_processed', 'processed'),
        Index('idx_billing_events_stripe_id', 'stripe_event_id', unique=True),
    )


class TenantNotificationDB(Base):
    """Tenant notification settings (Phase 2a - Notifications)."""
    __tablename__ = 'tenant_notifications'
    
    tenant_id = Column(String(255), primary_key=True)
    email = Column(String(255), nullable=True)
    slack_webhook_url = Column(Text, nullable=True)
    alerts_json = Column(JSON, nullable=False, server_default='{}')
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_by = Column(String(255), nullable=True)
    
    __table_args__ = (
        Index('idx_tenant_notifications_tenant', 'tenant_id', unique=True),
    )


class NotificationLogDB(Base):
    """Notification audit log (Phase 2a - Notifications)."""
    __tablename__ = 'notification_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(255), nullable=False)
    channel = Column(String(50), nullable=False)  # 'email' or 'slack'
    type = Column(String(100), nullable=False)     # e.g. 'psi_alert'
    payload_json = Column(JSON, nullable=False)
    sent = Column(Boolean, nullable=False, server_default='false')
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_notif_log_tenant_type', 'tenant_id', 'type', 'created_at'),
        Index('idx_notif_log_sent', 'sent'),
    )


class ReceiptFieldDB(Base):
    """Receipt field bounding boxes (Phase 2b - Receipt Highlights)."""
    __tablename__ = 'receipt_fields'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    receipt_id = Column(String(255), nullable=False)
    field = Column(String(50), nullable=False)  # date, amount, vendor, total
    page = Column(Integer, nullable=False, server_default='0')
    x = Column(Float, nullable=False)  # Normalized 0-1
    y = Column(Float, nullable=False)  # Normalized 0-1
    w = Column(Float, nullable=False)  # Normalized 0-1
    h = Column(Float, nullable=False)  # Normalized 0-1
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_receipt_fields_receipt', 'receipt_id'),
        Index('idx_receipt_fields_field', 'field'),
    )


class XeroMappingDB(Base):
    """Xero account mapping: internal → Xero (Sprint 11.2)."""
    __tablename__ = 'xero_account_mappings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    internal_account = Column(String(100), nullable=False)
    xero_account_code = Column(String(100), nullable=False)
    xero_account_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_xero_mapping_tenant_internal', 'tenant_id', 'internal_account'),
    )


class XeroExportLogDB(Base):
    """Xero export log (Sprint 11.2)."""
    __tablename__ = 'xero_export_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    journal_entry_id = Column(String(255), nullable=False, index=True)
    external_id = Column(String(64), nullable=False, index=True)
    xero_journal_id = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)  # posted, skipped, failed
    error_message = Column(Text, nullable=True)
    exported_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_xero_export_tenant', 'tenant_id'),
        Index('idx_xero_export_external_id', 'external_id'),
    )


class TransactionDB(Base):
    """Bank transaction."""
    __tablename__ = 'transactions'
    
    txn_id = Column(String(255), primary_key=True)
    date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default='USD')
    description = Column(Text, nullable=True)
    counterparty = Column(String(255), nullable=True)
    raw = Column(Text, nullable=True)
    doc_ids = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_transactions_date', 'date'),
        Index('idx_transactions_counterparty', 'counterparty'),
    )


class JournalEntryDB(Base):
    """Journal entry (proposed or posted)."""
    __tablename__ = 'journal_entries'
    
    je_id = Column(String(255), primary_key=True)
    date = Column(DateTime, nullable=False)
    lines = Column(JSON, nullable=False)  # List of {account, debit, credit}
    source_txn_id = Column(String(255), nullable=True)
    memo = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    status = Column(String(50), nullable=False, default='proposed')  # proposed, approved, posted
    needs_review = Column(Integer, nullable=False, default=0)  # 0 or 1
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_journal_entries_date', 'date'),
        Index('idx_journal_entries_status', 'status'),
        Index('idx_journal_entries_source_txn', 'source_txn_id'),
    )


class ReconciliationDB(Base):
    """Reconciliation match between transaction and journal entry."""
    __tablename__ = 'reconciliations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    txn_id = Column(String(255), nullable=False)
    je_id = Column(String(255), nullable=False)
    match_confidence = Column(Float, nullable=True)
    matched_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_reconciliations_txn', 'txn_id'),
        Index('idx_reconciliations_je', 'je_id'),
    )


class ModelTrainingLogDB(Base):
    """Log of ML model training runs (Sprint 5)."""
    __tablename__ = 'model_training_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(255), nullable=False)
    records_used = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=True)
    precision_weighted = Column(Float, nullable=True)
    recall_weighted = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    training_duration_sec = Column(Float, nullable=True)
    training_metadata = Column("metadata", JSON, nullable=True)
    trained_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_model_training_logs_model_name', 'model_name'),
        Index('idx_model_training_logs_trained_at', 'trained_at'),
    )


class ModelRetrainEventDB(Base):
    """Log of auto-retraining events (Sprint 7)."""
    __tablename__ = 'model_retrain_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    reason = Column(String(255), nullable=False)
    old_model_version = Column(String(255), nullable=True)
    new_model_version = Column(String(255), nullable=False)
    old_metrics = Column(JSON, nullable=True)
    new_metrics = Column(JSON, nullable=False)
    promoted = Column(Boolean, nullable=False)
    event_time = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_model_retrain_events_time', 'event_time'),
    )


class RuleVersionDB(Base):
    """Version history for adaptive rules (Sprint 8)."""
    __tablename__ = 'rule_versions'
    
    version_id = Column(String(255), primary_key=True)
    rules_yaml = Column(Text, nullable=False)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    is_active = Column(Boolean, nullable=False, default=False)
    
    __table_args__ = (
        Index('idx_rule_versions_created_at', 'created_at'),
        Index('idx_rule_versions_active', 'is_active'),
    )


class RuleCandidateDB(Base):
    """Rule candidates from evidence aggregation (Sprint 8)."""
    __tablename__ = 'rule_candidates'
    
    id = Column(String(255), primary_key=True)
    vendor_pattern = Column(String(255), nullable=False)
    suggested_account = Column(String(255), nullable=False)
    evidence_count = Column(Integer, nullable=False, default=0)
    evidence_precision = Column(Float, nullable=False, default=0.0)
    evidence_std_dev = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default='pending')  # pending, accepted, rejected
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_rule_candidates_status', 'status'),
        Index('idx_rule_candidates_vendor', 'vendor_pattern'),
    )


class DecisionAuditLogDB(Base):
    """Audit log for decision reasons (Stage D/E)."""
    __tablename__ = 'decision_audit_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    tenant_id = Column(String(255), nullable=True)
    txn_id = Column(String(255), nullable=True)
    vendor_normalized = Column(String(255), nullable=True)
    action = Column(String(50), nullable=True)  # auto_posted, reviewed, approved, rejected
    not_auto_post_reason = Column(String(50), nullable=True)
    calibrated_p = Column(Float, nullable=True)
    threshold_used = Column(Float, nullable=True)
    user_id = Column(String(255), nullable=True)
    cold_start_label_count = Column(Integer, nullable=True)
    cold_start_eligible = Column(Boolean, nullable=True)
    
    __table_args__ = (
        Index('idx_decision_audit_log_timestamp', 'timestamp'),
        Index('idx_decision_audit_log_tenant', 'tenant_id'),
        Index('idx_decision_audit_log_txn', 'txn_id'),
        Index('idx_decision_audit_log_action', 'action'),
    )


class ColdStartTrackingDB(Base):
    """Cold-start vendor tracking (Stage D)."""
    __tablename__ = 'cold_start_tracking'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(255), nullable=False)
    vendor_normalized = Column(String(255), nullable=False)
    suggested_account = Column(String(255), nullable=False)
    label_count = Column(Integer, nullable=False, default=0)
    consistent = Column(Boolean, nullable=False, default=False)
    last_seen = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_cold_start_tenant_vendor', 'tenant_id', 'vendor_normalized', unique=True),
    )


class QBOExportLogDB(Base):
    """QBO export log for idempotency (Stage F)."""
    __tablename__ = 'qbo_export_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(64), nullable=False, unique=True)  # SHA-256 first 32 hex
    je_id = Column(String(255), nullable=False)
    exported_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_qbo_export_log_external_id', 'external_id', unique=True),
        Index('idx_qbo_export_log_je_id', 'je_id'),
    )


class LLMCallLogDB(Base):
    """LLM call tracking for budget management (Stage G)."""
    __tablename__ = 'llm_call_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(255), nullable=False)
    txn_id = Column(String(255), nullable=True)
    call_type = Column(String(50), nullable=False)  # categorize, extract, etc.
    model = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    cost_usd = Column(Float, nullable=False, default=0.0)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_llm_call_logs_tenant', 'tenant_id'),
        Index('idx_llm_call_logs_timestamp', 'timestamp'),
    )


class EntitlementDB(Base):
    """Tenant entitlements and subscription details."""
    __tablename__ = 'entitlements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(255), nullable=False)
    plan = Column(String(50), nullable=False)  # starter, pro, firm
    active = Column(Boolean, nullable=False, server_default='false')
    tx_cap = Column(Integer, nullable=False, server_default='300')
    bulk_approve = Column(Boolean, nullable=False, server_default='false')
    included_companies = Column(Integer, nullable=False, server_default='1')
    trial_ends_at = Column(DateTime, nullable=True)
    subscription_status = Column(String(50), nullable=True)  # active, trialing, past_due, canceled
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_entitlements_tenant_id', 'tenant_id'),
        Index('idx_entitlements_active', 'active'),
        Index('idx_entitlements_plan', 'plan'),
    )


class UsageMonthlyDB(Base):
    """Monthly usage tracking for billing."""
    __tablename__ = 'usage_monthly'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(255), nullable=False)
    year_month = Column(String(7), nullable=False)  # Format: YYYY-MM
    tx_analyzed = Column(Integer, nullable=False, server_default='0')
    tx_posted = Column(Integer, nullable=False, server_default='0')
    last_reset_at = Column(DateTime, nullable=False, server_default=func.now())
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_usage_monthly_tenant_month', 'tenant_id', 'year_month', unique=True),
        Index('idx_usage_monthly_year_month', 'year_month'),
    )


class UsageDailyDB(Base):
    """Daily usage tracking for free tier limits."""
    __tablename__ = 'usage_daily'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(255), nullable=False)
    date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    analyze_count = Column(Integer, nullable=False, server_default='0')
    explain_count = Column(Integer, nullable=False, server_default='0')
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_usage_daily_tenant_date', 'tenant_id', 'date', unique=True),
        Index('idx_usage_daily_date', 'date'),
    )


class QBOTokenDB(Base):
    """QuickBooks Online OAuth tokens."""
    __tablename__ = 'qbo_tokens'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(255), nullable=False)
    realm_id = Column(String(255), nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    scope = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_qbo_tokens_tenant_id', 'tenant_id', unique=True),
        Index('idx_qbo_tokens_realm_id', 'realm_id'),
        Index('idx_qbo_tokens_expires_at', 'expires_at'),
    )


class JEIdempotencyDB(Base):
    """Journal entry idempotency tracking for QBO posting."""
    __tablename__ = 'je_idempotency'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(255), nullable=False)
    payload_hash = Column(String(64), nullable=False)  # SHA-256 hex
    qbo_doc_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_je_idempotency_tenant_hash', 'tenant_id', 'payload_hash', unique=True),
        Index('idx_je_idempotency_tenant_id', 'tenant_id'),
        Index('idx_je_idempotency_qbo_doc_id', 'qbo_doc_id'),
    )


# Import other models as needed for completeness
Transaction = TransactionDB
JournalEntry = JournalEntryDB
JournalEntryLine = dict  # Stored as JSON in JournalEntry
