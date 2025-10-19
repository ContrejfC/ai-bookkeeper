# 🚀 Launch-Ready Guide - Final Steps to Go Live

This guide walks you through the final validation and launch process for Google Ads.

---

## ⚡ Quick Start

```bash
# 1. Validate everything
make validate

# 2. If all 8 tests pass, deploy
git push origin main

# 3. Wait for Render deployment (3-5 minutes)

# 4. Run final checks
make smoke
make usage
make monthend-dry

# 5. Launch ads (follow GOOGLE_ADS_CAMPAIGN_CONFIG.md)
```

---

## 📋 The 8 Validation Criteria

Before launching Google Ads, ALL 8 criteria must pass:

### ✅ 1. Domains and CORS Work

**What:** Frontend at `app.ai-bookkeeper.app` calls API at `api.ai-bookkeeper.app` without errors

**Test:**
```bash
# Visit in browser
open https://app.ai-bookkeeper.app/gpt-bridge
# Check DevTools Console - no CORS errors
# Check GA4 DebugView - bridge_viewed event fires
```

**Auto-test:**
```bash
make validate
# Test 1 should pass
```

---

### ✅ 2. Stripe SKUs Match Approved Pricing

**What:** All Stripe price IDs in `config/stripe_price_map.json` match approved pricing

**Approved Pricing:**
- Starter: $49/mo (500 tx, $0.03/tx overage)
- Team: $149/mo (2,000 tx, $0.02/tx overage)
- Firm: $499/mo (10,000 tx, $0.015/tx overage)
- Enterprise: Custom (25,000+ tx, $0.01/tx overage)
- Pilot: $99/mo × 3 months (auto-migrate to Team/Firm)

**Test:**
```bash
make verify-stripe
# Should show all plans, overage prices, and add-ons loaded
```

**Manual:**
1. Open `config/stripe_price_map.json`
2. Verify no "placeholder" values
3. Cross-reference with Stripe Dashboard

---

### ✅ 3. Entitlements and Metering Enforce Quotas

**What:** Usage metering tracks transactions, calculates overage, blocks when exceeded

**Test:**
```bash
make usage
# Expected output:
# - 600 transactions processed
# - 100 overage (600 - 500)
# - $3.00 overage amount (100 × $0.03)
```

**Verification:**
- Starter tenant with 600 proposed tx shows 100 overage
- Export/post blocked when over hard limit (2× quota)
- Overage queued for month-end billing

---

### ✅ 4. Webhooks Update Access Instantly

**What:** Stripe webhooks process in <10 seconds and update entitlements

**Events to test:**
- `checkout.session.completed` - Creates subscription
- `invoice.paid` - Records payment
- `customer.subscription.updated` - Updates entitlements
- `customer.subscription.deleted` - Cancels access

**Manual test:**
1. Go to Stripe Dashboard → Webhooks
2. Find: `https://api.ai-bookkeeper.app/api/billing/webhook`
3. Send test event: `checkout.session.completed`
4. Check Render logs - should process in <10s
5. Check database - subscription created

---

### ✅ 5. E2E Purchase Succeeds

**What:** Complete checkout flow from pricing page to success page

**Steps:**
1. Visit `https://app.ai-bookkeeper.app/pricing`
2. Click "Start Starter"
3. Enter test card: `4242 4242 4242 4242`
4. Complete checkout
5. Redirect to `/success`
6. GA4 Realtime shows:
   - `purchase` (value: $49)
   - `subscription_started` (value: $49)
7. Stripe Dashboard shows new subscription

**Auto-test:**
```bash
make smoke
# Playwright tests will verify pages load and redirect to Stripe
```

---

### ✅ 6. Month-End Dry Run Works

**What:** Monthly billing job calculates overage and posts to Stripe (idempotent)

**Test:**
```bash
make monthend-dry
# Should show:
# - All subscriptions processed
# - Overage calculated correctly
# - Idempotent (re-running doesn't double-bill)
```

**Verification:**
```bash
# Run twice to verify idempotency
make monthend-dry
make monthend-dry
# Second run should detect existing billing for current month
```

---

### ✅ 7. Legal and Trust Pages Are Public

**What:** Privacy, Terms, DPA, Security pages load without authentication

**Test:**
```bash
make validate
# Test 7 checks all legal pages

# Or manually:
curl https://app.ai-bookkeeper.app/privacy
curl https://app.ai-bookkeeper.app/terms
curl https://app.ai-bookkeeper.app/dpa
curl https://app.ai-bookkeeper.app/security
```

**Verification:**
- All pages return 200 OK
- No authentication required
- Footer links work
- Contact email visible: support@ai-bookkeeper.app

---

### ✅ 8. Performance Is Green

**What:** Key pages load fast (LCP <2.5s), CSV preview <10s

**Test:**
```bash
# Lighthouse audit
npx lighthouse https://app.ai-bookkeeper.app/gpt-bridge --view
npx lighthouse https://app.ai-bookkeeper.app/tools/csv-cleaner --view

# Expected:
# - LCP < 2.5s
# - CLS < 0.1
# - INP < 200ms
# - Performance Score > 90
```

**CSV Performance:**
- Upload sample CSV
- Verify preview renders in <10 seconds
- Verify ≤50 rows displayed

