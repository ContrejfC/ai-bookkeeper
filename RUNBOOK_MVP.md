# MVP Runbook - Smoke Test & Operations Guide
## AI Bookkeeper

**Version:** 1.0  
**Last Updated:** October 27, 2025  
**Purpose:** Quick smoke testing and operational procedures for MVP deployment

---

## 🚀 Pre-Deployment Checklist

### Environment Variables

Verify all required environment variables are set:

```bash
# Backend (.env)
✓ DATABASE_URL
✓ SECRET_KEY
✓ STRIPE_SECRET_KEY
✓ STRIPE_WEBHOOK_SECRET
✓ STRIPE_BILLING_PORTAL_RETURN_URL
✓ QBO_ENV (sandbox or production)
✓ QBO_CLIENT_ID or QBO_CLIENT_ID_SANDBOX
✓ QBO_CLIENT_SECRET or QBO_CLIENT_SECRET_SANDBOX
✓ DEMO_MODE (true or false)
✓ REDIS_URL (optional)

# Frontend (.env.local)
✓ NEXT_PUBLIC_API_URL
✓ NEXT_PUBLIC_BASE_URL
```

### Database

```bash
# Run migrations
alembic upgrade head

# Verify tables exist
sqlite3 aibookkeeper.db ".tables"
# OR for PostgreSQL:
psql $DATABASE_URL -c "\dt"

# Expected tables:
# - users
# - tenants
# - transactions
# - journal_entries
# - billing_subscriptions
# - billing_events
# - usage_logs
# - qbo_tokens
# - je_idempotency
# - idempotency_logs
```

### Services Running

```bash
# Backend
curl http://localhost:8000/healthz
# Expected: {"status":"healthy"}

# Frontend
curl http://localhost:3000/
# Expected: HTML response (200 OK)

# Redis (if used)
redis-cli ping
# Expected: PONG
```

---

## 🧪 Smoke Tests

### Test 1: Health Endpoints

**Purpose:** Verify services are running

```bash
# Health check
curl http://localhost:8000/healthz

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-10-27T..."
}

# Readiness check
curl http://localhost:8000/readyz

# Expected response:
{
  "status": "ready",
  "database": "connected",
  "redis": "connected" # or "not_configured"
}
```

**✅ Pass Criteria:** Both endpoints return 200 OK

---

### Test 2: User Authentication

**Purpose:** Verify JWT auth works

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'

# Expected response:
{
  "access_token": "eyJ...",
  "user": {
    "email": "test@example.com",
    "user_id": "...",
    "role": "owner"
  }
}
```

**✅ Pass Criteria:** Returns valid JWT token

---

### Test 3: Billing Portal (Owner Only)

**Purpose:** Verify Stripe portal integration

```bash
# Get access token from Test 2
TOKEN="eyJ..."

# Request portal URL
curl -X POST http://localhost:8000/api/billing/portal \
  -H "Authorization: Bearer $TOKEN"

# Expected response:
{
  "url": "https://billing.stripe.com/session/..."
}
```

**✅ Pass Criteria:** Returns Stripe billing portal URL

---

### Test 4: Entitlements Check

**Purpose:** Verify quota enforcement

```bash
# Check entitlements
curl http://localhost:8000/api/billing/entitlements \
  -H "Authorization: Bearer $TOKEN"

# Expected response:
{
  "plan": "professional",
  "status": "active",
  "tx_quota_monthly": 2000,
  "tx_used_monthly": 150,
  "tx_remaining": 1850,
  "features": ["ai_categorization", "advanced_rules", "qbo_export"]
}
```

**✅ Pass Criteria:** Returns user's entitlements correctly

---

### Test 5: QBO Environment Detection

**Purpose:** Verify QBO sandbox/production detection

```bash
# Check QBO status
curl http://localhost:8000/api/qbo/status \
  -H "Authorization: Bearer $TOKEN"

# Expected response:
{
  "connected": false,
  "environment": "sandbox",
  "demo_mode": true
}
```

**✅ Pass Criteria:** Shows correct environment (sandbox/production)

---

### Test 6: Demo Data Creation

**Purpose:** Verify onboarding demo data

```bash
# Create demo data
curl -X POST http://localhost:8000/api/onboarding/seed-demo \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test-tenant",
    "count": 10
  }'

# Expected response:
{
  "inserted": 10,
  "tenant_id": "test-tenant",
  "date_range": {
    "start": "2025-07-28",
    "end": "2025-10-27"
  }
}
```

**✅ Pass Criteria:** Creates demo transactions successfully

---

### Test 7: PII Redaction in Logs

**Purpose:** Verify sensitive data is redacted

```bash
# Check recent logs
tail -n 100 logs/app.log | grep -E "EMAIL|TOKEN|PAN|SSN"

