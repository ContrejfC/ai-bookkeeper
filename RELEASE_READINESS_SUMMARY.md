# Release & Cutover - Implementation Summary

**Date:** 2025-10-17  
**Status:** 🚧 PARTIAL DELIVERY (Stripe LIVE + Billing Polish COMPLETE)

---

## Executive Summary

Implemented production readiness features focusing on Stripe LIVE mode transition and billing enhancements:

1. ✅ **Billing Polish** - Added `trial_days_left` to `/billing/status`
2. ✅ **Stripe LIVE Verification** - Script to verify webhook configuration
3. ✅ **Stripe LIVE Documentation** - Complete switch guide with rollback plan
4. 🚧 **QBO Production** - PENDING (docs + verification script)
5. 🚧 **OpenAPI Versioning** - PENDING (freeze + CI guard)
6. 🚧 **Production Safety Scripts** - PENDING (env verify + smoke tests)
7. 🚧 **Monitoring Hooks** - PENDING (alerts documentation)
8. 🚧 **GPT Listing Bundle** - PENDING (store submission materials)

---

## Completed Features

### 1. Billing Status Enhancement

**Modified:** `app/services/billing.py`

**Added to `/api/billing/status` response:**
```json
{
  "trial_ends_at": "2025-10-31T12:00:00Z",
  "trial_days_left": 14,
  "subscription_status": "trialing"
}
```

**Logic:**
- `trial_days_left` = `max(0, (trial_end - now).days)`
- Returns `null` if not in trial
- Already included `trial_ends_at` (ISO datetime)

### 2. Stripe Webhook Verification Script

**File:** `scripts/verify_stripe_webhook.py`

**Features:**
- Lists all webhook endpoints (TEST or LIVE mode)
- Checks enabled status
- Verifies expected events subscribed
- Alerts if multiple active webhooks (potential issue)
- Detects missing events

**Usage:**
```bash
# TEST mode
STRIPE_SECRET_KEY=sk_test_... python scripts/verify_stripe_webhook.py

# LIVE mode
STRIPE_SECRET_KEY=sk_live_... python scripts/verify_stripe_webhook.py
```

