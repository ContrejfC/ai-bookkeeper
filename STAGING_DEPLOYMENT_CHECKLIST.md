# Staging Deployment Validation Checklist

**AI Bookkeeper - Pre-Production Gate**

Use this checklist to validate that staging environment is ready for production cutover.

---

## 🎯 Gate Criteria for "Sellable MVP"

All items marked **[REQUIRED]** must pass before declaring staging sellable.  
Items marked **[RECOMMENDED]** should pass for production-grade quality.  
Items marked **[OPTIONAL]** are nice-to-have improvements.

---

## A) Pre-Deployment Setup

### Environment Variables

- [ ] **[REQUIRED]** All secrets configured in `.env.staging`:
  - [ ] `DATABASE_URL` (PostgreSQL, not SQLite)
  - [ ] `JWT_SECRET` (min 32 chars)
  - [ ] `OPENAI_API_KEY`
  - [ ] `STRIPE_SECRET_KEY` (test mode)
  - [ ] `STRIPE_WEBHOOK_SECRET`
  - [ ] All 18 Stripe price IDs (starter/team/firm monthly/annual + overages + addons)
  - [ ] `QBO_CLIENT_ID` + `QBO_CLIENT_SECRET` (sandbox)
  - [ ] `XERO_CLIENT_ID` + `XERO_CLIENT_SECRET` (optional)
  - [ ] `CORS_ALLOWED_ORIGINS` (includes staging frontend URL)
  - [ ] `BACKEND_URL` + `FRONTEND_URL` (staging URLs)
  - [ ] `COOKIE_SECURE=true`
  - [ ] `COOKIE_SAMESITE=lax`

- [ ] **[REQUIRED]** `.env.staging` never committed to git

### Database Migration

- [ ] **[REQUIRED]** Fresh database created (PostgreSQL)
- [ ] **[REQUIRED]** `alembic upgrade head` runs cleanly (no errors)
- [ ] **[REQUIRED]** All 30 tables exist (check with `\dt` in psql)
- [ ] **[REQUIRED]** Unique index on `je_idempotency(tenant_id, payload_hash)` exists
- [ ] **[RECOMMENDED]** Seed entitlements: `python scripts/seed_entitlements.py`

### Stripe Configuration

- [ ] **[REQUIRED]** Stripe test mode enabled
- [ ] **[REQUIRED]** 3 products created (Starter, Team, Firm)
- [ ] **[REQUIRED]** 7 subscription prices created (monthly + annual per product + pilot)
- [ ] **[REQUIRED]** 4 metered overage prices created
- [ ] **[REQUIRED]** 6 add-on prices created
- [ ] **[REQUIRED]** Webhook endpoint configured: `https://staging-api.example.com/api/billing/stripe_webhook`
- [ ] **[REQUIRED]** Webhook secret stored in env
- [ ] **[RECOMMENDED]** Test webhook delivery with Stripe CLI: `stripe listen --forward-to https://staging-api.example.com/api/billing/stripe_webhook`

### QuickBooks Sandbox

- [ ] **[REQUIRED]** Intuit developer account created
- [ ] **[REQUIRED]** Sandbox app configured with OAuth 2.0
- [ ] **[REQUIRED]** Redirect URI set to staging API: `https://staging-api.example.com/api/qbo/oauth/callback`
- [ ] **[REQUIRED]** Sandbox company created in QuickBooks
- [ ] **[RECOMMENDED]** Chart of accounts seeded in QBO sandbox

---

## B) Deployment Validation

### Health Checks

```bash
curl -sS https://staging-api.example.com/healthz | jq
```

- [ ] **[REQUIRED]** `/healthz` returns 200
- [ ] **[REQUIRED]** Response includes:
  - [ ] `status: "ok"`
  - [ ] `database_status: "healthy"`
  - [ ] `db_ping_ms` < 50ms
  - [ ] `version` matches deployed version
- [ ] **[REQUIRED]** `/readyz` returns 200
- [ ] **[REQUIRED]** `/openapi.json` returns valid JSON (1400+ lines)

### HTTPS & CORS

```bash
curl -I https://staging-api.example.com/healthz
```

- [ ] **[REQUIRED]** HTTPS enabled (not HTTP)
- [ ] **[REQUIRED]** SSL certificate valid (not self-signed)
- [ ] **[REQUIRED]** CORS headers present for allowed origins
- [ ] **[REQUIRED]** CORS preflight (OPTIONS) works for `/api/auth/login`

### Migration Status

```bash
# SSH into staging server or use remote psql
alembic current
alembic heads
```

