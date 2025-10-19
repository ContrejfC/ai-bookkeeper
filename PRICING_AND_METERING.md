# Pricing and Metering Documentation

This document explains the AI Bookkeeper pricing model, usage metering, and billing implementation.

## Overview

AI Bookkeeper uses a tiered subscription model with usage-based overage charges. All billing is handled through Stripe with automated metering and invoicing.

---

## Plans and Pricing

### **Starter - $49/month**

**Target:** Solo SMBs

**Includes:**
- 1 entity
- 500 transactions/month
- $0.03 per transaction overage

**Features:**
- OCR with bounding boxes
- Propose/review/export workflows
- QuickBooks & Xero integration
- Email support

**Stripe Price IDs:**
- Monthly: `STRIPE_PRICE_STARTER_MONTHLY`
- Annual: `STRIPE_PRICE_STARTER_ANNUAL` ($41/month with 17% discount)
- Overage: `STRIPE_PRICE_OVERAGE_STARTER`

---

### **Team - $149/month**

**Target:** Small firms or operations teams

**Includes:**
- 3 entities
- 2,000 transactions/month
- $0.02 per transaction overage

**Features:**
- Everything in Starter
- Rules versioning
- Bulk approve
- Email ingest
- Priority email support

**Stripe Price IDs:**
- Monthly: `STRIPE_PRICE_TEAM_MONTHLY`
- Annual: `STRIPE_PRICE_TEAM_ANNUAL` ($124/month with 17% discount)
- Overage: `STRIPE_PRICE_OVERAGE_TEAM`

---

### **Firm - $499/month**

**Target:** Bookkeeping firms with multiple clients

**Includes:**
- 10 entities
- 10,000 transactions/month
- $0.015 per transaction overage

**Features:**
- Everything in Team
- API access
- Audit exports
- Role-based access control (RBAC)
- Quarterly review
- 99.5% SLA
- Priority support (24h target)

**Stripe Price IDs:**
- Monthly: `STRIPE_PRICE_FIRM_MONTHLY`
- Annual: `STRIPE_PRICE_FIRM_ANNUAL` ($414/month with 17% discount)
- Overage: `STRIPE_PRICE_OVERAGE_FIRM`

---

### **Enterprise - Custom**

**Target:** Compliance-heavy companies

**Includes:**
- 25+ entities
- 25,000+ transactions/month
- $0.01 per transaction overage

**Features:**
- Everything in Firm
- SSO with SAML
- Data Processing Agreement (DPA)
- Custom retention policies
- 99.9% SLA
- Dedicated success manager

**Pricing:** Contact sales@ai-bookkeeper.app

**Stripe Price IDs:**
- Custom subscription created per customer
- Overage: `STRIPE_PRICE_OVERAGE_ENTERPRISE`

---

### **Pilot Offer - $99/month for 3 months**

**Special limited-time offer**

**Includes:**
- 3 entities
- 3,000 transactions/month
- $0.02 per transaction overage
- All Team features

**Auto-migration:** After 3 months, automatically migrates to Team or Firm based on usage. Cancel anytime.

**Stripe Price IDs:**
- Monthly: `STRIPE_PRICE_PILOT_MONTHLY`

---

## Add-ons

### Extra Entity
- **Starter/Team:** $25/month per additional entity
- **Firm:** $15/month per additional entity
- **Stripe Price IDs:** `STRIPE_PRICE_ADDON_ENTITY_STARTER`, `STRIPE_PRICE_ADDON_ENTITY_FIRM`

### SSO (SAML)
- **Price:** $99/month
- **Stripe Price ID:** `STRIPE_PRICE_ADDON_SSO`

### White-label
- **Price:** $149/month
- **Stripe Price ID:** `STRIPE_PRICE_ADDON_WHITELABEL`

### Extended Log Retention
- **Price:** $49/month (extends from 12 to 24 months)
- **Stripe Price ID:** `STRIPE_PRICE_ADDON_RETENTION`

