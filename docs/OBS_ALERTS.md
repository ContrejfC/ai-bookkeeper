# Monitoring & Alerts - Operational Guide

**Purpose:** Define what to monitor, thresholds, and runbooks for production operations.

---

## Alert Scenarios & Thresholds

### 1. Stripe Webhook Failures

**What to watch:**
- Webhook delivery success rate
- Consecutive 5xx responses from webhook endpoint

**Threshold:**
- Alert if: >3 consecutive failures OR <95% success rate over 1 hour

**How to check:**

**Via Stripe Dashboard:**
1. Go to Stripe Dashboard → Developers → Webhooks
2. Click your webhook endpoint
3. View "Recent deliveries" log
4. Check for red (failed) entries

**Via cURL (manual check):**
```bash
# Check webhook endpoint is reachable
curl -I https://YOUR_DOMAIN/api/billing/webhook

# Expected: 405 Method Not Allowed (POST only)
# Failure: 404, 502, 503, timeout
```

**Alert Query (Stripe API):**
```bash
# List recent webhook deliveries (requires Stripe API key)
curl https://api.stripe.com/v1/webhook_endpoints/we_xxx/attempts \
  -u "$STRIPE_SECRET_KEY:"

# Parse for failed attempts
```

**Runbook (Webhook Failures):**
1. Check Stripe Dashboard → Webhooks → Logs for error details
2. If 500: Check application logs for exceptions in webhook handler
3. If 502/503: Check if app is running (`GET /healthz`)
4. If signature error: Verify `STRIPE_WEBHOOK_SECRET` matches Dashboard
5. Manual retry: Stripe Dashboard → Event → Send test webhook
6. If persistent: Disable webhook, fix issue, re-enable

---

### 2. QBO API 5xx Errors

**What to watch:**
- QBO API response codes (5xx)
- Token refresh failures

**Threshold:**
- Alert if: >10% of QBO requests return 5xx over 5 minutes

**How to check:**

**Via Application Logs:**
```bash
# Search for QBO errors
grep "QBO.*5xx" logs/app.log | tail -20

# Or count errors
grep "QBO.*error" logs/app.log | wc -l
```

**Via /metrics (if implemented):**
```bash
curl http://localhost:8000/metrics | grep qbo_5xx_total

# Sample output:
# qbo_5xx_total 5
```

**Runbook (QBO 5xx):**
1. Check QBO API status: https://status.developer.intuit.com
2. If degraded: Wait 5-10 minutes, errors should clear
3. If not degraded: Check token expiry (`GET /api/qbo/status`)
4. If token expired: Trigger refresh (attempt next post)
5. If persistent: Re-authorize QBO (`GET /api/auth/qbo/start`)
6. Log incident: Track duration and affected tenants

---

### 3. Health Check Failures

**What to watch:**
- `/healthz` and `/readyz` endpoint responses
- Database connectivity

**Threshold:**
- Alert if: `/healthz` returns non-200 for >1 minute

**How to check:**

**Via cURL:**
```bash
# Health check
curl -s http://YOUR_DOMAIN/healthz

# Expected: {"status": "healthy", "db": "ok", ...}
# Failure: timeout, 500, connection refused
```

**Via Render (or hosting platform):**
- Render Dashboard → Service → Health Checks
- Should show green checkmark

**Runbook (Health Failures):**
1. Check if app is running: `ps aux | grep uvicorn` (or Render logs)
2. Check database connectivity: `psql $DATABASE_URL -c "SELECT 1;"`
3. Check disk space: `df -h`
4. Check memory: `free -m`
5. If OOM: Scale up service (Render: increase RAM)
6. If DB timeout: Check connection pool settings
7. Restart service if unresponsive

---

### 4. Post Commit Error Rate

**What to watch:**
- `/api/post/commit` error responses
- Item-level errors (UNBALANCED_JE, QBO_VALIDATION)

**Threshold:**
- Alert if: >5% of commit requests fail over 10 minutes

**How to check:**