---

## 🚨 Pre-Launch Validation

Run the complete validation:

```bash
make validate
```

**Expected output:**
```
PRE-LAUNCH VALIDATION
============================================================
Test 1: Domains and CORS work
✅ PASS - Domains and CORS work

Test 2: Stripe SKUs match approved pricing
✅ PASS - Stripe SKUs match approved pricing

Test 3: Entitlements and metering enforce quotas
✅ PASS - Entitlements and metering enforce quotas

Test 4: Webhooks update access instantly
✅ PASS - Webhooks update access instantly

Test 5: E2E purchase succeeds
✅ PASS - E2E purchase succeeds

Test 6: Month-end dry run works
✅ PASS - Month-end dry run works

Test 7: Legal and trust pages are public
✅ PASS - Legal and trust pages are public

Test 8: Performance is green
✅ PASS - Performance is green

VALIDATION SUMMARY
============================================================
Passed: 8/8
Failed: 0/8

✅ ALL TESTS PASSED!

🚀 READY TO LAUNCH GOOGLE ADS
```

---

## 🎯 If All 8 Pass - Launch Google Ads

Follow `GOOGLE_ADS_CAMPAIGN_CONFIG.md` for complete campaign setup.

### Quick Launch Steps:

1. **Create Campaign in Google Ads**
   - Type: Search
   - Goal: Conversions
   - Budget: $40/day
   - Bidding: Maximize conversions

2. **Add Keywords (Exact Match)**
   - `[quickbooks auto categorize]`
   - `[ai bookkeeping quickbooks]`
   - `[bank csv to qbo]`
   - `[post journal entries quickbooks]`
   - `[xero auto categorize]`

3. **Create Responsive Search Ad**
   - **Headlines:** QuickBooks Auto-Categorize, Clean Bank CSV → QBO, Preview 50 Rows Free
   - **Descriptions:** Upload a bank CSV, preview 50 rows free, then export or post to QuickBooks/Xero. Starter $49/mo. Metered overage.
   - **Final URL:** `https://app.ai-bookkeeper.app/gpt-bridge?utm_source=google&utm_medium=search&utm_campaign=core_intent&utm_term={keyword}`

4. **Add Extensions**
   - Sitelinks: Free CSV Cleaner, View Pricing, ChatGPT Integration, Security
   - Callouts: Free CSV Tool, SOC 2 Compliant, 500 Transactions Included
   - Structured Snippets: Plans (Starter, Team, Firm, Enterprise)

5. **Set Conversions**
   - Primary: `purchase` (value-based)
   - Secondary: `export_paywalled` (observation)

6. **Enable Campaign**

---

## 📊 Launch Day Monitoring

### Hour 0 (Launch)
- [ ] Enable campaign
- [ ] Verify first impression (within 30 minutes)
- [ ] Open GA4 Realtime
- [ ] Open Render logs
- [ ] Open Stripe Dashboard

### Hour 1
- [ ] Check impressions count
- [ ] Check first click (if any)
- [ ] Monitor for errors
- [ ] Verify quality score appearing

### Hour 24
- [ ] Impressions: _____
- [ ] Clicks: _____
- [ ] CTR: _____%
- [ ] Conversions: _____
- [ ] CPC: $_____
- [ ] CPA: $_____

### Week 1
- [ ] Daily monitoring
- [ ] Pause keywords with CPC > $8 and 0 conversions after 50 clicks
- [ ] Add negative keywords from Search Terms
- [ ] Optimize ad copy if CTR < 3%

---

## 🛑 Pause Conditions

**Immediately pause campaign if:**
- Site goes down (check Render status)
- Checkout flow breaks (test daily)
- GA4 stops tracking (verify in Realtime)
- CPC > $10 consistently
- No conversions after $300 spend

**Pause individual keywords if:**
- CPC > $8 and 0 conversions after 50 clicks
- Quality Score < 4 (landing page issue)
- Irrelevant search terms triggering

---

## 📞 Emergency Contacts

**Technical Issues:**
- Render: https://render.com/support
- Immediate action: Pause campaign, investigate, fix, resume

**Billing Issues:**
- Stripe: https://support.stripe.com/
- Check webhook logs, verify keys

**Tracking Issues:**
- GA4: https://support.google.com/analytics/
- Verify gtag.js loaded, check DebugView

---

## ✅ Final Checklist

Before enabling ads:

- [ ] `make validate` passes all 8 tests
- [ ] Stripe live mode enabled with real price IDs
- [ ] GA4 property created and linked to Google Ads
- [ ] Test purchase completed successfully
- [ ] All environment variables set correctly
- [ ] Custom domains working with SSL
- [ ] Uptime monitoring configured
- [ ] Support email active
- [ ] Credit card added to Google Ads
- [ ] Campaign created and ready to enable

**Once complete:**
- [ ] Enable campaign
- [ ] Monitor first hour closely
- [ ] Document results
- [ ] Iterate and optimize

---

## 🎉 Ready to Launch!

If `make validate` shows **8/8 tests passed**, you're ready to launch Google Ads!

See `GOOGLE_ADS_CAMPAIGN_CONFIG.md` for complete campaign settings.

**Good luck! 🚀**

