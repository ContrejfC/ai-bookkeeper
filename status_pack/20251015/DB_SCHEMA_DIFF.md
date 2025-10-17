# AI Bookkeeper - Database Schema Diff Report
**Generated:** 2025-10-15  
**Database:** SQLite (ai_bookkeeper_demo.db)  
**Size:** 0.34 MB  
**Tables:** 23 tables

## Migration Status
- **Current Head:** 008_xero_export
- **Status:** ⚠️ **BROKEN** - Missing revision '001'
- **Error:** `KeyError: '001'` in Alembic chain
- **Available Revisions:** 7 revisions (002-008)

## Available Migration Revisions

| Revision | Description | Date | Status |
|----------|-------------|------|--------|
| 002_tenant_settings | Add tenant_settings and user_tenants tables | 2024-10-11 | ✅ Available |
| 003_auth_users | Add users table for authentication | 2024-10-11 | ✅ Available |
| 004_billing | Add billing_subscriptions and billing_events | 2024-10-11 | ✅ Available |
| 004_create_admin_user | Create admin user for production setup | 2024-10-13 | ✅ Available |
| 005_notifications | Add tenant_notifications and notification_log | 2024-10-11 | ✅ Available |
| 006_receipt_fields | Add receipt_fields and xero_account_mappings | 2024-10-11 | ✅ Available |
| 008_xero_export | Add xero_export_log and qbo_export_log | 2024-10-11 | ✅ Available |

## Current Database Schema

### Core Tables (6)