**Expected Events:**
- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_failed`
- `customer.subscription.trial_will_end`

### 3. Stripe LIVE Switch Documentation

**File:** `docs/STRIPE_LIVE_SWITCH.md`

**Sections:**
1. Prerequisites (account activation, identity verification)
2. Create LIVE products/prices (via bootstrap script)
3. Create LIVE webhook (via Dashboard)
4. Update environment variables (Render/hosting)
5. Test LIVE billing flow (with Stripe test cards)
6. Monitor & verify (Dashboard + logs)
7. Rollback plan (revert to TEST or pause webhooks)
8. Common issues & fixes
9. Security checklist
10. Final verification

**Key Points:**
- Step-by-step guide for non-technical stakeholders
- Includes verification commands at each step
- Rollback procedures for safety
- Troubleshooting common webhook issues

---

## Pending Implementation

### A) QBO Production Switch

**Files to Create:**
- `docs/QBO_PROD_SWITCH.md` - Production app creation guide
- `scripts/check_qbo_env.py` - Environment verification

**Content Needed:**
- How to create QuickBooks production app (not marketplace)
- Set production redirect URIs
- Rotate `QBO_CLIENT_ID` and `QBO_CLIENT_SECRET` in Render
- Test OAuth flow in production
- Verify sandbox vs production base URLs

### B) OpenAPI Versioning & Freeze

**Files to Create:**
- `docs/openapi-v0.9.json` - Versioned snapshot
- `docs/OPENAPI_VERSIONING.md` - Version policy
- `.github/workflows/openapi_version_guard.yml` - CI check

**Logic:**
- Fail CI if `/openapi.json` changes without bumping `/docs/openapi-vX.Y.json`
- Semantic versioning (major.minor)
- Breaking changes = major bump
- New endpoints/fields = minor bump

### C) Production Safety Scripts

**Files to Create:**
- `scripts/verify_prod_env.py` - Check all required ENV vars
- `ops/smoke_live.sh` - End-to-end smoke test

**verify_prod_env.py checks:**
- `STRIPE_SECRET_KEY` (starts with `sk_live_`)
- `STRIPE_WEBHOOK_SECRET` (starts with `whsec_`)
- `STRIPE_PUBLISHABLE_KEY` (starts with `pk_live_`)
- `QBO_CLIENT_ID` and `QBO_CLIENT_SECRET`
- `DATABASE_URL` (postgres:// format)
- `BASE_URL` (https:// format)
- Optional: `SENTRY_DSN`

**smoke_live.sh sequence:**
1. `GET /healthz` → 200
2. `GET /billing/status` (with API key) → 200
3. `GET /qbo/status` → `connected:false` (pre-OAuth)
4. `GET /auth/qbo/start` → 302 with Location header
5. `POST /post/commit` (no plan) → 402 `ENTITLEMENT_REQUIRED`
6. After manual subscription: `POST /post/commit` with sample JE → 200
7. Repeat same JE → `idempotent:true`

### D) Monitoring & Alerts

**File to Create:**
- `docs/OBS_ALERTS.md` - What to alert on + how

**Alert Scenarios:**
- Stripe webhook failures (consecutive 5xx responses)
- QBO API 5xx spike (>10% of requests in 5min)
- POST /post/commit error rate >20%
- Trial ending soon (webhook `customer.subscription.trial_will_end`)
- Entitlement creation failures

**Metrics Integration:**
- Note: `/metrics` endpoint exists (from earlier implementation if added)
- Prometheus format preferred
- Grafana/Datadog/NewRelic integration examples

### E) GPT Listing Bundle

**File to Create:**
- `gpt_config/listing.md` - ChatGPT Store submission materials

**Content:**
- **Title:** "AI Bookkeeper for QuickBooks"
- **Subtitle:** "Automate QuickBooks journal entries with AI proposals and bulk posting"
- **Tags:** accounting, quickbooks, automation, bookkeeping, finance
- **Description:** (60-90 words, store-safe)
- **Screenshots:** 3 required (dashboard, proposals, QBO connection)
- **Demo Video:** 60-90 second Loom outline
- **Privacy Policy URL:**
- **Terms of Service URL:**

---

## Files Created/Modified (This Batch)

### New Files (3)
1. `scripts/verify_stripe_webhook.py` - Webhook verification script
2. `docs/STRIPE_LIVE_SWITCH.md` - LIVE mode switch guide
3. `RELEASE_READINESS_SUMMARY.md` - This file

### Modified Files (1)
1. `app/services/billing.py` - Added `trial_days_left` calculation

### Pending Files (~10)
- `scripts/check_qbo_env.py`
- `scripts/verify_prod_env.py`
- `ops/smoke_live.sh`
- `docs/QBO_PROD_SWITCH.md`
- `docs/OPENAPI_VERSIONING.md`
- `docs/OBS_ALERTS.md`
- `docs/openapi-v0.9.json`
- `.github/workflows/openapi_version_guard.yml`
- `gpt_config/listing.md`
- `docs/GO_LIVE_CHECKLIST.md` (final version)

---

## Testing & Verification

### Stripe Webhook Verification (Sample Output)

```
======================================================================
  Stripe Webhook Verification (TEST Mode)
======================================================================

Found 1 webhook endpoint(s):

1. ✅ ENABLED
   URL: https://ai-bookkeeper.onrender.com/api/billing/webhook
   Events: 6 subscribed
   ✅ All expected events subscribed

✅ 1 active webhook configured

======================================================================
  Verification Complete
======================================================================
```

### Billing Status Response (With Trial)

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
    "tx_analyzed": 5,
    "tx_posted": 2,
    "daily_analyze": 3,
    "daily_explain": 1
  },
  "trial_ends_at": "2025-10-31T12:00:00Z",
  "trial_days_left": 14,
  "subscription_status": "trialing"
}
```

---

## Deployment Notes

### Environment Variables Required

**Stripe (LIVE mode):**
```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRODUCT_STARTER=prod_...
STRIPE_PRICE_STARTER=price_...
STRIPE_PRODUCT_PRO=prod_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRODUCT_FIRM=prod_...
STRIPE_PRICE_FIRM=price_...
```

**QuickBooks (Production):**
```bash
QBO_CLIENT_ID=...
QBO_CLIENT_SECRET=...
QBO_REDIRECT_URI=https://YOUR_DOMAIN/api/auth/qbo/callback
QBO_ENVIRONMENT=production  # or sandbox
```