- [ ] **[REQUIRED]** Current revision matches head
- [ ] **[REQUIRED]** No warnings about missing revisions
- [ ] **[REQUIRED]** `alembic history` shows clean chain: `001_initial_schema -> 002_multi_tenant`

---

## C) Auth Flow

### Signup & Login

```bash
# Signup
curl -X POST https://staging-api.example.com/api/auth/signup/test \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","full_name":"Test User"}'

# Login
curl -X POST https://staging-api.example.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

- [ ] **[REQUIRED]** Signup returns `user_id` or `access_token`
- [ ] **[REQUIRED]** Login returns valid JWT `access_token`
- [ ] **[REQUIRED]** `/api/auth/me` with JWT returns user info
- [ ] **[REQUIRED]** Invalid JWT returns 401

### CSRF Protection

- [ ] **[REQUIRED]** Health endpoints (`/healthz`, `/docs`) work without CSRF token
- [ ] **[REQUIRED]** Auth endpoints (`/api/auth/signup`) exempt from CSRF
- [ ] **[REQUIRED]** Protected endpoints (`/api/post/propose`) require CSRF token for POST
- [ ] **[RECOMMENDED]** CSRF token endpoint exists: `/api/csrf-token`

---

## D) Ingestion Pipeline

### CSV Upload

```bash
curl -X POST https://staging-api.example.com/api/upload \
  -H "Authorization: Bearer $JWT" \
  -F "file=@sample.csv"
```

- [ ] **[REQUIRED]** CSV upload returns `upload_id` or `job_id`
- [ ] **[REQUIRED]** Transactions normalized to database
- [ ] **[REQUIRED]** Date parsing works for common formats (YYYY-MM-DD, MM/DD/YYYY)
- [ ] **[REQUIRED]** Currency amounts handled correctly (negative signs, commas)
- [ ] **[RECOMMENDED]** PII redaction in logs (no raw descriptions logged)

### PDF Upload

```bash
curl -X POST https://staging-api.example.com/api/upload \
  -H "Authorization: Bearer $JWT" \
  -F "file=@sample.pdf"
```

- [ ] **[REQUIRED]** PDF upload accepted
- [ ] **[REQUIRED]** OCR extracts text (even if basic Tesseract)
- [ ] **[OPTIONAL]** Bbox coordinates stored for manual review

---

## E) Decisioning Pipeline

### Propose (AI Categorization)

```bash
curl -X POST "https://staging-api.example.com/api/post/propose?threshold=0.90" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json"
```

- [ ] **[REQUIRED]** Returns proposed journal entries
- [ ] **[REQUIRED]** Each entry has:
  - [ ] `proposed_account` (GL account)
  - [ ] `confidence` (0.0-1.0)
  - [ ] `rationale` object with:
    - [ ] `rule` (executed: true/false, confidence, details)
    - [ ] `embedding` (executed: true/false, confidence, details)
    - [ ] `llm` (executed: true/false, confidence, details)
  - [ ] `execution_order` (e.g., ["rule", "embedding", "llm"])
- [ ] **[REQUIRED]** Audit log entry created in `decision_audit_log` table
- [ ] **[RECOMMENDED]** High-confidence transactions (≥0.90) skip LLM call
- [ ] **[RECOMMENDED]** Response time < 2s per transaction (p95)

### Approve & Commit

```bash
curl -X POST https://staging-api.example.com/api/post/approve \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"entry_ids": ["je_123"]}'

curl -X POST https://staging-api.example.com/api/post/commit \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"entry_ids": ["je_123"]}'
```

- [ ] **[REQUIRED]** Approve marks entries as ready
- [ ] **[REQUIRED]** Commit finalizes entries
- [ ] **[RECOMMENDED]** Cannot commit without approval

---

## F) Exports (QBO)

### Dry-Run Export

```bash
curl -X POST "https://staging-api.example.com/api/export/quickbooks?dry_run=true" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"entries": [{"account":"1000","debit":100,"credit":0}, {"account":"4000","debit":0,"credit":100}]}'
```

- [ ] **[REQUIRED]** Dry-run returns balanced preview
- [ ] **[REQUIRED]** Validation checks:
  - [ ] Total debits == Total credits
  - [ ] All accounts present
  - [ ] No negative amounts on wrong side
- [ ] **[REQUIRED]** Returns deterministic `je_hash`

### Live Export to QBO Sandbox

```bash
curl -X POST https://staging-api.example.com/api/export/quickbooks \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"entries": [...]}'
```

- [ ] **[REQUIRED]** First export succeeds and returns `vendor_doc_id` (QBO JournalEntry ID)
- [ ] **[REQUIRED]** Second export with **same payload** returns cached `vendor_doc_id`
- [ ] **[REQUIRED]** `je_idempotency` table has **one row** (not two)
- [ ] **[REQUIRED]** `payload_hash` matches between calls
- [ ] **[REQUIRED]** Verify in QBO sandbox that JournalEntry exists
- [ ] **[RECOMMENDED]** Export respects tenant isolation (cannot export to another tenant's QBO)

### Error Handling

- [ ] **[REQUIRED]** Unbalanced entry returns `422_UNBALANCED_ENTRY` with delta
- [ ] **[REQUIRED]** QBO auth failure returns `401_QBO_NOT_CONNECTED`
- [ ] **[REQUIRED]** Missing account returns `422_INVALID_ACCOUNT`

---

## G) Billing & Entitlements

### Billing Status

```bash
curl https://staging-api.example.com/api/billing/status \
  -H "Authorization: Bearer $JWT"