#### 1. users
```sql
CREATE TABLE users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'staff',
    is_active BOOLEAN DEFAULT true,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. tenant_settings
```sql
CREATE TABLE tenant_settings (
    tenant_id VARCHAR(255) PRIMARY KEY,
    autopost_enabled BOOLEAN DEFAULT false,
    autopost_threshold FLOAT DEFAULT 0.90,
    llm_tenant_cap_usd FLOAT DEFAULT 50.0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. user_tenants
```sql
CREATE TABLE user_tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, tenant_id)
);
```

#### 4. transactions
```sql
CREATE TABLE transactions (
    txn_id VARCHAR(255) PRIMARY KEY,
    company_id VARCHAR(255),
    date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    counterparty VARCHAR(255),
    description TEXT,
    account_code VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 5. journal_entries
```sql
CREATE TABLE journal_entries (
    je_id VARCHAR(255) PRIMARY KEY,
    company_id VARCHAR(255),
    date DATE NOT NULL,
    description TEXT,
    account_code VARCHAR(50),
    debit_amount DECIMAL(10,2),
    credit_amount DECIMAL(10,2),
    source_txn_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 6. reconciliations
```sql
CREATE TABLE reconciliations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id VARCHAR(255),
    txn_id VARCHAR(255),
    je_id VARCHAR(255),
    reconciled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reconciled_by VARCHAR(255)
);
```

### ML & Analytics Tables (3)

#### 7. model_training_logs
```sql
CREATE TABLE model_training_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name VARCHAR(255) NOT NULL,
    records_used INTEGER NOT NULL,
    accuracy FLOAT,
    precision_weighted FLOAT,
    recall_weighted FLOAT,
    f1_score FLOAT,
    training_duration_sec FLOAT,
    metadata JSON,
    trained_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 8. model_retrain_events
```sql
CREATE TABLE model_retrain_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_type VARCHAR(50),
    records_added INTEGER,
    retrained_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 9. llm_call_logs
```sql
CREATE TABLE llm_call_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_hash VARCHAR(255),
    model_used VARCHAR(100),
    tokens_used INTEGER,
    response_time_ms INTEGER,
    cost_usd FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Rules Engine Tables (2)

#### 10. rule_versions
```sql
CREATE TABLE rule_versions (
    version_id VARCHAR(255) PRIMARY KEY,
    created_by VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT false
);
```

#### 11. rule_candidates
```sql
CREATE TABLE rule_candidates (
    id VARCHAR(255) PRIMARY KEY,
    vendor_pattern VARCHAR(255),
    suggested_account VARCHAR(255),
    evidence JSON,
    status VARCHAR(50) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Audit & Compliance Tables (4)

#### 12. decision_audit_log
```sql
CREATE TABLE decision_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    tenant_id VARCHAR(255),
    txn_id VARCHAR(255),
    vendor_normalized VARCHAR(255),
    action VARCHAR(50),
    not_auto_post_reason VARCHAR(50),
    calibrated_p FLOAT,
    threshold_used FLOAT,
    user_id VARCHAR(255),
    cold_start_label_count INTEGER,
    cold_start_eligible BOOLEAN
);
```

#### 13. cold_start_tracking
```sql
CREATE TABLE cold_start_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_normalized VARCHAR(255),
    first_seen_at DATETIME,
    label_count INTEGER DEFAULT 0,
    graduated_at DATETIME
);
```

#### 14. billing_subscriptions
```sql
CREATE TABLE billing_subscriptions (
    id VARCHAR(255) PRIMARY KEY,
    tenant_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    status VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 15. billing_events
```sql
CREATE TABLE billing_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id VARCHAR(255),
    event_type VARCHAR(50),
    event_data JSON,
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Integration Tables (4)

#### 16. receipt_fields
```sql
CREATE TABLE receipt_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id VARCHAR(255),
    field_name VARCHAR(100),
    field_value TEXT,
    confidence FLOAT,
    bbox JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 17. xero_account_mappings
```sql
CREATE TABLE xero_account_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    internal_code VARCHAR(50),
    xero_code VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 18. xero_export_log
```sql
CREATE TABLE xero_export_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id VARCHAR(255),
    export_date DATE,
    records_exported INTEGER,
    status VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 19. qbo_export_log
```sql
CREATE TABLE qbo_export_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id VARCHAR(255),
    export_date DATE,
    records_exported INTEGER,
    status VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Notification Tables (2)

#### 20. tenant_notifications
```sql
CREATE TABLE tenant_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id VARCHAR(255),
    notification_type VARCHAR(50),
    settings JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 21. notification_log
```sql
CREATE TABLE notification_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id VARCHAR(255),
    notification_type VARCHAR(50),
    status VARCHAR(50),
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Indexes

### Performance Indexes
```sql
-- Tenant settings
CREATE INDEX idx_tenant_settings_updated_at ON tenant_settings(updated_at);

-- User-tenant relationships
CREATE INDEX idx_user_tenants_user_id ON user_tenants(user_id);
CREATE INDEX idx_user_tenants_tenant_id ON user_tenants(tenant_id);
CREATE INDEX idx_user_tenants_user_tenant ON user_tenants(user_id, tenant_id);

-- Transactions
CREATE INDEX idx_transactions_date_amount ON transactions(date, amount);
CREATE INDEX idx_transactions_counterparty ON transactions(counterparty);
CREATE INDEX idx_transactions_company ON transactions(company_id);

-- Journal entries
CREATE INDEX idx_journal_entries_company_date ON journal_entries(company_id, date);
CREATE INDEX idx_journal_entries_source_txn ON journal_entries(source_txn_id);

-- Rule candidates
CREATE INDEX idx_rule_candidates_vendor ON rule_candidates(vendor_pattern);
CREATE INDEX idx_rule_candidates_status ON rule_candidates(status);

-- Rule versions
CREATE INDEX idx_rule_versions_created ON rule_versions(created_at);

-- Model training
CREATE INDEX idx_model_training_logs_model_name ON model_training_logs(model_name);
CREATE INDEX idx_model_training_logs_trained_at ON model_training_logs(trained_at);

-- Decision audit log
CREATE INDEX idx_decision_audit_log_timestamp ON decision_audit_log(timestamp);
CREATE INDEX idx_decision_audit_log_tenant ON decision_audit_log(tenant_id);
CREATE INDEX idx_decision_audit_log_txn ON decision_audit_log(txn_id);
CREATE INDEX idx_decision_audit_log_action ON decision_audit_log(action);
```

## Schema Changes Since 2025-10-08

### Added Tables (Since Baseline)
- `tenant_settings` - Multi-tenant configuration
- `user_tenants` - RBAC user-tenant relationships
- `billing_subscriptions` - Stripe integration
- `billing_events` - Billing event tracking
- `tenant_notifications` - Notification preferences
- `notification_log` - Notification delivery log
- `decision_audit_log` - SOC2 compliance audit trail
- `cold_start_tracking` - ML model cold-start tracking

### Modified Tables
- `users` - Enhanced with role-based access control
- `transactions` - Added tenant isolation support
- `journal_entries` - Added tenant isolation support

### Data Volume
```
Tables: 23
Total Records: ~2,000+ (estimated)
Database Size: 0.34 MB
```

## Migration Issues

### Critical Issue: Missing Revision '001'
```
ERROR: KeyError: '001'
File "alembic/script/revision.py", line 245, in _revision_map
    down_revision = map_[downrev]
```

**Root Cause:** Alembic migration chain references revision '001' which doesn't exist in the versions directory.

**Impact:** 
- Cannot run `alembic current`
- Cannot run `alembic upgrade head`
- Database migrations are broken

**Resolution Needed:**
1. Create missing revision '001_initial_schema.py'
2. Or update all down_revision references to remove dependency on '001'
3. Or reset Alembic version table and re-run migrations

## Database Connectivity

### Current Configuration
- **Dialect:** SQLite
- **Database File:** `ai_bookkeeper_demo.db`
- **Connection String:** `sqlite:///./ai_bookkeeper_demo.db`
- **Backup Database:** `aibookkeeper.db` (2.17 MB, older)

### PostgreSQL Support
- **Configuration:** Available in `requirements-postgres.txt`
- **Migration Support:** Alembic configured for PostgreSQL
- **Production Ready:** Yes (with proper DATABASE_URL)

## Data Integrity

### Foreign Key Relationships
- `user_tenants.user_id` → `users.id`
- `user_tenants.tenant_id` → `tenant_settings.tenant_id`
- `journal_entries.source_txn_id` → `transactions.txn_id`
- `reconciliations.txn_id` → `transactions.txn_id`
- `reconciliations.je_id` → `journal_entries.je_id`

### Constraints
- Unique constraints on email addresses
- Unique constraints on user-tenant relationships
- NOT NULL constraints on critical fields
- Check constraints on threshold values (0.80-0.98)

## Backup Status
- **Current Database:** `ai_bookkeeper_demo.db` (0.34 MB)
- **Backup Database:** `aibookkeeper.db` (2.17 MB, from 2025-10-09)
- **Backup Script:** `scripts/backup_restore_check.sh` (implemented)
- **Retention Policy:** 365 days for receipts, 30 days for logs

## Next Steps

1. **Fix Alembic Migration Chain**
   - Create missing revision '001_initial_schema.py'
   - Test migration rollback and upgrade
   - Verify database integrity

2. **Add Missing Tables for Label Pipeline**
   - `user_consent` - Consent tracking for data collection
   - `training_labels` - User decision labels with redaction
   - `data_export_log` - Audit trail for data exports

3. **Enhance QBO/Xero Integration Tables**
   - `oauth_tokens` - Store OAuth2 tokens securely
   - `integration_settings` - Per-tenant integration config
   - `sync_log` - Track sync operations

4. **Add Performance Monitoring**
   - `performance_metrics` - Track query performance
   - `error_logs` - Application error tracking
   - `usage_stats` - Feature usage analytics