**Application:**
```bash
DATABASE_URL=postgresql://...
BASE_URL=https://YOUR_DOMAIN
SENTRY_DSN=...  # Optional
```

### Pre-Launch Checklist

- [ ] Run `scripts/verify_stripe_webhook.py` with LIVE key
- [ ] Verify billing status includes `trial_days_left`
- [ ] Test paywall (402 without subscription)
- [ ] Test subscription flow (checkout → webhook → entitlement)
- [ ] Test trial countdown display
- [ ] Verify webhook delivery in Stripe Dashboard
- [ ] Check application logs for webhook processing
- [ ] Test cancel/resubscribe flow
- [ ] Verify billing portal access
- [ ] Test QBO OAuth (if switching to production)

---

## Security Considerations

### Stripe LIVE Mode

1. **API Keys:**
   - Never commit LIVE keys to git
   - Use secure env var storage (Render, AWS Secrets)
   - Rotate keys if exposed

2. **Webhook Security:**
   - ALWAYS verify signature (`STRIPE_WEBHOOK_SECRET`)
   - Use HTTPS only (Render enforces this)
   - Rate limit webhook endpoint (future)

3. **Customer Data:**
   - Stripe handles PCI compliance
   - Never log full credit card numbers
   - Mask customer IDs in logs

### QBO Production Mode

1. **OAuth Credentials:**
   - Rotate from sandbox to production credentials
   - Production app requires approval (not marketplace)
   - Test redirect URIs carefully

2. **Token Storage:**
   - Access tokens in `qbo_tokens` table (encrypted at rest via DB)
   - Refresh tokens encrypted
   - Tokens never logged

---

## Known Limitations

1. **Alembic Migrations:** Chain issues remain (non-blocking, DB state correct)
2. **Metrics Endpoint:** Not fully implemented (counters exist, no Prometheus export yet)
3. **Audit Export:** Pending implementation (month-end compliance feature)
4. **Multi-Tenancy:** Billing per-tenant works, but no cross-tenant admin panel
5. **Webhook Retry:** Stripe retries automatically, but no manual retry UI

---

## Next Steps (Priority Order)

### High Priority (Pre-Launch)
1. **Complete QBO Production Switch** (docs + verification)
2. **Production Safety Scripts** (env verify + smoke test)
3. **Final GO_LIVE_CHECKLIST** (one-page, actionable)

### Medium Priority (Week 1 Post-Launch)
4. **OpenAPI Versioning** (freeze + CI guard)
5. **Monitoring Documentation** (alerts setup)
6. **Audit Export** (month-end compliance)

### Low Priority (Week 2+)
7. **GPT Listing Bundle** (ChatGPT Store submission)
8. **Metrics Enhancement** (Prometheus export)
9. **Alembic Chain Fix** (clean up migration history)

---

## Manual Steps Required

### Before LIVE Switch

1. **Stripe Account Setup:**
   - Complete identity verification
   - Add business details
   - Configure tax settings
   - Set up bank account for payouts

2. **QuickBooks App:**
   - Create production app (if not done)
   - Submit for review (if marketplace)
   - Configure redirect URIs
   - Test OAuth flow

3. **Domain & SSL:**
   - Configure custom domain (optional)
   - Ensure SSL certificate valid
   - Update OAuth redirect URIs
   - Update Stripe webhook URL

### After LIVE Switch

1. **Monitor First Week:**
   - Check webhook delivery daily
   - Verify subscriptions processing correctly
   - Monitor error rates
   - Check customer support inquiries

2. **Gradual Rollout:**
   - Start with internal testing
   - Invite pilot users (10-20)
   - Collect feedback
   - Fix critical issues before public launch

---

## Support & Escalation

- **Stripe Issues:** [Stripe Support](https://support.stripe.com)
- **QuickBooks Issues:** [Intuit Developer Support](https://developer.intuit.com/support)
- **Render Deployment:** [Render Support](https://render.com/docs/support)
- **Application Bugs:** GitHub Issues (or internal tracker)

---

**STATUS:** Stripe LIVE foundation complete. Remaining items documented and prioritized. Ready for QBO production switch and safety script implementation.

**ESTIMATED COMPLETION:** 2-4 hours for remaining high-priority items.