```

- [ ] **[REQUIRED]** Returns:
  - [ ] `plan` (starter/team/firm)
  - [ ] `subscription_status` (active/trialing/past_due)
  - [ ] `trial_ends_at` (if in trial)
  - [ ] `limits` (entity_limit, monthly_tx_cap)
  - [ ] `usage` (entities_used, transactions_used)

### Checkout Flow

```bash
curl -X POST https://staging-api.example.com/api/billing/create_checkout_session \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"plan":"starter","billing_cycle":"monthly"}'
```

- [ ] **[REQUIRED]** Returns Stripe checkout URL
- [ ] **[REQUIRED]** URL redirects to Stripe test checkout page
- [ ] **[REQUIRED]** After test payment, webhook fires and updates entitlement
- [ ] **[REQUIRED]** Entitlement row updated in database with `subscription_status: "active"`

### Entitlement Enforcement

- [ ] **[REQUIRED]** Soft gate at 80% of limit (warning message)
- [ ] **[REQUIRED]** Hard gate at 100% of limit (blocks request with `429_QUOTA_EXCEEDED`)
- [ ] **[REQUIRED]** Usage metering increments on propose (not on retries)
- [ ] **[RECOMMENDED]** Overage billing configured in Stripe

### Stripe Webhooks

- [ ] **[REQUIRED]** Webhook endpoint reachable from internet (not localhost)
- [ ] **[REQUIRED]** Webhook signature validation passes
- [ ] **[REQUIRED]** Handles events:
  - [ ] `customer.subscription.created`
  - [ ] `customer.subscription.updated`
  - [ ] `customer.subscription.deleted`
  - [ ] `invoice.paid`
  - [ ] `customer.subscription.trial_will_end`

---

## H) Observability & Logs

### Structured Logging

- [ ] **[REQUIRED]** Logs include:
  - [ ] `request_id` (UUID per request)
  - [ ] `tenant_id` (for tenant isolation)
  - [ ] `principal_id` (user_id)
  - [ ] `error_code` (from error taxonomy)
  - [ ] `timestamp` (ISO 8601)
- [ ] **[REQUIRED]** PII redacted in logs (emails, account numbers, tokens)
- [ ] **[RECOMMENDED]** Logs sent to external aggregator (Datadog, CloudWatch)

### Error Taxonomy

- [ ] **[REQUIRED]** 5xx errors use standardized codes:
  - [ ] `500_INTERNAL_ERROR`
  - [ ] `503_LLM_UNAVAILABLE`
  - [ ] `503_QBO_UNAVAILABLE`
  - [ ] `504_TIMEOUT`
- [ ] **[REQUIRED]** 4xx errors use standardized codes:
  - [ ] `400_INVALID_FORMAT`
  - [ ] `401_UNAUTHORIZED`
  - [ ] `403_FORBIDDEN`
  - [ ] `422_UNBALANCED_ENTRY`
  - [ ] `422_FILE_ENCRYPTED`
  - [ ] `429_RATE_LIMITED`
  - [ ] `429_QUOTA_EXCEEDED`

### Background Jobs

- [ ] **[REQUIRED]** Worker process running (if using background jobs)
- [ ] **[REQUIRED]** Jobs enqueued and processed
- [ ] **[OPTIONAL]** Redis configured (or in-memory queue for staging)

---

## I) Security Checks

### Authentication & Authorization

- [ ] **[REQUIRED]** JWT tokens expire (check `exp` claim)
- [ ] **[REQUIRED]** Expired tokens return 401
- [ ] **[REQUIRED]** Tenant isolation enforced (cannot read another tenant's data)
- [ ] **[REQUIRED]** Role-based access control (owner vs staff)

### Data Protection

- [ ] **[REQUIRED]** Database credentials in env vars (not hardcoded)
- [ ] **[REQUIRED]** Stripe keys in env vars (not committed)
- [ ] **[REQUIRED]** S3/GCS keys in env vars (if used)
- [ ] **[REQUIRED]** HTTPS enforced (HTTP redirects to HTTPS)
- [ ] **[RECOMMENDED]** Database SSL enabled
- [ ] **[RECOMMENDED]** Uploaded files auto-deleted after 24h

### Rate Limiting

- [ ] **[REQUIRED]** Rate limits configured (per IP, per tenant)
- [ ] **[REQUIRED]** Excessive requests return `429_RATE_LIMITED`
- [ ] **[OPTIONAL]** CAPTCHA on signup/login after N failed attempts

---

## J) E2E Smoke Test

Run the automated smoke test script:

```bash
./scripts/e2e_smoke.sh https://staging-api.example.com
```

- [ ] **[REQUIRED]** All core tests PASS:
  - [ ] Health checks
  - [ ] Auth flow (signup → login → /me)
  - [ ] File upload (CSV)
  - [ ] Decisioning (propose with rationale)
  - [ ] Billing status
  - [ ] OpenAPI spec
- [ ] **[RECOMMENDED]** All advanced tests PASS:
  - [ ] PDF upload with OCR
  - [ ] QBO export with idempotency
  - [ ] Checkout link generation
  - [ ] Webhook handling

---

## K) Performance & Load Testing

### Response Time Targets

- [ ] **[REQUIRED]** `/healthz` < 100ms (p95)
- [ ] **[REQUIRED]** `/api/auth/login` < 500ms (p95)
- [ ] **[REQUIRED]** `/api/upload` (CSV) < 5s for 1000 rows (p95)
- [ ] **[RECOMMENDED]** `/api/post/propose` < 2s per transaction (p95)
- [ ] **[RECOMMENDED]** `/api/export/quickbooks` < 3s (p95)

### Load Testing

```bash
# Example with Apache Bench
ab -n 100 -c 10 https://staging-api.example.com/healthz