### Priority Support
- **Price:** $99/month (24-hour response target)
- **Note:** Included in Firm and Enterprise
- **Stripe Price ID:** `STRIPE_PRICE_ADDON_PRIORITY_SUPPORT`

---

## Discounts

### Annual Prepay
- **Discount:** 17% off monthly price
- Applied automatically to annual subscriptions

### Nonprofit
- **Discount:** 10% off all plans
- Contact support@ai-bookkeeper.app to apply

---

## Usage Metering

### What is a Billable Transaction?

A **billable transaction** is defined as:
- A bank or card line that is **ingested and processed through the propose endpoint** (`POST /api/post/propose`)

**NOT billable:**
- Idempotent retries (same transaction processed multiple times)
- Re-exports to QuickBooks/Xero
- Transaction edits or updates
- Preview operations in CSV cleaner

### How Usage is Tracked

1. **Increment:** When `POST /api/post/propose` is called with a new transaction
2. **Idempotency:** Uses `Idempotency-Key` header to prevent double billing
3. **Storage:** Usage counter stored in `BillingSubscriptionDB.metadata.tx_used_monthly`
4. **Reset:** Counter resets to 0 on the 1st day of each calendar month

### Monthly Quota and Overage

- **Quota:** Number of included transactions per plan (e.g., 500 for Starter)
- **Overage:** Transactions beyond quota are allowed but billed at overage rate
- **Hard Limit:** System enforces a hard limit at 2x quota to prevent runaway costs
- **Billing:** Overage is calculated and billed at **end of month** via Stripe usage records

### Monthly Reset Schedule

**Last day of month (11:59 PM UTC):**
1. Calculate overage for each active subscription
2. Post Stripe usage record for overage charges
3. Fire `overage_charged` GA4 event

**First day of month (12:01 AM UTC):**
1. Reset `tx_used_monthly` to 0 for all subscriptions
2. Clear idempotency key cache

---

## API Endpoints

### Checkout

**Endpoint:** `POST /api/billing/checkout`

**Request:**
```json
{
  "plan": "starter",
  "term": "monthly",
  "addons": ["addon_sso"]
}
```

**Response:**
```json
{
  "url": "https://checkout.stripe.com/..."
}
```

### Billing Status

**Endpoint:** `GET /api/billing/status?tenant_id={tenant_id}`

**Response:**
```json
{
  "plan": "starter",
  "term": "monthly",
  "entities_allowed": 1,
  "tx_quota_monthly": 500,
  "tx_used_monthly": 127,
  "overage_unit_price": 0.03,
  "addons": {
    "sso": false,
    "white_label": false,
    "retention_24m": false,
    "priority_support": false
  },
  "is_annual": false,
  "nonprofit_discount": false
}
```

### Webhook

**Endpoint:** `POST /api/billing/webhook`

**Headers:** `Stripe-Signature`

**Events Handled:**
- `checkout.session.completed` - Create subscription record
- `customer.subscription.created` - Initialize entitlements
- `customer.subscription.updated` - Update entitlements
- `invoice.paid` - Record payment, fire GA4 events
- `customer.subscription.deleted` - Cancel subscription

---

## Entitlements and Gates

### Entity Limit

- Enforced at entity creation
- Returns HTTP 402 if limit exceeded
- Upgrade link provided in error response

### Monthly Transaction Limit

- Soft limit: Allow overage (billed at month end)
- Hard limit: 2x quota (prevents runaway costs)
- Returns HTTP 402 if hard limit exceeded

### Feature Gates

| Feature | Starter | Team | Firm | Enterprise |
|---------|---------|------|------|------------|
| API Access | ❌ | ❌ | ✅ | ✅ |
| Audit Exports | ❌ | ❌ | ✅ | ✅ |
| RBAC | ❌ | ❌ | ✅ | ✅ |
| SSO | Add-on | Add-on | Add-on | ✅ |
| White-label | Add-on | Add-on | Add-on | ✅ |
| Priority Support | ❌ | ❌ | ✅ | ✅ |

---

## Stripe Configuration

### Required Environment Variables

