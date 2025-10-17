# AI Bookkeeper - Billing Operations Runbook
**Version:** 1.0  
**Date:** 2025-10-17  
**Status:** Production Ready

## Overview

This runbook covers all operational procedures for the AI Bookkeeper billing system, including Stripe integration, entitlement management, and usage tracking.

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Running the Bootstrap Script](#running-the-bootstrap-script)
3. [Switching TEST → LIVE Mode](#switching-test--live-mode)
4. [Configuring Stripe Webhook](#configuring-stripe-webhook)
5. [Handling Failed Payments](#handling-failed-payments)
6. [Monthly Rollover Procedures](#monthly-rollover-procedures)
7. [Testing with Test Cards](#testing-with-test-cards)
8. [Monitoring & Alerts](#monitoring--alerts)
9. [Troubleshooting](#troubleshooting)

---

## Initial Setup

### Prerequisites

1. **Stripe Account**: Create account at https://stripe.com
2. **API Keys**: Get TEST mode keys from Stripe Dashboard
3. **Python Environment**: Python 3.8+ with dependencies installed

### Installation

```bash
# Install Stripe Python library
pip install stripe

# Verify installation
python3 -c "import stripe; print(stripe.__version__)"
```

---

## Running the Bootstrap Script

The bootstrap script creates products and prices in Stripe TEST mode.

### Step 1: Set Environment Variables

```bash
# Export your Stripe TEST secret key
export STRIPE_SECRET_KEY=sk_test_...

# Verify it's set
echo $STRIPE_SECRET_KEY
```

### Step 2: Run Bootstrap Script

```bash
# Navigate to project root
cd /path/to/ai-bookkeeper

# Run bootstrap script
python scripts/stripe_bootstrap.py
```

### Step 3: Verify Output

The script will output:

1. **Product IDs** - Created in Stripe
2. **Price IDs** - Created in Stripe
3. **Environment Configuration** - Copy to `.env` file

Example output:

```json
{
  "starter": {
    "product_id": "prod_ABC123",
    "price_id": "price_XYZ789",
    "amount": 4900,
    "metadata": {
      "plan": "starter",
      "tx_cap": "300",
      "bulk_approve": "false",
      "included_companies": "1"
    }
  }
}
```

### Step 4: Update .env File

```bash
# Copy environment variables to .env
cat >> .env << 'EOF'
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...  # Set after creating webhook
STRIPE_PRODUCT_STARTER=prod_...
STRIPE_PRICE_STARTER=price_...
STRIPE_PRODUCT_PRO=prod_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRODUCT_FIRM=prod_...
STRIPE_PRICE_FIRM=price_...
STRIPE_PRICE_FIRM_ADDON=price_...
EOF
```

---

## Switching TEST → LIVE Mode

### WARNING: Complete Testing First

Before switching to LIVE mode:

- ✅ Test all webhook events
- ✅ Test checkout flow
- ✅ Test billing portal
- ✅ Test cap enforcement
- ✅ Verify database operations

### Step 1: Get LIVE API Keys

1. Go to Stripe Dashboard
2. Toggle from "Test mode" to "Live mode"
3. Navigate to Developers > API keys
4. Copy "Secret key" (starts with `sk_live_...`)

### Step 2: Re-run Bootstrap in LIVE Mode

```bash
# IMPORTANT: This creates REAL products that can charge REAL money
export STRIPE_SECRET_KEY=sk_live_...

# Run bootstrap
python scripts/stripe_bootstrap.py

# Confirm when prompted
# Type "yes" when asked about live key
```

### Step 3: Update Environment

```bash
# Update .env with LIVE keys
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...  # New live webhook secret
STRIPE_PRODUCT_STARTER=prod_...  # New live product IDs
STRIPE_PRICE_STARTER=price_...    # New live price IDs
# ... etc
```

### Step 4: Deploy to Production

```bash
# Commit changes
git add .env.example config/stripe_products.json
git commit -m "chore: update Stripe products for LIVE mode"

# Deploy (Render, Railway, etc.)
git push origin main

# Verify environment variables in deployment platform
# Set STRIPE_SECRET_KEY and other vars in Render dashboard
```

---

## Configuring Stripe Webhook

### Step 1: Create Webhook Endpoint

1. Go to Stripe Dashboard > Developers > Webhooks
2. Click "Add endpoint"
3. Enter endpoint URL: `https://your-domain.com/api/billing/webhook`
4. Select events to listen for:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
   - `customer.subscription.trial_will_end`

### Step 2: Get Signing Secret

1. After creating webhook, click to view details
2. Copy "Signing secret" (starts with `whsec_...`)
3. Add to environment:

```bash
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Step 3: Test Webhook

```bash
# Use Stripe CLI to send test events
stripe trigger checkout.session.completed

# Check application logs for webhook processing
tail -f logs/app.log | grep "webhook"
```

### Step 4: Verify in Stripe Dashboard

1. Go to Developers > Webhooks
2. Click on your endpoint
3. View "Events" tab to see received events
4. Verify all show "Succeeded" status

---

## Handling Failed Payments

### Detection

Failed payments trigger the `invoice.payment_failed` webhook event.

### Automatic Actions

When payment fails:

1. Webhook sets `entitlement.active = False`
2. Webhook sets `subscription_status = "past_due"`
3. User loses access to paid features
4. User can still access free tier (50 analyze/day)

### Manual Recovery

#### Option 1: Customer Updates Payment Method

1. Customer goes to `/api/billing/portal`
2. Updates payment method
3. Stripe automatically retries payment
4. On success, webhook reactivates entitlement

#### Option 2: Admin Manual Activation

```python
# scripts/admin_reactivate_subscription.py
from app.db.session import get_db_context
from app.db.models import EntitlementDB

def reactivate_subscription(tenant_id: str):
    with get_db_context() as db:
        entitlement = db.query(EntitlementDB).filter(
            EntitlementDB.tenant_id == tenant_id
        ).first()
        
        if entitlement:
            entitlement.active = True
            entitlement.subscription_status = "active"
            db.commit()
            print(f"✓ Reactivated subscription for {tenant_id}")

if __name__ == "__main__":
    import sys
    reactivate_subscription(sys.argv[1])
```

Usage:

```bash
python scripts/admin_reactivate_subscription.py tenant_123
```

---

## Monthly Rollover Procedures

### Automated Rollover

The monthly rollover script resets usage counters on the 1st of each month.

#### Setup Cron Job

```bash
# Edit crontab
crontab -e

# Add monthly rollover (UTC)
0 0 1 * * cd /path/to/ai-bookkeeper && python scripts/roll_usage_month.py >> logs/rollover.log 2>&1
```

#### Render Cron Job

Add to `render.yaml`:

```yaml
- type: cron
  name: monthly-usage-rollover
  runtime: docker
  schedule: "0 0 1 * *"  # First day of month at midnight UTC
  startCommand: "python scripts/roll_usage_month.py"
  envVars:
    - key: DATABASE_URL
      sync: false
```

### Manual Rollover

```bash
# Run rollover manually
python scripts/roll_usage_month.py

# Expected output:
# Starting monthly usage rollover for 2025-11...
# Found 15 active tenants
#   Reset usage for tenant tenant_abc123
#   ...
# ✓ Monthly usage rollover completed for 2025-11
#   Processed 15 tenants
```

### Verification

```sql
-- Check current month's usage
SELECT tenant_id, year_month, tx_analyzed, tx_posted, last_reset_at
FROM usage_monthly
WHERE year_month = '2025-11'
ORDER BY tenant_id;

-- Verify all counters are 0
SELECT COUNT(*) as non_zero_count
FROM usage_monthly
WHERE year_month = '2025-11'
AND (tx_analyzed > 0 OR tx_posted > 0);
-- Should return 0
```

---

## Testing with Test Cards

### Stripe Test Cards

#### Successful Payment

```
Card number: 4242 4242 4242 4242
Expiry: Any future date (e.g., 12/25)
CVC: Any 3 digits (e.g., 123)
ZIP: Any 5 digits (e.g., 12345)
```

#### Payment Declined

```
Card number: 4000 0000 0000 0002
```

#### Insufficient Funds

```
Card number: 4000 0000 0000 9995
```

#### 3D Secure Authentication Required

```
Card number: 4000 0025 0000 3155
```

### Test Scenarios

#### Scenario 1: New Subscription

```bash
# 1. Create test tenant
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
  }'

# 2. Get billing status (should be inactive)
curl http://localhost:8000/api/billing/status \
  -H "Authorization: Bearer $TOKEN"

# 3. Create checkout session
curl -X POST http://localhost:8000/api/billing/checkout \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price_id": "'$STRIPE_PRICE_STARTER'"
  }'

# 4. Complete checkout in browser with test card
# 5. Verify webhook processed
# 6. Check billing status (should be active)
```

#### Scenario 2: Monthly Cap Enforcement

```bash
# 1. Post transactions until cap reached
for i in {1..301}; do
  curl -X POST http://localhost:8000/api/post/commit \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"je_ids": ["je_'$i'"]}'
done

# 2. Verify 402 response on 301st attempt
# Expected: {"code": "MONTHLY_CAP_EXCEEDED", ...}
```

#### Scenario 3: Free Tier Daily Cap

```bash
# 1. Call propose 51 times in one day
for i in {1..51}; do
  curl -X POST http://localhost:8000/api/post/propose \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"txn_ids": ["txn_'$i'"]}'
done

# 2. Verify 429 response on 51st attempt
# Expected: {"code": "FREE_CAP_EXCEEDED", ...}
```

---

## Monitoring & Alerts

### Key Metrics to Monitor

#### Webhook Success Rate

```sql
-- Webhook processing success rate
SELECT 
  DATE(created_at) as date,
  COUNT(*) as total_events,
  SUM(CASE WHEN processed = true THEN 1 ELSE 0 END) as processed,
  ROUND(100.0 * SUM(CASE WHEN processed = true THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM billing_events
WHERE created_at >= DATE('now', '-7 days')
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

#### Active Subscriptions

```sql
-- Count active subscriptions by plan
SELECT 
  plan,
  subscription_status,
  COUNT(*) as count
FROM entitlements
WHERE active = true
GROUP BY plan, subscription_status;
```

#### Usage Trends

```sql
-- Monthly usage by plan
SELECT 
  e.plan,
  u.year_month,
  AVG(u.tx_posted) as avg_posted,
  MAX(u.tx_posted) as max_posted,
  SUM(CASE WHEN u.tx_posted >= e.tx_cap THEN 1 ELSE 0 END) as at_cap_count
FROM usage_monthly u
JOIN entitlements e ON u.tenant_id = e.tenant_id
WHERE u.year_month >= DATE('now', 'start of month', '-3 months')
GROUP BY e.plan, u.year_month
ORDER BY u.year_month DESC, e.plan;
```

### Recommended Alerts

1. **Webhook Failure Rate > 5%**
   - Check Stripe Dashboard for errors
   - Verify webhook secret is correct
   - Check application logs

2. **Failed Payment Count > 10/day**
   - Review Stripe Dashboard for patterns
   - Consider sending customer communications

3. **Monthly Rollover Failure**
   - Check cron job logs
   - Verify database connectivity
   - Run manual rollover

---

## Troubleshooting

### Issue: Webhook Not Receiving Events

**Symptoms:**
- Subscription created in Stripe but not reflected in app
- Billing status shows inactive after checkout

**Diagnosis:**

```bash
# Check Stripe Dashboard > Webhooks
# Look for failed deliveries

# Check application logs
tail -f logs/app.log | grep webhook

# Test webhook manually
stripe trigger checkout.session.completed
```

**Resolution:**

1. Verify webhook URL is correct
2. Check STRIPE_WEBHOOK_SECRET is set
3. Verify application is accessible from internet
4. Check firewall/security group settings

### Issue: Entitlement Not Activating

**Symptoms:**
- User completed checkout but still can't post

**Diagnosis:**

```sql
-- Check entitlement status
SELECT * FROM entitlements WHERE tenant_id = 'tenant_123';

-- Check billing events
SELECT * FROM billing_events 
WHERE payload_json LIKE '%tenant_123%'
ORDER BY created_at DESC LIMIT 5;
```

**Resolution:**

```python
# Manual entitlement activation
from app.services.billing import BillingService
from app.db.session import get_db_context

with get_db_context() as db:
    service = BillingService(db)
    service.create_or_update_entitlement(
        tenant_id="tenant_123",
        plan="starter",
        active=True,
        subscription_status="active"
    )
```

### Issue: Usage Counter Stuck

**Symptoms:**
- User reports cap reached but shouldn't be

**Diagnosis:**

```sql
-- Check current usage
SELECT * FROM usage_monthly 
WHERE tenant_id = 'tenant_123' 
AND year_month = strftime('%Y-%m', 'now');
```

**Resolution:**

```sql
-- Manual reset (use with caution)
UPDATE usage_monthly
SET tx_posted = 0, tx_analyzed = 0, last_reset_at = datetime('now')
WHERE tenant_id = 'tenant_123'
AND year_month = strftime('%Y-%m', 'now');
```

### Issue: 402/429 Errors Not Showing Paywall

**Symptoms:**
- User gets blocked but no upgrade prompt

**Diagnosis:**

```bash
# Check middleware is loaded
grep -r "EntitlementGateMiddleware" app/

# Check error response format
curl -v http://localhost:8000/api/post/commit \
  -H "Authorization: Bearer $TOKEN"
```

**Resolution:**

Verify middleware is registered in `app/main.py`:

```python
from app.middleware.entitlements import EntitlementGateMiddleware

app.add_middleware(EntitlementGateMiddleware)
```

---

## Support Contacts

- **Stripe Support**: https://support.stripe.com
- **Application Logs**: `logs/app.log`
- **Database**: `sqlite:///ai_bookkeeper_demo.db` (local) or PostgreSQL (production)
- **Monitoring Dashboard**: [Link to monitoring tool]

---

## Appendix: Environment Variables Reference

```bash
# Required
STRIPE_SECRET_KEY=sk_test_... or sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Product IDs (from bootstrap)
STRIPE_PRODUCT_STARTER=prod_...
STRIPE_PRICE_STARTER=price_...
STRIPE_PRODUCT_PRO=prod_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRODUCT_FIRM=prod_...
STRIPE_PRICE_FIRM=price_...
STRIPE_PRICE_FIRM_ADDON=price_...

# Optional
BILLING_RETURN_URL=https://your-domain.com/dashboard
```

---

## Changelog

- **2025-10-17**: Initial runbook creation
- Future updates will be logged here

---

**END OF RUNBOOK**