**Via Application Logs:**
```bash
# Count successful posts
grep "Posted JE to QBO" logs/app.log | wc -l

# Count failed posts
grep "QBO.*error\|UNBALANCED_JE" logs/app.log | wc -l

# Calculate error rate
```

**Via /metrics (if implemented):**
```bash
curl http://localhost:8000/metrics | grep -E "posts_ok_total|posts_error_total"

# Sample:
# posts_ok_total 150
# posts_error_total 5
# Error rate: 5 / (150 + 5) = 3.2%
```

**Runbook (High Error Rate):**
1. Identify error type from logs (UNBALANCED vs QBO_VALIDATION)
2. If UNBALANCED: Check proposal logic (amounts, rounding)
3. If QBO_VALIDATION: Check account refs (may need CoA refresh)
4. If QBO_UNAUTHORIZED: Check token status (`/api/qbo/status`)
5. If widespread: Pause auto-posting, investigate
6. Review affected transactions: Query `je_idempotency` table

---

### 5. Trial Ending Soon

**What to watch:**
- `customer.subscription.trial_will_end` Stripe webhook
- Trial countdown in `/billing/status`

**Threshold:**
- Alert: 7 days before trial end

**How to check:**

**Via Stripe Dashboard:**
- Customers tab → Filter by "Trialing"
- View trial end dates

**Via API:**
```bash
curl -H "Authorization: Bearer API_KEY" \
     https://YOUR_DOMAIN/api/billing/status | jq '.trial_days_left'

# Output: 7 (alert customer)
```

**Runbook (Trial Ending):**
1. Send notification to customer (email/Slack)
2. Offer upgrade link: `POST /api/billing/portal` → return URL
3. Track conversion: Did they upgrade?
4. If not upgraded: Expect subscription to cancel at trial end
5. Webhook `customer.subscription.deleted` will set `active: false`

---

### 6. Paywall Hit Rate (402/429)

**What to watch:**
- Frequency of 402 ENTITLEMENT_REQUIRED responses
- Frequency of 429 FREE_CAP_EXCEEDED responses

**Threshold:**
- Informational (not critical, but indicates upgrade opportunity)

**How to check:**

**Via Application Logs:**
```bash
# Count 402 responses
grep "402.*ENTITLEMENT_REQUIRED" logs/app.log | wc -l

# Count 429 responses
grep "429.*FREE_CAP_EXCEEDED" logs/app.log | wc -l
```

**Runbook (High Paywall Hits):**
1. Identify tenants hitting walls (group by tenant_id)
2. Send upgrade offer email
3. Track conversion rate
4. Consider: Adjust free tier cap (50→100?) or trial length (14→30 days)

---

## Metrics Endpoint (if implemented)

### Current Status

**If `/metrics` exists:**
```bash
curl http://YOUR_DOMAIN/metrics
```

**Expected counters:**
- `posts_ok_total` - Successful QBO posts
- `posts_idempotent_total` - Idempotent post hits
- `qbo_4xx_total` - QBO client errors
- `qbo_5xx_total` - QBO server errors
- `stripe_webhook_fail_total` - Webhook delivery failures

**Expected gauges:**
- `tenants_active` - Active subscriptions count
- `trial_days_left` - Per-tenant (via /billing/status)

### If Not Implemented

Use log-based monitoring:

```bash
# Count events manually
grep "Posted JE" logs/app.log | wc -l  # posts_ok
grep "idempotent.*true" logs/app.log | wc -l  # idempotent hits
grep "QBO.*5xx" logs/app.log | wc -l  # qbo errors
```

---

## Alert Integration Examples

### Sentry (Application Errors)

**Setup:**
```python
# Already configured via SENTRY_DSN env var
import sentry_sdk
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))
```

**What Sentry captures:**
- Unhandled exceptions
- QBO API errors (if not caught)
- Database connection errors
- Webhook processing failures

**Alert on:**
- Error rate >1% over 5 minutes
- New error types (fingerprinting)
- Performance degradation (slow endpoints)

### PagerDuty (Critical Alerts)

