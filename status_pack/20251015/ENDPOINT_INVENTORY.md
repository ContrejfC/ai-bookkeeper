# AI Bookkeeper - Endpoint Inventory
**Generated:** 2025-10-15  
**OpenAPI Version:** 3.1.0  
**Total Endpoints:** 33+ REST endpoints

## Authentication Endpoints (`/api/auth`)

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| POST | `/api/auth/login` | Issue JWT token | No | `{"email": "user@example.com", "password": "pass"}` | `{"success": true, "user_id": "123", "token": "jwt..."}` | 401, 422 |
| POST | `/api/auth/signup` | Create user account | No | `{"email": "user@example.com", "password": "pass", "full_name": "User"}` | `{"success": true, "user_id": "123"}` | 422, 500 |
| GET | `/api/auth/signup/test` | Test signup route | No | - | `{"message": "Signup route working"}` | - |
| POST | `/api/auth/logout` | Clear session cookie | No | - | `{"message": "Logged out"}` | - |
| GET | `/api/auth/me` | Get current user info | Yes (Cookie/Header) | - | `{"user_id": "123", "email": "user@example.com", "role": "owner", "tenants": []}` | 401, 422 |

## Tenant Management (`/api/tenants`)

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| GET | `/api/tenants` | List visible tenants | Yes (RBAC) | - | `[{"id": "tenant1", "name": "Company", "tier": "pro"}]` | 401, 422 |
| GET | `/api/tenants/{tenant_id}` | Get tenant details | Yes (RBAC) | - | `{"id": "tenant1", "autopost_enabled": false}` | 401, 404, 422 |
| POST | `/api/tenants/{tenant_id}/settings` | Update tenant settings | Yes (Owner only) | `{"autopost_threshold": 0.95}` | `{"success": true}` | 401, 403, 422 |

## Rules Management (`/api/rules`)

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| GET | `/api/rules/candidates` | List rule candidates | Yes | `?status=pending` | `[{"id": "rule1", "vendor_pattern": "AMAZON", "status": "pending"}]` | 401, 422 |
| POST | `/api/rules/dryrun` | Simulate rule impact | Yes | `{"candidate_ids": ["rule1"], "tenant_id": "tenant1"}` | `{"before": {...}, "after": {...}}` | 401, 422 |
| POST | `/api/rules/candidates/{id}/accept` | Promote candidate | Yes | - | `{"success": true, "version_id": "v1"}` | 401, 404, 422 |
| POST | `/api/rules/candidates/{id}/reject` | Decline candidate | Yes | `?reason=duplicate` | `{"success": true}` | 401, 404, 422 |
| POST | `/api/rules/rollback` | Rollback to version | Yes | `?to_version=v1` | `{"success": true}` | 401, 404, 422 |
| GET | `/api/rules/versions` | List rule versions | Yes | - | `[{"version_id": "v1", "created_at": "2025-10-15", "is_active": true}]` | 401, 422 |

## Audit & Compliance (`/api/audit`)

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| GET | `/api/audit/export.csv` | Stream audit log as CSV | Yes | `?start_ts=2025-10-01&tenant_id=tenant1` | CSV stream | 401, 422 |

## Billing & Subscriptions (`/api/billing`)

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| POST | `/api/billing/create_checkout_session` | Create Stripe checkout | Yes (Owner) | `{"tenant_id": "tenant1", "plan": "pro"}` | `{"checkout_url": "https://checkout.stripe.com/..."}` | 401, 403, 422 |
| GET | `/api/billing/portal_link` | Get customer portal | Yes (Owner) | `?tenant_id=tenant1` | `{"portal_url": "https://billing.stripe.com/..."}` | 401, 403, 422 |
| POST | `/api/billing/stripe_webhook` | Handle Stripe events | No (Webhook) | Stripe webhook payload | `{"received": true}` | - |

## Notifications (`/api/notifications`)

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| GET | `/api/notifications/settings` | Get notification settings | Yes (RBAC) | `?tenant_id=tenant1` | `{"email": "admin@example.com", "psi_alert": true}` | 401, 422 |
| POST | `/api/notifications/settings` | Update settings | Yes (Owner only) | `{"tenant_id": "tenant1", "psi_alert": true}` | `{"success": true}` | 401, 403, 422 |
| POST | `/api/notifications/test` | Send test notification | Yes (Owner only) | `{"tenant_id": "tenant1", "channel": "email"}` | `{"sent": true}` | 401, 403, 422 |

