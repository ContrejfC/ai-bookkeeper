# Stripe LIVE Mode Switch Guide

**Purpose:** Transition from Stripe TEST mode to LIVE mode for production billing.

---

## Prerequisites

- [ ] Stripe account fully activated (identity verification complete)
- [ ] Business details configured in Stripe Dashboard
- [ ] Test mode working correctly (webhooks, checkout, portal)
- [ ] Ready to accept real payments

---

## Step 1: Create LIVE Products & Prices

```bash
# Set LIVE secret key
export STRIPE_SECRET_KEY=sk_live_XXXXX

# Run bootstrap script in LIVE mode
python scripts/stripe_bootstrap.py

# Output will include:
# - STRIPE_PRODUCT_STARTER=prod_XXXXX
# - STRIPE_PRICE_STARTER=price_XXXXX
# - STRIPE_PRODUCT_PRO=prod_XXXXX
# - STRIPE_PRICE_PRO=price_XXXXX
# - STRIPE_PRODUCT_FIRM=prod_XXXXX
# - STRIPE_PRICE_FIRM=price_XXXXX
```

**Save these IDs** - you'll need them for environment variables.

---

## Step 2: Create LIVE Webhook

### Via Stripe Dashboard

1. Go to [Stripe Dashboard](https://dashboard.stripe.com) → **Developers** → **Webhooks**
2. Toggle to **Live mode** (top-right)
3. Click **Add endpoint**
4. Configure:
   - **Endpoint URL:** `https://YOUR_PRODUCTION_DOMAIN/api/billing/webhook`
   - **Events to send:**
     - `checkout.session.completed`
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_failed`
     - `customer.subscription.trial_will_end`
5. Click **Add endpoint**
6. Copy the **Signing secret** (starts with `whsec_`)

### Verify Webhook

```bash
# Test that webhook is configured correctly
STRIPE_SECRET_KEY=sk_live_XXXXX python scripts/verify_stripe_webhook.py

# Expected output:
# ✅ 1 active webhook configured
# ✅ All expected events subscribed
```

---

## Step 3: Update Environment Variables

### In Render (or your hosting platform)

Update these environment variables to LIVE values:

```bash
# Stripe API Keys (LIVE)
STRIPE_SECRET_KEY=sk_live_XXXXXXXXXXXXX
STRIPE_PUBLISHABLE_KEY=pk_live_XXXXXXXXXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXXXXXXX

# Stripe Product/Price IDs (LIVE)
STRIPE_PRODUCT_STARTER=prod_XXXXX
STRIPE_PRICE_STARTER=price_XXXXX
STRIPE_PRODUCT_PRO=prod_XXXXX
STRIPE_PRICE_PRO=price_XXXXX
STRIPE_PRODUCT_FIRM=prod_XXXXX
STRIPE_PRICE_FIRM=price_XXXXX

# Billing Return URL (production domain)
BILLING_RETURN_URL=https://YOUR_PRODUCTION_DOMAIN
```

**Important:** After updating, redeploy your application!

---

## Step 4: Test LIVE Billing Flow

### 4.1 Create Test Subscription (with real card)

```bash
# Get API key for a test tenant
python scripts/create_api_key.py --tenant test_tenant_live --name "Live Test"

# Use test card (Stripe provides special cards for testing in live mode)
# Card: 4242 4242 4242 4242
# Expiry: Any future date
# CVC: Any 3 digits
```

**⚠️ WARNING:** In LIVE mode, real charges will occur. Use Stripe test cards or small amounts.

### 4.2 Verify Billing Status

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://YOUR_PRODUCTION_DOMAIN/api/billing/status
```

Expected response:
```json
{
  "active": true,
  "plan": "starter",
  "limits": {
    "tx_cap": 300,
    "bulk_approve": false,
    "included_companies": 1
  },
  "usage": {
    "tx_analyzed": 0,
    "tx_posted": 0
  },
  "trial_ends_at": "2025-10-31T12:00:00Z",
  "trial_days_left": 14,
  "subscription_status": "trialing"
}
```

### 4.3 Test Webhook Delivery

1. In Stripe Dashboard → **Developers** → **Webhooks** → **Your Endpoint**
2. Click **Send test webhook**
3. Select `customer.subscription.created`
4. Click **Send test webhook**
5. Verify **Response: 200 OK**

---

## Step 5: Test Paywall Behavior

### 5.1 Free Tier (No Subscription)

```bash
# Try to commit without subscription
curl -X POST https://YOUR_PRODUCTION_DOMAIN/api/post/commit \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"approvals": []}'

# Expected: HTTP 402
# {
#   "code": "ENTITLEMENT_REQUIRED",
#   "message": "Activate a plan to post to QuickBooks.",
#   "actions": ["/billing/portal"]
# }
```

### 5.2 After Subscription

```bash
# After subscribing, retry
curl -X POST https://YOUR_PRODUCTION_DOMAIN/api/post/commit \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "approvals": [
         {
           "txn_id": "test_1",
           "je": {
             "txnDate": "2025-10-17",
             "refNumber": "TEST-001",
             "privateNote": "Live test",
             "lines": [
               {"amount": 1.00, "postingType": "Debit", "accountRef": {"value": "46"}},
               {"amount": 1.00, "postingType": "Credit", "accountRef": {"value": "7"}}
             ]
           }
         }
       ]
     }'

# Expected: HTTP 200 (if QBO connected)
# or HTTP 400 (if QBO not connected yet)
```

---

## Step 6: Monitor & Verify

### 6.1 Check Stripe Dashboard

- **Customers:** Should see your test customer
- **Subscriptions:** Should show active trial or subscription
- **Logs:** Check for webhook deliveries (should be 200 OK)

### 6.2 Check Application Logs

```bash
# In Render or your logs
grep "Stripe webhook" logs/app.log

# Should see:
# "Stripe webhook received: customer.subscription.created"
# "Entitlement updated: active=True, plan=starter"
```

### 6.3 Run Full Smoke Test

```bash
# Run comprehensive smoke test (requires subscription active)
./ops/smoke_live.sh
```

---

## Rollback Plan

If issues occur after switching to LIVE:

### Option 1: Revert to TEST Mode

1. In Render, update environment variables back to `sk_test_...` and `whsec_test...`
2. Redeploy
3. Verify TEST mode working

### Option 2: Pause Webhooks

1. Stripe Dashboard → **Developers** → **Webhooks**
2. Click your webhook → **Disable**
3. Fix issues, then re-enable

---

## Common Issues

### Issue: Webhook Signature Verification Failed

**Cause:** Wrong `STRIPE_WEBHOOK_SECRET` (test secret in live mode)

**Fix:**
1. Get correct signing secret from Stripe Dashboard (live mode)
2. Update `STRIPE_WEBHOOK_SECRET` environment variable
3. Redeploy

### Issue: 402 ENTITLEMENT_REQUIRED After Subscribing

**Cause:** Webhook not received or failed

**Fix:**
1. Check Stripe Dashboard → Webhooks → View logs
2. If 4xx/5xx, check application logs for errors
3. Manually trigger webhook from Dashboard

### Issue: Customer Created But No Subscription

**Cause:** Checkout session completed but subscription not created

**Fix:**
1. Check Stripe Dashboard → Events
2. Look for `checkout.session.completed` event
3. Verify `customer.subscription.created` event followed
4. If missing, customer may have cancelled before completing

---

## Security Checklist

- [ ] LIVE keys never committed to git
- [ ] LIVE keys stored in secure environment variables (Render, AWS Secrets Manager)
- [ ] Webhook signing secret verified (not using test secret)
- [ ] HTTPS enforced (no HTTP in production)
- [ ] Rate limiting enabled (if applicable)
- [ ] Logging excludes sensitive data (card numbers, full keys)

---

## Final Verification

```bash
# Run full verification suite
STRIPE_SECRET_KEY=sk_live_XXXXX python scripts/verify_stripe_webhook.py
STRIPE_SECRET_KEY=sk_live_XXXXX python scripts/verify_prod_env.py

# Both should pass with ✅
```

---

## Support

- **Stripe Issues:** [Stripe Support](https://support.stripe.com)
- **Webhook Debugging:** Stripe Dashboard → Developers → Webhooks → Logs
- **Application Logs:** Render Dashboard → Logs tab

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-17  
**Applicable to:** AI Bookkeeper v0.9.1+