**Setup:**
```bash
# Add PAGERDUTY_INTEGRATION_KEY to env vars
# Or use webhook endpoint
```

**Alert routing:**
- Health check failures → Page on-call
- QBO 5xx spike → Page on-call
- Stripe webhook failures → Page on-call (billing critical)
- High error rate → Warn (email, no page)

### Slack (Informational)

**Setup:**
```bash
# Add SLACK_WEBHOOK_URL to env vars
# Use existing notification system
```

**Alert routing:**
- Trial ending soon → #sales channel
- New subscription → #revenue channel
- Paywall hits → #growth channel
- Errors → #engineering channel

---

## Cron Monitoring (Simple, No External Tools)

### Health Ping (Every 5 Minutes)

```bash
# crontab entry
*/5 * * * * curl -sf https://YOUR_DOMAIN/healthz || echo "Health check failed" | mail -s "API Down" ops@yourcompany.com
```

### Webhook Verification (Daily)

```bash
# crontab entry
0 9 * * * cd /app && python scripts/verify_stripe_webhook.py || echo "Webhook issue" | mail -s "Stripe Webhook" ops@yourcompany.com
```

### QBO Environment Check (Daily)

```bash
# crontab entry
0 10 * * * cd /app && python scripts/check_qbo_env.py || echo "QBO env issue" | mail -s "QBO Config" ops@yourcompany.com
```

---

## Log-Based Checks (No /metrics)

### Error Rate Calculation

```bash
#!/bin/bash
# scripts/check_error_rate.sh

# Count total requests
TOTAL=$(grep "POST /api/post/commit" logs/app.log | wc -l)

# Count errors
ERRORS=$(grep "POST /api/post/commit.*HTTP/1.1\" [45]" logs/app.log | wc -l)

# Calculate rate
if [ $TOTAL -gt 0 ]; then
    ERROR_RATE=$(echo "scale=2; $ERRORS * 100 / $TOTAL" | bc)
    echo "Error rate: $ERROR_RATE%"
    
    # Alert if > 5%
    if (( $(echo "$ERROR_RATE > 5.0" | bc -l) )); then
        echo "⚠️  High error rate detected!"
        exit 1
    fi
fi
```

### Webhook Success Rate

```bash
#!/bin/bash
# scripts/check_webhook_rate.sh

# Count webhook events
TOTAL=$(grep "Stripe webhook received" logs/app.log | wc -l)

# Count failures
FAILURES=$(grep "Stripe webhook.*failed" logs/app.log | wc -l)

# Calculate rate
if [ $TOTAL -gt 0 ]; then
    SUCCESS_RATE=$(echo "scale=2; ($TOTAL - $FAILURES) * 100 / $TOTAL" | bc)
    echo "Webhook success rate: $SUCCESS_RATE%"
    
    # Alert if < 95%
    if (( $(echo "$SUCCESS_RATE < 95.0" | bc -l) )); then
        echo "⚠️  Low webhook success rate!"
        exit 1
    fi
fi
```

---

## Security Alerts

### API Key Leak Detection

**What to watch:**
- Suspicious API key usage (many tenants, high volume)
- API key from unexpected IPs (if logging client IP)

**How to detect:**
```sql
-- Query api_keys table for recent usage
SELECT api_key.id, COUNT(*) as request_count
FROM api_keys
JOIN request_logs ON api_key.id = request_logs.api_key_id
WHERE request_logs.created_at > NOW() - INTERVAL '1 hour'
GROUP BY api_key.id
HAVING COUNT(*) > 1000;
```

**Runbook (Suspected Leak):**
1. Identify which API key (from logs)
2. Revoke immediately: `python scripts/revoke_api_key.py --token TOKEN`
3. Generate new key for affected tenant
4. Notify tenant of key rotation
5. Review logs for suspicious activity
6. Consider: Add rate limiting per API key

---

## Secrets Management Alerts

### Never Log These

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `QBO_CLIENT_SECRET`
- `DATABASE_URL` (contains password)
- API keys (full tokens)