## Onboarding (`/api/onboarding`)

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| POST | `/api/onboarding/complete` | Complete onboarding | Yes (Owner) | Multipart form with CoA file | `{"success": true}` | 401, 403, 422 |

## Receipts (`/api/receipts`)

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| GET | `/api/receipts/` | List receipts | Yes | `?tenant_id=tenant1` | `[{"receipt_id": "r1", "filename": "receipt.pdf"}]` | 401, 422 |
| GET | `/api/receipts/{receipt_id}/fields` | Get OCR fields | Yes | - | `[{"field": "total", "bbox": [0.1, 0.2, 0.3, 0.4]}]` | 401, 404, 422 |
| GET | `/api/receipts/{receipt_id}/pdf` | Serve receipt PDF | Yes | - | PDF binary | 401, 404, 422 |

## Analytics (`/api/analytics`)

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| GET | `/api/analytics/last7` | Get last 7 days reports | Yes | - | `[{"date": "2025-10-15", "automation_rate": 0.85}]` | 401, 422 |
| GET | `/api/analytics/events/types` | Get event types | Yes | - | `{"transaction_reviewed": "Transaction reviewed by user"}` | 401, 422 |

## Core Business Logic

### Transaction Processing (`/api/upload`, `/api/post`)

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| POST | `/api/upload` | Upload bank statement | Yes | Multipart file upload | `{"job_id": "job123", "transactions": 150}` | 401, 422 |
| POST | `/api/post/propose` | Generate journal entries | Yes | `["txn1", "txn2"]` | `[{"je_id": "je1", "account": "Office Supplies"}]` | 401, 422 |
| POST | `/api/post/approve` | Approve/post journal entries | Yes | `["je1", "je2"]` | `{"approved": 2, "posted": 2}` | 401, 422 |

### Chart of Accounts (`/api/chart-of-accounts`)

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| GET | `/api/chart-of-accounts` | Get chart of accounts | Yes | - | `[{"account": "1000", "name": "Cash", "type": "Asset"}]` | 401, 422 |

### Reconciliation (`/api/reconcile`)

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| POST | `/api/reconcile/run` | Run reconciliation | Yes | - | `{"matched": 145, "unmatched": 5}` | 401, 422 |
| GET | `/api/reconcile/unmatched` | Get unmatched items | Yes | - | `{"transactions": [], "journal_entries": []}` | 401, 422 |

## Export/Import (`/api/export`, `/api/import`)

### Export Endpoints

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| GET | `/api/export/journal-entries` | Export JEs as CSV | Yes | `?status=posted` | CSV download | 401, 422 |
| GET | `/api/export/reconciliation` | Export recon results | Yes | - | CSV download | 401, 422 |
| GET | `/api/export/general-ledger` | Export general ledger | Yes | `?start_date=2025-10-01` | CSV download | 401, 422 |
| GET | `/api/export/trial-balance` | Export trial balance | Yes | `?as_of_date=2025-10-15` | CSV download | 401, 422 |
| POST | `/api/export/quickbooks` | Export to QuickBooks | Yes | `?format=iif&status=posted` | IIF/CSV download | 401, 422 |
| POST | `/api/export/xero` | Export to Xero | Yes | `?status=posted` | CSV download | 401, 422 |

### Import Endpoints

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| POST | `/api/import/quickbooks` | Import QBO chart | Yes | Multipart file upload | `{"imported": 25, "errors": []}` | 401, 422 |
| POST | `/api/import/xero` | Import Xero chart | Yes | Multipart file upload | `{"imported": 30, "errors": []}` | 401, 422 |

## Financial Reports (`/api/analytics`)

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| GET | `/api/analytics/pnl` | Profit & Loss statement | Yes | `?company_id=c1&start_date=2025-10-01` | `{"revenue": 50000, "expenses": 30000}` | 401, 422 |
| GET | `/api/analytics/balance-sheet` | Balance sheet | Yes | `?company_id=c1&as_of_date=2025-10-15` | `{"assets": 100000, "liabilities": 20000}` | 401, 422 |
| GET | `/api/analytics/cashflow` | Cash flow statement | Yes | `?company_id=c1&start_date=2025-10-01` | `{"operating": 25000, "investing": -5000}` | 401, 422 |
| GET | `/api/analytics/automation-metrics` | Automation stats | Yes | `?company_id=c1&days=30` | `{"automation_rate": 0.85, "accuracy": 0.92}` | 401, 422 |
| GET | `/api/analytics/automation-trend` | Automation trend | Yes | `?company_id=c1&days=90` | `[{"date": "2025-10-15", "rate": 0.85}]` | 401, 422 |