# Expected: Redacted versions like ***EMAIL***, ***TOKEN***
# NOT expected: Actual email addresses, tokens, etc.
```

**✅ Pass Criteria:** No plaintext sensitive data in logs

---

### Test 8: Request ID Tracking

**Purpose:** Verify request tracing

```bash
# Make request with custom request ID
curl http://localhost:8000/healthz \
  -H "X-Request-Id: test-trace-12345" \
  -v

# Check response headers:
# X-Request-Id: test-trace-12345
```

**✅ Pass Criteria:** Request ID is preserved in response

---

### Test 9: Frontend Paywall

**Purpose:** Verify entitlement gates work

**Manual Test Steps:**
1. Open browser to `http://localhost:3000`
2. Login as free-tier user
3. Navigate to `/transactions`
4. **Expected:** See upgrade CTA or blocked access
5. Login as paid user
6. Navigate to `/transactions`
7. **Expected:** Full access granted

**✅ Pass Criteria:** Free users blocked, paid users allowed

---

### Test 10: Webhook Idempotency

**Purpose:** Verify Stripe webhooks don't process duplicates

```bash
# Send webhook twice (requires STRIPE_WEBHOOK_SECRET)
# This is typically tested in CI/staging, not manually

# Check database:
sqlite3 aibookkeeper.db \
  "SELECT COUNT(*) FROM billing_events WHERE stripe_event_id='evt_test_123'"

# Expected: 1 (not 2)
```

**✅ Pass Criteria:** Duplicate events processed only once

---

## 📊 Post-Deployment Verification

### 1. Check Application Logs

```bash
# Backend logs
tail -f logs/app.log

# Look for:
# - No ERROR level messages
# - QBO environment logged correctly
# - PII redaction active
```

### 2. Database Health

```bash
# Check connection pool
# (For PostgreSQL)
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'aibookkeeper';"

# Should be within DB_POOL_SIZE + DB_MAX_OVERFLOW
```

### 3. Monitor Stripe Webhooks

```bash
# Check Stripe dashboard:
# https://dashboard.stripe.com/test/webhooks

# Verify:
# - Webhook endpoint configured
# - Recent events processed successfully
# - No failed deliveries
```

### 4. QBO OAuth Flow

**Manual Test:**
1. Login as owner
2. Go to `/export`
3. Click "Connect QuickBooks (Sandbox)"
4. Complete OAuth flow
5. Verify connection status shows "Connected"

**✅ Pass Criteria:** OAuth completes without errors

---

## 🚨 Common Issues & Solutions

### Issue 1: 500 Error on /api/billing/portal

**Symptoms:**
- 500 Internal Server Error
- Log shows "Stripe error"

**Solution:**
```bash
# Check Stripe keys
echo $STRIPE_SECRET_KEY
# Should start with sk_test_ or sk_live_

# Verify customer exists in Stripe dashboard
# Create subscription if missing
```

---

### Issue 2: Quota Not Enforcing

**Symptoms:**
- Free users can access paid features
- No 402 errors

**Solution:**
```bash
# Check entitlements middleware is loaded
grep "Entitlement check passed" logs/app.log

# Verify billing_subscriptions table has data
sqlite3 aibookkeeper.db "SELECT * FROM billing_subscriptions WHERE tenant_id='xxx';"

# Check usage_logs
sqlite3 aibookkeeper.db "SELECT * FROM usage_logs ORDER BY timestamp DESC LIMIT 10;"
```

---

### Issue 3: QBO Connection Fails

**Symptoms:**
- OAuth redirect fails
- Error: "QBO_NOT_CONNECTED"

**Solution:**
```bash
# Verify QBO_ENV
echo $QBO_ENV
# Should be "sandbox" or "production"

# Check credentials
echo $QBO_CLIENT_ID_SANDBOX
# Should not be empty if QBO_ENV=sandbox

# Verify redirect URI matches
# Intuit Developer Console → App Settings → Redirect URIs
# Should include: http://localhost:8000/api/qbo/callback
```

---

### Issue 4: PII Not Redacted

**Symptoms:**
- Email addresses visible in logs
- Tokens in plaintext

**Solution:**
```bash
# Verify redaction filter configured
grep "RedactionFilter" app/api/main.py

# Check log configuration
cat logging.conf

# Manually test
python -c "from app.logging.redaction import redact_text; print(redact_text('Email: test@example.com'))"
# Expected: Email: ***EMAIL***
```

---

### Issue 5: Webhook Not Processing

**Symptoms:**
- Subscription created in Stripe but not in DB
- billing_events table empty

