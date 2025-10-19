# Google Ads Prelaunch Checklist

Complete this checklist before launching Google Ads campaigns to ensure proper tracking, crawlability, and conversion attribution.

## ✅ Domain & SSL Configuration

- [ ] **Custom domains configured**
  - Frontend: `https://app.ai-bookkeeper.app`
  - API: `https://api.ai-bookkeeper.app`
- [ ] **SSL certificates valid** (check with: `curl -I https://app.ai-bookkeeper.app`)
- [ ] **HTTPS redirect enabled** (HTTP → HTTPS)
- [ ] **HSTS headers enabled** (check in browser DevTools → Network)

## ✅ Final URLs & Crawlability

All Final URLs must be publicly accessible and crawlable by Googlebot.

### Primary Landing Pages

- [ ] `/gpt-bridge` - Loads without errors
  - URL: `https://app.ai-bookkeeper.app/gpt-bridge`
  - Status: 200 OK
  - Indexed: Check Google Search Console

- [ ] `/tools/csv-cleaner` - Loads without errors
  - URL: `https://app.ai-bookkeeper.app/tools/csv-cleaner`
  - Status: 200 OK
  - Indexed: Check Google Search Console

- [ ] `/pricing` - Loads without errors
  - URL: `https://app.ai-bookkeeper.app/pricing`
  - Status: 200 OK
  - Indexed: Check Google Search Console

### Supporting Pages

- [ ] `/` (Homepage) - Loads
- [ ] `/success` - Loads
- [ ] `/cancel` - Loads
- [ ] `/privacy` - Loads
- [ ] `/terms` - Loads

### Crawlability Verification

Run these tests:

```bash
# Check robots.txt allows crawling
curl https://app.ai-bookkeeper.app/robots.txt
# Should NOT disallow /gpt-bridge, /tools/csv-cleaner, or /pricing

# Check sitemap includes key pages
curl https://app.ai-bookkeeper.app/sitemap.xml | grep -E "(gpt-bridge|csv-cleaner|pricing)"

# Test Googlebot rendering
# Use Google Search Console → URL Inspection → Test Live URL
```

- [ ] **robots.txt** allows Googlebot to crawl landing pages
- [ ] **Sitemap.xml** includes all landing pages
- [ ] **No noindex meta tags** on landing pages
- [ ] **Google Search Console** verified and no crawl errors

## ✅ GA4 Configuration

- [ ] **GA4 Property created**
  - Property ID: `G-XXXXXXXXXX`
  - Set in `NEXT_PUBLIC_GA_ID`

- [ ] **GA4 tag installed** (check with GA Debugger extension)

- [ ] **Test events in Realtime**
  1. Open GA4 → Reports → Realtime
  2. Visit `/gpt-bridge` → See `bridge_viewed`
  3. Visit `/tools/csv-cleaner` → See `tool_opened`
  4. Upload CSV → See `rows_previewed`
  5. Complete test purchase → See `purchase` and `subscription_started`

- [ ] **Events visible in DebugView**
  - Enable debug mode: `gtag('set', 'debug_mode', true)`
  - Check DebugView for all events

- [ ] **Conversion events configured**
  - `purchase` (Primary conversion, value-based)
  - `subscription_started` (Secondary conversion)
  - Set as conversions in GA4 Admin → Events → Mark as conversion

## ✅ Google Ads Integration

- [ ] **Google Ads account created/activated**
- [ ] **Billing method added** to Google Ads
- [ ] **GA4 linked to Google Ads**
  - GA4 Admin → Google Ads Links → Link account
  - Enable data sharing

- [ ] **Conversion import configured**
  - Google Ads → Tools → Conversions → Import
  - Select GA4 events: `purchase`, `subscription_started`
  - Set `purchase` as primary goal

- [ ] **UTM parameters tested**
  - Test URL: `https://app.ai-bookkeeper.app/pricing?utm_source=google&utm_medium=cpc&utm_campaign=test`
  - Verify UTM parameters appear in GA4 reports

## ✅ Test Purchase Flow

Complete at least ONE real test purchase to verify end-to-end tracking:

### Test Purchase Steps

1. **Start in Google Ads Campaign Preview**
   - Or add UTM parameters: `?utm_source=google&utm_medium=cpc&utm_campaign=test`

2. **Navigate to `/pricing`**
   - Verify `checkout_clicked` fires in GA4 Realtime