## Job Queue (`/api/jobs`)

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| GET | `/api/jobs/{job_id}` | Get job status | Yes | - | `{"status": "completed", "progress": 100}` | 401, 404, 422 |
| GET | `/api/jobs/company/{company_id}` | List company jobs | Yes | `?limit=50` | `[{"job_id": "job1", "status": "running"}]` | 401, 404, 422 |

## Setup (`/api/setup`)

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| POST | `/api/setup/create-admin` | Create admin user | No (Setup only) | - | `{"admin_created": true}` | 422 |

## Health & Status

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| GET | `/healthz` | Health check | No | - | `{"status": "healthy", "version": "0.2.1-beta"}` | - |
| GET | `/readyz` | Readiness check | No | - | `{"status": "ready", "components": {...}}` | - |
| GET | `/health` | Legacy health check | No | - | `{"status": "ok"}` | - |
| GET | `/` | Root endpoint | No | - | Redirect to docs | - |

## UI Endpoints (HTML)

| Method | Path | Purpose | Auth Required | Sample Request | Sample Response | Error Codes |
|--------|------|---------|---------------|----------------|-----------------|-------------|
| GET | `/review` | Review page | Yes | `?tenant_id=tenant1&reason_filter=low_confidence` | HTML page | 401, 422 |
| GET | `/metrics` | Metrics dashboard | Yes | `?tenant_id=tenant1&period=30d` | HTML page | 401, 422 |
| GET | `/export` | Export center | Yes | - | HTML page | 401, 422 |
| GET | `/firm` | Firm console | Yes (Owner/Staff) | - | HTML page | 401, 403, 422 |
| GET | `/rules` | Rules console | Yes | `?active_tab=candidates` | HTML page | 401, 422 |
| GET | `/audit` | Audit log viewer | Yes | `?date_from=2025-10-01&tenant_id=tenant1` | HTML page | 401, 422 |
| GET | `/legal/terms` | Terms of service | No | - | HTML page | - |
| GET | `/legal/privacy` | Privacy policy | No | - | HTML page | - |
| GET | `/legal/dpa` | Data processing agreement | No | - | HTML page | - |
| GET | `/support` | Support page | No | - | HTML page | - |

## ACTIONS-Ready Endpoints (OpenAPI opIds)

The following endpoints have proper OpenAPI operation IDs suitable for ChatGPT Actions:

- `login_api_auth_login_post` - User authentication
- `signup_api_auth_signup_post` - User registration  
- `list_tenants_api_tenants_get` - List accessible tenants
- `get_tenant_api_tenants__tenant_id__get` - Get tenant details
- `list_candidates_api_rules_candidates_get` - List rule candidates
- `dryrun_rule_promotion_api_rules_dryrun_post` - Simulate rule impact
- `accept_candidate_api_rules_candidates__id__accept_post` - Promote rule
- `reject_candidate_api_rules_candidates__id__reject_post` - Decline rule
- `export_audit_csv_api_audit_export_csv_get` - Export audit data
- `upload_statement_api_upload_post` - Upload bank statement
- `propose_journal_entries_api_post_propose_post` - Generate journal entries
- `approve_journal_entries_api_post_approve_post` - Approve/post entries
- `export_quickbooks_api_export_quickbooks_post` - Export to QuickBooks
- `export_xero_api_export_xero_post` - Export to Xero

## Authentication Methods

1. **Cookie-based**: HttpOnly, Secure, SameSite=Lax cookies for UI
2. **Bearer Token**: Authorization header for API clients
3. **Magic Token**: Dev mode bypass with `magic_token="dev"`

## RBAC (Role-Based Access Control)

- **Owner**: Full access to all tenants, can modify settings, approve/reject rules
- **Staff**: Read-only access to assigned tenants only
- **Public**: Access to legal pages, support, health checks only

## Error Response Format

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Rate Limiting

- No explicit rate limiting configured
- Relies on Render's default limits for free tier
- Authentication endpoints may have implicit limits
