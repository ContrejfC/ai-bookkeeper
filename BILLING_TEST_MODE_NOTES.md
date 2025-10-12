# Billing Test Mode — Configuration & Testing Guide

**Phase 2a — Stripe Integration**

---

## Environment Variables

### Required for Full Integration

```bash
# Stripe Secret Key (Test Mode)
STRIPE_SECRET_KEY=sk_test_51OFxyz...

# Stripe Webhook Secret (for signature verification)
STRIPE_WEBHOOK_SECRET=whsec_...

# Price IDs (from Stripe Dashboard → Products)
STRIPE_PRICE_STARTER=price_1OFStarter...
STRIPE_PRICE_PRO=price_1OFPro...
STRIPE_PRICE_FIRM=price_1OFFirm...

# App URL (for checkout redirects)
APP_URL=http://localhost:8000
```

### Optional for Stub Mode

If **no** environment variables are set:
- UI shows "Not Configured" banner
- API returns stub responses (no errors)
- System works in demo mode

---

## Creating Stripe Test Products

1. Go to [Stripe Dashboard → Products](https://dashboard.stripe.com/test/products)
2. Create 3 products:

**Starter Plan:**
- Name: "Starter Plan"
- Price: $49/month recurring
- Copy Price ID → `STRIPE_PRICE_STARTER`

**Pro Plan:**
- Name: "Pro Plan"
- Price: $149/month recurring
- Copy Price ID → `STRIPE_PRICE_PRO`

**Firm Plan:**
- Name: "Firm Plan"
- Price: $499/month recurring
- Copy Price ID → `STRIPE_PRICE_FIRM`

---

## Simulating Webhooks Locally

### 1. Install Stripe CLI

```bash
brew install stripe/stripe-cli/stripe
# or
curl -s https://packages.stripe.com/api/security/keypair/stripe-cli-gpg/public | gpg --dearmor | sudo tee /usr/share/keyrings/stripe.gpg
```

### 2. Login to Stripe

```bash
stripe login
```

### 3. Forward Webhooks to Local Server

```bash
stripe listen --forward-to localhost:8000/api/billing/stripe_webhook
```

**Output:**
```
> Ready! Your webhook signing secret is whsec_abc123xyz...
```

Copy the `whsec_...` value → set as `STRIPE_WEBHOOK_SECRET`

### 4. Trigger Test Events

```bash
# Subscription created
stripe trigger customer.subscription.created

# Subscription updated
stripe trigger customer.subscription.updated

# Payment failed
stripe trigger invoice.payment_failed
```

---

## Testing Checkout Flow

### 1. Start Local Server

```bash
uvicorn app.api.main:app --reload
```

### 2. Navigate to Billing

```
http://localhost:8000/billing
```

### 3. Select a Plan

Click "Select Plan" on any tier (Starter/Pro/Firm)

### 4. Use Test Card

Stripe redirects to checkout. Use test cards:

**Success:**
- Card: `4242 4242 4242 4242`
- Expiry: Any future date
- CVC: Any 3 digits
- ZIP: Any 5 digits

**Failure (Declined):**
- Card: `4000 0000 0000 0002`

**Requires Authentication:**
- Card: `4000 0025 0000 3155`

[Full test card list](https://stripe.com/docs/testing)

### 5. Complete Checkout

After payment:
- Redirects to `/billing?success=true`
- Alert: "Subscription successful!"
- Webhook fires → subscription created in DB

---

## Verifying Database State

```bash
# Check subscriptions
psql -d ai_bookkeeper -c "SELECT tenant_id, plan, status, stripe_customer_id FROM billing_subscriptions;"

# Check webhook events
psql -d ai_bookkeeper -c "SELECT type, stripe_event_id, processed, created_at FROM billing_events ORDER BY created_at DESC LIMIT 10;"
```

---

## Testing Coupons

### 1. Create Coupon in Stripe Dashboard

Go to [Products → Coupons](https://dashboard.stripe.com/test/coupons)

Create coupon:
- ID: `PILOT20`
- Discount: 20% off
- Duration: Once

### 2. Apply in UI

1. Go to `/billing`
2. Enter `PILOT20` in coupon field
3. Click "Apply"
4. Select plan → coupon applied at checkout

---

## Webhook Event Types

**Handled by System:**

| Event | Action |
|-------|--------|
| `customer.subscription.created` | Create subscription record |
| `customer.subscription.updated` | Update status, renewal date |
| `customer.subscription.deleted` | Mark as canceled |
| `invoice.payment_failed` | Mark as past_due |

**Logged but Not Processed:**
- All other event types logged to `billing_events` for audit

---

## Idempotency

Webhooks are **idempotent**:
- Duplicate events (same `stripe_event_id`) are ignored
- Only first occurrence processed
- All events logged for audit

**Test:**
```bash
# Send same event twice
curl -X POST http://localhost:8000/api/billing/stripe_webhook \
  -H "Content-Type: application/json" \
  -H "Stripe-Signature: test_sig" \
  -d @artifacts/billing/sample_webhook.json

# Second call returns: "Event already processed"
```

---

## Subscription States

| Status | Meaning | UI Display |
|--------|---------|------------|
| `active` | Paid, current | Green pill |
| `trialing` | In trial period | Blue pill |
| `past_due` | Payment failed | Red pill + warning |
| `canceled` | Subscription ended | Gray pill |

**Cancel Behavior:**
- `cancel_at_period_end=true` → shows "Canceling" badge
- Access continues until `current_period_end`

---

## Customer Portal

**Purpose:** Let customers manage their subscription:
- Update payment method
- View invoices
- Cancel subscription
- Change plan

**Access:**
1. Go to `/billing`
2. Click "Manage Billing"
3. Redirected to Stripe Customer Portal

**Requirements:**
- Active subscription
- `stripe_customer_id` present

---

## Troubleshooting

### "Billing not configured" Banner

**Cause:** `STRIPE_SECRET_KEY` not set

**Fix:**
```bash
export STRIPE_SECRET_KEY=sk_test_...
```

### Checkout Button Does Nothing

**Cause:** Price IDs not configured

**Fix:**
```bash
export STRIPE_PRICE_STARTER=price_...
export STRIPE_PRICE_PRO=price_...
export STRIPE_PRICE_FIRM=price_...
```

### Webhooks Not Firing

**Cause:** Webhook secret invalid or Stripe CLI not running

**Fix:**
```bash
# Restart Stripe CLI
stripe listen --forward-to localhost:8000/api/billing/stripe_webhook

# Copy new secret
export STRIPE_WEBHOOK_SECRET=whsec_...
```

### "Invalid signature" Error

**Cause:** Webhook secret mismatch

**Fix:**
- Check `STRIPE_WEBHOOK_SECRET` matches Stripe CLI output
- In production, use webhook secret from Dashboard

---

## Production Deployment

### 1. Switch to Live Mode

```bash
# Use live keys (sk_live_...)
export STRIPE_SECRET_KEY=sk_live_...
export STRIPE_WEBHOOK_SECRET=whsec_live_...

# Update price IDs to live versions
export STRIPE_PRICE_STARTER=price_live_...
```

### 2. Configure Webhook Endpoint

In [Stripe Dashboard → Webhooks](https://dashboard.stripe.com/webhooks):
- Add endpoint: `https://yourdomain.com/api/billing/stripe_webhook`
- Select events:
  - `customer.subscription.created`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_failed`
- Copy signing secret → `STRIPE_WEBHOOK_SECRET`

### 3. Update App URL

```bash
export APP_URL=https://yourdomain.com
```

### 4. Test in Production

Use Stripe Dashboard → Developers → Webhooks → Send test webhook

---

## Security Notes

- **CSRF:** Webhook endpoint exempt (external call)
- **RBAC:** Checkout/Portal restricted to Owner role
- **Signature Verification:** All webhooks verified via `Stripe-Signature` header
- **Idempotency:** Prevents duplicate processing
- **Audit:** All actions logged to `billing_events` and `decision_audit_log`

---

## References

- [Stripe Testing Docs](https://stripe.com/docs/testing)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [Stripe CLI](https://stripe.com/docs/stripe-cli)
- [Test Cards](https://stripe.com/docs/testing#cards)

---

**Status:** Test mode ready  
**Version:** Phase 2a  
**Last Updated:** 2024-10-11