```bash
# Backend
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
ALLOWED_ORIGINS=https://app.ai-bookkeeper.app,https://ai-bookkeeper-web.onrender.com

# Frontend
NEXT_PUBLIC_API_URL=https://api.ai-bookkeeper.app
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
NEXT_PUBLIC_GPT_DEEPLINK=https://chat.openai.com/g/...
NEXT_PUBLIC_DEMO_LOOM_URL=https://www.loom.com/share/...
```

### Creating Stripe Products

1. **Go to Stripe Dashboard → Products**
2. **Create products for each plan:**
   - Starter (Monthly & Annual)
   - Team (Monthly & Annual)
   - Firm (Monthly & Annual)
   - Pilot (Monthly only)

3. **Create metered usage prices:**
   - Set billing scheme to "Per unit"
   - Set usage aggregation to "Sum"
   - Create separate price for each plan's overage rate

4. **Create add-on products:**
   - Extra Entity (2 variants: Starter/Team and Firm)
   - SSO
   - White-label
   - Extended Retention
   - Priority Support

5. **Copy Price IDs and set as environment variables**

---

## Runbook

### Post Monthly Overage Usage to Stripe

**When:** Last day of month at 11:59 PM UTC

**Script:**
```python
from app.db.session import get_db_context
from app.services.usage_metering import UsageMeteringService

with get_db_context() as db:
    service = UsageMeteringService(db)
    results = service.run_monthly_billing_job()
    print(f"Billed {results['success']} subscriptions, total: ${results['total_billed']}")
```

**Cron:**
```cron
59 23 28-31 * * /path/to/python /path/to/scripts/bill_monthly_overage.py
```

### Reset Monthly Usage

**When:** First day of month at 12:01 AM UTC

**Script:**
```python
from app.db.session import get_db_context
from app.services.usage_metering import UsageMeteringService

with get_db_context() as db:
    service = UsageMeteringService(db)
    results = service.run_monthly_reset_job()
    print(f"Reset {results['total']} subscriptions")
```

**Cron:**
```cron
1 0 1 * * /path/to/python /path/to/scripts/reset_monthly_usage.py
```

### Adjust Entity Limits

**Manual adjustment:**
```python
from app.db.session import get_db_context
from app.db.models import BillingSubscriptionDB

with get_db_context() as db:
    sub = db.query(BillingSubscriptionDB).filter_by(tenant_id="tenant_123").first()
    sub.metadata["extra_entities"] = 2  # Add 2 extra entities
    db.commit()
```

### Add/Remove Add-ons

**Via Stripe Dashboard:**
1. Go to Customer → Subscriptions
2. Click subscription → Update subscription
3. Add/remove add-on price items
4. Webhook will automatically update entitlements

---

## Testing

### Test Cards

**Stripe Test Mode:**
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- Require 3DS: `4000 0025 0000 3155`

### Test Workflow

1. Set `STRIPE_SECRET_KEY` to test key (`sk_test_...`)
2. Create checkout session for Starter plan
3. Complete checkout with test card
4. Verify subscription appears in database
5. Call propose endpoint 550 times
6. Verify overage calculation
7. Manually trigger monthly billing job
8. Verify Stripe usage record created

---

## GA4 Events

| Event | When | Value |
|-------|------|-------|
| `bridge_viewed` | `/gpt-bridge` page load | - |
| `open_gpt_clicked` | User clicks "Open in ChatGPT" | - |
| `tool_opened` | `/tools/csv-cleaner` page load | - |
| `rows_previewed` | CSV preview rendered | row_count |
| `export_paywalled` | User hits paywall | action |
| `checkout_clicked` | User clicks checkout button | plan, term |
| `purchase` | Checkout completed | plan, value (first month) |
| `subscription_started` | Subscription created | plan, value (first month) |
| `overage_charged` | Monthly overage billed | value (overage amount) |

---

## Support

For questions about billing, pricing, or metering:
- **Email:** billing@ai-bookkeeper.app
- **Sales:** sales@ai-bookkeeper.app
- **Support:** support@ai-bookkeeper.app