# Or with k6 (see tests/load/k6_propose.js)
k6 run tests/load/k6_propose.js
```

- [ ] **[RECOMMENDED]** 100 concurrent users: 99% success rate
- [ ] **[RECOMMENDED]** 1000 requests/minute: avg latency < 1s
- [ ] **[OPTIONAL]** Autoscaling configured (Kubernetes HPA, Cloud Run auto-scale)

---

## L) Documentation & Runbooks

- [ ] **[REQUIRED]** `.env.example` up to date with all required vars
- [ ] **[REQUIRED]** `README.md` has deployment instructions
- [ ] **[RECOMMENDED]** Runbook for common errors (QBO auth expired, LLM rate limit)
- [ ] **[RECOMMENDED]** Rollback procedure documented
- [ ] **[OPTIONAL]** Observability dashboard (Grafana, Datadog)

---

## M) Final Go/No-Go Decision

### Go Criteria (All Required)

- ✅ Migrations run cleanly
- ✅ Health checks pass
- ✅ Auth flow works
- ✅ Decisioning returns confidence + rationale
- ✅ QBO export succeeds with idempotency
- ✅ Billing status endpoint works
- ✅ E2E smoke test passes
- ✅ Logs include request_id, tenant_id, error_code
- ✅ HTTPS enabled with valid certificate
- ✅ Secrets in env vars (not hardcoded)

### No-Go Conditions (Any of These)

- ❌ Health check fails
- ❌ Migrations have errors
- ❌ JE idempotency allows duplicates
- ❌ Tenant isolation broken (data leak)
- ❌ Unbalanced exports reach QBO
- ❌ PII logged in plaintext
- ❌ Secrets hardcoded or committed

---

## N) Post-Deployment Monitoring

### First 24 Hours

- [ ] **[REQUIRED]** Monitor error rate (should be < 1%)
- [ ] **[REQUIRED]** Monitor p95 latency (should match targets)
- [ ] **[REQUIRED]** Check for any 500 errors in logs
- [ ] **[REQUIRED]** Verify webhooks firing from Stripe
- [ ] **[RECOMMENDED]** Set up alerts for critical failures

### First Week

- [ ] **[REQUIRED]** Review user feedback (if beta users onboarded)
- [ ] **[REQUIRED]** Check for any data integrity issues
- [ ] **[REQUIRED]** Verify billing calculations correct
- [ ] **[RECOMMENDED]** Run weekly audit report

---

## Checklist Sign-Off

**Completed by:** _______________________  
**Date:** _______________________  
**Staging URL:** _______________________  
**Ready for Production:** ☐ YES  ☐ NO (see notes)

**Notes / Blockers:**

---

**End of Checklist**

_Save this file as `STAGING_DEPLOYMENT_CHECKLIST.md` in repo root._