**Solution:**
```bash
# Check webhook secret
echo $STRIPE_WEBHOOK_SECRET
# Should start with whsec_

# Test webhook locally
stripe listen --forward-to localhost:8000/api/billing/stripe_webhook

# Check logs
tail -f logs/app.log | grep webhook

# Verify endpoint in Stripe dashboard
# https://dashboard.stripe.com/test/webhooks
```

---

## 🔧 Operational Commands

### View Recent Logs

```bash
# Last 100 lines
tail -n 100 logs/app.log

# Follow in real-time
tail -f logs/app.log

# Filter for errors
grep ERROR logs/app.log | tail -n 20

# Filter by request ID
grep "test-trace-12345" logs/app.log
```

### Check Database Stats

```bash
# SQLite
sqlite3 aibookkeeper.db "
  SELECT 'Users' as table_name, COUNT(*) as count FROM users
  UNION ALL
  SELECT 'Tenants', COUNT(*) FROM tenants
  UNION ALL
  SELECT 'Transactions', COUNT(*) FROM transactions
  UNION ALL
  SELECT 'Journal Entries', COUNT(*) FROM journal_entries
  UNION ALL
  SELECT 'Subscriptions', COUNT(*) FROM billing_subscriptions;
"

# PostgreSQL
psql $DATABASE_URL -c "
  SELECT 'Users' as table_name, COUNT(*) as count FROM users
  UNION ALL
  SELECT 'Tenants', COUNT(*) FROM tenants
  UNION ALL
  SELECT 'Transactions', COUNT(*) FROM transactions
  UNION ALL
  SELECT 'Journal Entries', COUNT(*) FROM journal_entries
  UNION ALL
  SELECT 'Subscriptions', COUNT(*) FROM billing_subscriptions;
"
```

### Clear Test Data

```bash
# ⚠️  DESTRUCTIVE - Use with caution

# Delete demo transactions
sqlite3 aibookkeeper.db "DELETE FROM transactions WHERE raw LIKE '%\"demo\":true%';"

# Delete test users
sqlite3 aibookkeeper.db "DELETE FROM users WHERE email LIKE '%@test.com';"

# Reset usage logs for tenant
sqlite3 aibookkeeper.db "DELETE FROM usage_logs WHERE tenant_id='test-tenant';"
```

### Restart Services

```bash
# Backend (development)
pkill -f "uvicorn app.api.main:app"
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (development)
cd frontend
npm run dev

# Production (systemd)
sudo systemctl restart ai-bookkeeper-api
sudo systemctl restart ai-bookkeeper-web
```

---

## 📈 Monitoring Checklist

### Daily Checks

- [ ] `/healthz` endpoint returns 200
- [ ] No ERROR logs in last 24 hours
- [ ] Stripe webhooks processing (check dashboard)
- [ ] Database size within limits

### Weekly Checks

- [ ] Review Stripe billing activity
- [ ] Check quota usage by tenant
- [ ] Review PII redaction logs
- [ ] Test QBO OAuth flow end-to-end

### Monthly Checks

- [ ] Rotate database backups
- [ ] Review and archive old audit logs
- [ ] Update dependencies (security patches)
- [ ] Test disaster recovery procedure

---

## 🆘 Emergency Contacts

### Critical Issues

| Issue | Action | Contact |
|-------|--------|---------|
| Service Down | Check logs, restart services | DevOps Team |
| Data Breach | Rotate secrets, notify users | Security Team |
| Stripe Webhook Failure | Check Stripe dashboard | Billing Team |
| QBO OAuth Broken | Verify credentials | Integration Team |

### Escalation Path

1. **Level 1:** Check runbook, restart services
2. **Level 2:** Review logs, check database
3. **Level 3:** Contact on-call engineer
4. **Level 4:** Escalate to CTO

---

## 📚 Additional Resources

- **Full Documentation:** `MVP_FINAL_COMPLETE.md`
- **API Documentation:** `API_ROUTE_FIX_NEEDED.md`
- **Deployment Guide:** `AD_READY_DEPLOYMENT_GUIDE.md`
- **Alerting Setup:** `ops/ALERTING.md`
- **Environment Variables:** `env.example`

---

## ✅ Acceptance Criteria Summary

| Criteria | Status | Notes |
|----------|--------|-------|
| Unpaid users blocked | ✅ | Entitlement gates active |
| Paid users complete flow ≤10 min | ✅ | Onboarding optimized |
| QBO Sandbox connects | ✅ | OAuth flow working |
| Demo export works | ✅ | Mock JE posted |
| Webhooks idempotent | ✅ | Duplicate detection active |
| PII redacted | ✅ | Logs and exports clean |
| Health endpoints pass | ✅ | /healthz and /readyz OK |
| DB pool configured | ✅ | Pool size set in env |

---

**Document Version:** 1.0  
**Maintained By:** AI Bookkeeper DevOps Team  
**Next Review:** November 27, 2025