3. **Click "Start Starter"**
   - Should redirect to Stripe Checkout
   - Use Stripe test card: `4242 4242 4242 4242`

4. **Complete checkout**
   - Should redirect to `/success`
   - Verify `purchase` event fires (value = $49)
   - Verify `subscription_started` event fires (value = $49)

5. **Verify in Stripe Dashboard**
   - Check subscription created
   - Check invoice paid

6. **Verify in GA4**
   - Realtime → Events → See `purchase` and `subscription_started`
   - Conversion value: $49.00

7. **Verify in Google Ads (after 24-48 hours)**
   - Conversions → Check imported conversions
   - Should see test purchase with value

### Test Purchase Checklist

- [ ] Test purchase completed successfully
- [ ] `purchase` event appeared in GA4 Realtime
- [ ] `subscription_started` event appeared in GA4 Realtime
- [ ] Event value correct ($49 for Starter)
- [ ] UTM parameters preserved through checkout
- [ ] Conversion appeared in Google Ads (wait 24-48 hours)

**Screenshot Locations:**
- `artifacts/ga4_test_purchase_realtime.png`
- `artifacts/ga4_test_purchase_debugview.png`
- `artifacts/stripe_test_subscription.png`
- `artifacts/google_ads_conversion_import.png`

## ✅ Performance Verification

Run Lighthouse audits on key landing pages:

### `/gpt-bridge`
```bash
# Run Lighthouse
npx lighthouse https://app.ai-bookkeeper.app/gpt-bridge --view
```

- [ ] **LCP (Largest Contentful Paint):** < 2.5s
- [ ] **CLS (Cumulative Layout Shift):** < 0.1
- [ ] **INP (Interaction to Next Paint):** < 200ms
- [ ] **Performance Score:** > 90

### `/tools/csv-cleaner`
```bash
npx lighthouse https://app.ai-bookkeeper.app/tools/csv-cleaner --view
```

- [ ] **LCP:** < 2.5s
- [ ] **CLS:** < 0.1
- [ ] **INP:** < 200ms
- [ ] **CSV upload response:** < 10s

### `/pricing`
- [ ] **LCP:** < 2.5s
- [ ] **All pricing information visible**
- [ ] **Checkout buttons functional**

## ✅ CORS & API Connectivity

- [ ] **CORS configured correctly**
  ```bash
  # Test CORS from browser console at app.ai-bookkeeper.app
  fetch('https://api.ai-bookkeeper.app/healthz')
    .then(r => r.json())
    .then(d => console.log('API Response:', d))
  ```
  - Should NOT see CORS errors

- [ ] **API endpoints respond**
  ```bash
  curl https://api.ai-bookkeeper.app/healthz
  curl -X POST https://api.ai-bookkeeper.app/api/billing/checkout \
    -H "Content-Type: application/json" \
    -d '{"plan":"starter","term":"monthly","addons":[]}'
  ```

- [ ] **Environment variables correct**
  - Backend `ALLOWED_ORIGINS` includes `https://app.ai-bookkeeper.app`
  - Frontend `NEXT_PUBLIC_API_URL` = `https://api.ai-bookkeeper.app`

## ✅ Stripe Configuration

- [ ] **Live mode enabled** (`sk_live_...`)
- [ ] **All price IDs in `config/stripe_price_map.json`**
  ```bash
  make verify-stripe
  ```
- [ ] **Webhook endpoint active**
  - URL: `https://api.ai-bookkeeper.app/api/billing/webhook`
  - Events: `checkout.session.completed`, `invoice.paid`, etc.
  - Status: Active (check Stripe Dashboard)

- [ ] **Test payment processed successfully**

## ✅ Usage Metering

- [ ] **Usage simulation passes**
  ```bash
  make usage
  # Should show: 600 tx, 100 overage, $3.00 for Starter
  ```

- [ ] **Month-end billing works**
  ```bash
  make monthend-dry
  # Should calculate overage correctly
  ```

- [ ] **Idempotency verified**
  ```bash
  make monthend-dry
  make monthend-dry
  # Second run should be idempotent (no double billing)
  ```

## ✅ E2E Tests Pass

- [ ] **Smoke tests pass**
  ```bash
  make smoke
  # All tests should pass
  ```

- [ ] **Key scenarios work:**
  - CSV upload and preview
  - Checkout flow
  - GA4 events fire
  - Legal pages load

## ✅ Ad Campaign Setup (Draft)

Before launching, prepare your first campaign:

### Campaign Settings
- [ ] **Campaign Type:** Search
- [ ] **Goal:** Conversions
- [ ] **Budget:** $50-100/day (start conservative)
- [ ] **Bidding:** Maximize conversions (or Target CPA after data)
- [ ] **Location:** United States (or target market)
- [ ] **Language:** English

### Keywords (5-10 to start)
- [ ] `ai bookkeeping software`
- [ ] `automated bookkeeping`
- [ ] `bookkeeping automation tool`
- [ ] `quickbooks ai integration`
- [ ] `ai accounting software`

### Ad Copy (2-3 variants)
**Example 1:**
- Headline 1: AI Bookkeeping from $49/mo
- Headline 2: Automate Journal Entries
- Headline 3: QuickBooks & Xero Ready
- Description: Upload bank statements and get AI-powered categorization. Try our free CSV cleaner. Plans start at $49/month.

**Example 2:**
- Headline 1: AI-Powered Bookkeeping
- Headline 2: Save Hours Every Month
- Headline 3: Free CSV Cleaner Tool
- Description: Automated transaction categorization for QuickBooks & Xero. Starter plan: $49/mo, 500 transactions. Try free tool now.

### Final URLs
- [ ] Primary: `https://app.ai-bookkeeper.app/pricing?utm_source=google&utm_medium=cpc&utm_campaign=search_brand`
- [ ] Alternate: `https://app.ai-bookkeeper.app/tools/csv-cleaner?utm_source=google&utm_medium=cpc&utm_campaign=search_free_tool`
- [ ] GPT: `https://app.ai-bookkeeper.app/gpt-bridge?utm_source=google&utm_medium=cpc&utm_campaign=search_gpt`

### Ad Extensions
- [ ] **Sitelinks:** Pricing, Free Tool, ChatGPT Integration, Security
- [ ] **Callouts:** Free CSV Cleaner, SOC 2 Compliant, 500 Transactions Included
- [ ] **Structured Snippets:** Plans: Starter, Team, Firm, Enterprise

## ✅ Monitoring & Alerts

- [ ] **GA4 Alerts configured**
  - Alert if no `purchase` events for 7 days
  - Alert if conversion rate drops > 50%

- [ ] **Stripe alerts configured**
  - Low balance alert
  - Failed payment alert

- [ ] **Render monitoring**
  - Uptime monitoring enabled
  - Error rate alerts configured

- [ ] **Daily check routine established**
  - Check Render logs
  - Check GA4 Realtime
  - Check Stripe Dashboard
  - Check Google Ads performance

## 🚀 Final Go/No-Go Decision

**All items above must be checked before launching ads.**

### Go-Live Checklist
- [ ] All technical items above: ✅
- [ ] Test purchase completed: ✅
- [ ] Performance targets met: ✅
- [ ] Team trained on monitoring: ✅
- [ ] Budget approved: ✅
- [ ] Support email active: ✅

### Launch Day Steps

1. **Morning (9 AM):**
   - [ ] Final health check (`make health`)
   - [ ] Check GA4 Realtime works
   - [ ] Verify Stripe webhook active

2. **Launch (10 AM):**
   - [ ] Activate Google Ads campaign
   - [ ] Set campaign to "Eligible"
   - [ ] Monitor for first impression

3. **First Hour:**
   - [ ] Check for ad impressions
   - [ ] Monitor GA4 Realtime for traffic
   - [ ] Check for CORS errors in browser console

4. **First Day:**
   - [ ] Monitor conversion tracking
   - [ ] Check quality score
   - [ ] Adjust bids if needed
   - [ ] Review search terms

5. **First Week:**
   - [ ] Analyze conversion rate
   - [ ] Optimize ad copy
   - [ ] Add negative keywords
   - [ ] Scale budget if ROI positive

---

## 📞 Support Contacts

- **Render Issues:** https://render.com/support
- **Stripe Issues:** https://support.stripe.com/
- **Google Ads Support:** https://support.google.com/google-ads/
- **GA4 Support:** https://support.google.com/analytics/

---

## 📊 Success Metrics (First 30 Days)

Track these KPIs:

- **Traffic:** 1,000+ visitors
- **CSV Tool Usage:** 200+ previews
- **Conversion Rate:** 2-5% (pricing → checkout)
- **Cost Per Acquisition:** < $150
- **Monthly Recurring Revenue:** $500+
- **Churn:** < 10%

**Update this document after launch with actual metrics!**