**Safe to Log:**
- Last 4 chars of IDs (`cus_xxxx...1234`)
- Token hashes (SHA-256)
- Masked keys (`sk_live_xxxx...`)

**Alert on:**
- `grep -i "sk_live_" logs/app.log` (full key in logs)
- `grep -i "whsec_" logs/app.log` (webhook secret in logs)

**Runbook (Secret Exposed in Logs):**
1. Rotate key immediately (Stripe/QBO Dashboard)
2. Update env vars in Render
3. Redeploy application
4. Audit: Who had access to logs?
5. Review: Fix logging to mask secrets

---

## Dashboard Queries (Future Enhancement)

If you implement a metrics dashboard (Grafana, Datadog, NewRelic):

### Stripe Webhook Success Rate
```promql
# Prometheus query
(sum(rate(stripe_webhook_success_total[5m])) / sum(rate(stripe_webhook_total[5m]))) * 100

# Alert if < 95%
```

### QBO Error Rate
```promql
# Prometheus query
(sum(rate(qbo_5xx_total[5m])) / sum(rate(qbo_requests_total[5m]))) * 100

# Alert if > 10%
```

### Post Commit Success Rate
```promql
# Prometheus query
(sum(rate(posts_ok_total[10m])) / sum(rate(posts_total[10m]))) * 100

# Alert if < 95%
```

---

## Recommended Alert Channels

### Critical (Page Immediately)
- Health check down >1 minute → PagerDuty
- Database connection lost → PagerDuty
- Stripe webhook 100% failure rate → PagerDuty

### Warning (Email/Slack)
- QBO 5xx spike >10% → Slack #engineering
- Post commit error rate >5% → Slack #engineering
- Trial ending in 3 days → Slack #sales

### Informational (Daily Summary)
- Paywall hit count (upgrade opportunities) → Email
- New subscriptions → Slack #revenue
- Usage stats (posts, analyses) → Email digest

---

## Monitoring Checklist (Launch Week)

### Daily Checks (First 7 Days)

- [ ] Check Stripe webhook logs (all green?)
- [ ] Review application error logs (any new exceptions?)
- [ ] Verify QBO OAuth flows (any failures?)
- [ ] Check trial countdown notifications sent
- [ ] Monitor `/healthz` uptime (should be 100%)

### Weekly Checks (First Month)

- [ ] Run `python scripts/verify_prod_env.py` (all vars still set?)
- [ ] Run `./ops/smoke_live.sh` (end-to-end still works?)
- [ ] Review Sentry dashboard (any new error patterns?)
- [ ] Check Stripe Dashboard → Revenue (growing?)
- [ ] Review customer support tickets (any common issues?)

---

## Future Enhancements

### /metrics Prometheus Export

**Implement:**
```python
# app/routers/metrics.py
from prometheus_client import Counter, Gauge, generate_latest

posts_ok = Counter('posts_ok_total', 'Successful QBO posts')
posts_idempotent = Counter('posts_idempotent_total', 'Idempotent hits')
qbo_5xx = Counter('qbo_5xx_total', 'QBO 5xx errors')
stripe_webhook_fail = Counter('stripe_webhook_fail_total', 'Webhook failures')
tenants_active = Gauge('tenants_active', 'Active subscriptions')

@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

**Scrape Configuration (Prometheus):**
```yaml
scrape_configs:
  - job_name: 'ai-bookkeeper'
    static_configs:
      - targets: ['YOUR_DOMAIN:443']
    metrics_path: '/metrics'
    scheme: 'https'
```

### Grafana Dashboards

**Panels to add:**
1. QBO API call rate (requests/sec)
2. Stripe webhook success rate (%)
3. Post commit success rate (%)
4. Trial countdown (days left per tenant)
5. Revenue metrics (MRR, ARR)

---

## Support & Resources

- **Stripe Status:** https://status.stripe.com
- **QBO API Status:** https://status.developer.intuit.com
- **Render Status:** https://status.render.com
- **Sentry Docs:** https://docs.sentry.io

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-17  
**Applicable to:** AI Bookkeeper v0.9.1+

