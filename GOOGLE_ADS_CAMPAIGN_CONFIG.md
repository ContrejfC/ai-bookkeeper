# Google Ads Campaign Configuration

Campaign settings and assets ready for launch once all 8 validation criteria pass.

---

## 🎯 Campaign Overview

**Campaign Name:** AI Bookkeeper - Core Intent - Search

**Objective:** Drive subscriptions via high-intent bookkeeping automation searches

**Budget:** $40/day ($1,200/month)

**Bidding:** Maximize conversions (switch to Target CPA after 30 conversions)

---

## 🔑 Keywords (Exact Match)

Target high-intent, low-competition keywords:

| Keyword | Match Type | Max CPC |
|---------|------------|---------|
| `[quickbooks auto categorize]` | Exact | $8.00 |
| `[ai bookkeeping quickbooks]` | Exact | $8.00 |
| `[bank csv to qbo]` | Exact | $8.00 |
| `[post journal entries quickbooks]` | Exact | $8.00 |
| `[xero auto categorize]` | Exact | $8.00 |

**Keyword Strategy:**
- Start with exact match only (higher intent, lower waste)
- Pause any keyword with CPC > $8 and 0 conversions after 50 clicks
- Add phrase match after 2 weeks if exact match performs well
- Monitor Search Terms report daily for first week

---

## 📝 Responsive Search Ads (RSA)

### Ad Group 1: QuickBooks Automation

**Headlines (15 max, provide 5-10):**
1. QuickBooks Auto-Categorize
2. Clean Bank CSV → QBO
3. Preview 50 Rows Free
4. Export to QBO in Minutes
5. Explainable Rules + Rollback
6. AI Bookkeeping from $49/mo
7. Save Hours Every Month
8. Try Free CSV Cleaner
9. Automate Journal Entries
10. QuickBooks Ready in Seconds

**Descriptions (4 max, provide 2-3):**
1. Upload a bank CSV, preview 50 rows free, then export or post to QuickBooks/Xero.
2. Starter $49/mo. Metered overage. Pilot $99/mo for 3 months.
3. AI-powered transaction categorization for QuickBooks & Xero. Try our free CSV tool now.

**Final URL:**
```
https://app.ai-bookkeeper.app/gpt-bridge?utm_source=google&utm_medium=search&utm_campaign=core_intent&utm_term={keyword}
```

**Display Path:**
- Path 1: `Free-Tool`
- Path 2: `CSV-Cleaner`

---

## 🔗 Ad Extensions

### Sitelinks (4 recommended)

1. **Free CSV Cleaner**
   - Description: Try our tool - no account needed
   - URL: `https://app.ai-bookkeeper.app/tools/csv-cleaner?utm_source=google&utm_medium=search&utm_campaign=core_intent&utm_content=sitelink_tool`

2. **View Pricing**
   - Description: Plans start at $49/month
   - URL: `https://app.ai-bookkeeper.app/pricing?utm_source=google&utm_medium=search&utm_campaign=core_intent&utm_content=sitelink_pricing`

3. **ChatGPT Integration**
   - Description: Use AI Bookkeeper in ChatGPT
   - URL: `https://app.ai-bookkeeper.app/gpt-bridge?utm_source=google&utm_medium=search&utm_campaign=core_intent&utm_content=sitelink_gpt`

4. **Security & Compliance**
   - Description: SOC 2 certified, bank-level encryption
   - URL: `https://app.ai-bookkeeper.app/security?utm_source=google&utm_medium=search&utm_campaign=core_intent&utm_content=sitelink_security`

### Callouts (6-10 recommended)

1. Free CSV Cleaner Tool
2. SOC 2 Type II Compliant
3. 500 Transactions Included
4. QuickBooks & Xero Ready
5. Pilot: $99 for 3 Months
6. No Long-term Contracts
7. Email Support Included
8. Preview 50 Rows Free
9. Cancel Anytime
10. 99.5% SLA on Firm Plan

### Structured Snippets

**Service Catalog:**
- Transaction Categorization
- Journal Entry Generation
- QuickBooks Integration
- Xero Integration
- Receipt OCR
- Audit Exports

**Plans:**
- Starter: $49/mo
- Team: $149/mo
- Firm: $499/mo
- Enterprise: Custom

---

## 🎯 Conversion Tracking

### Primary Conversion
- **Event:** `purchase`
- **Value:** Dynamic (first month fee: $49, $149, $499, or $99)
- **Action:** Count as conversion, include in "Conversions" column
- **Goal:** Primary optimization target

### Secondary Conversion
- **Event:** `subscription_started`
- **Value:** Dynamic (same as purchase)
- **Action:** Track separately, verify consistency with `purchase`

### Micro-Conversion (Observation)
- **Event:** `export_paywalled`
- **Value:** None
- **Action:** Track as observation, measure funnel drop-off
- **Use:** Optimize for users who hit paywall but don't convert

---

## 📊 Campaign Settings (Detailed)

### General Settings
- **Campaign Type:** Search
- **Goal:** Conversions
- **Network:** Google Search only (disable Search Partners initially)
- **Locations:** United States (or your target market)
- **Languages:** English
- **Start Date:** (Set when ready)
- **End Date:** None (ongoing)

### Bidding & Budget
- **Bid Strategy:** Maximize conversions
- **Budget:** $40/day ($1,200/month)
- **Delivery Method:** Standard

### Ad Schedule
- **All days:** 24/7 (monitor and adjust based on data)
- **Bid Adjustments:** None initially (add after data collection)

### Audience Segments (Observation Only)
- In-Market: Business Services
- In-Market: Accounting & Tax Services
- Affinity: Business Professionals

### Negative Keywords (Add immediately)
```
free quickbooks
quickbooks free trial
quickbooks download
quickbooks login
quickbooks support
quickbooks alternative
quickbooks vs
jobs
careers
training
course
tutorial
```

---

## 📈 Performance Targets

### Week 1 Targets
- **Impressions:** 500-1,000
- **Clicks:** 20-50 (CTR: 4-5%)
- **Conversions:** 1-3 (Conv Rate: 5-6%)
- **CPC:** $3-$8
- **CPA:** $50-$150
- **Quality Score:** 7-10

### Week 2-4 Optimization
- **Add phrase match** keywords if exact match saturates
- **Adjust bids** based on keyword performance
- **A/B test ad copy** (create 2-3 variants)
- **Add negative keywords** from Search Terms report
- **Optimize for CPA** once you have 30+ conversions

### Month 1 Goals
- **Conversions:** 10-20 paid signups
- **MRR:** $500-$1,500
- **CPA:** < $150
- **ROAS:** Break-even to 2x (LTV = 6 months = $294 for Starter)
- **Quality Score:** 8-10 average

---

## 🚨 Pause Conditions

**Immediately pause if:**
- CPC > $8 for any keyword after 50 clicks
- 0 conversions after $200 spend on a keyword
- Quality Score < 5 (check landing page relevance)
- Site goes down (set up uptime monitoring)

**Review and optimize if:**
- CTR < 2% (ad copy issue)
- Conv Rate < 2% (landing page issue)
- CPA > $200 (bid too high or poor targeting)

---

## 📋 Launch Day Protocol

### Pre-Launch (1 hour before)
- [ ] Run: `python scripts/validate_prelaunch.py`
- [ ] All 8 tests pass
- [ ] Complete `GO_LIVE_FINAL_CHECKLIST.md`
- [ ] Verify GA4 Realtime working
- [ ] Verify Stripe webhook active
- [ ] Check Render services healthy

### Launch (Hour 0)
- [ ] Enable Google Ads campaign
- [ ] Set status to "Eligible"
- [ ] Verify first impression appears within 30 minutes
- [ ] Open GA4 Realtime view
- [ ] Open Render logs (both services)
- [ ] Open Stripe Dashboard

### Post-Launch (Hour 1)
- [ ] Verify impressions appearing
- [ ] Check first click (if any)
- [ ] Monitor for CORS errors in browser console
- [ ] Verify no 500 errors in Render logs
- [ ] Check quality score (should be 5-7 initially)

### Day 1 Review (EOD)
- [ ] Total impressions: _____
- [ ] Total clicks: _____
- [ ] CTR: _____%
- [ ] Conversions: _____
- [ ] CPC: $_____
- [ ] Any issues: _____

### Week 1 Review
- [ ] Pause underperforming keywords (CPC > $8, 0 conv after 50 clicks)
- [ ] Add negative keywords from Search Terms
- [ ] Review ad copy performance
- [ ] Check conversion rate by keyword
- [ ] Adjust budget if needed

---

## 🎓 Campaign Import (JSON Format)

For bulk import into Google Ads Editor:

```json
{
  "campaign": {
    "name": "AI Bookkeeper - Core Intent - Search",
    "type": "SEARCH",
    "budget": 40,
    "budget_type": "DAILY",
    "bidding_strategy": "MAXIMIZE_CONVERSIONS",
    "network_settings": {
      "target_google_search": true,
      "target_search_network": false,
      "target_content_network": false
    }
  },
  "ad_groups": [
    {
      "name": "QuickBooks Automation",
      "keywords": [
        {"text": "quickbooks auto categorize", "match_type": "EXACT"},
        {"text": "ai bookkeeping quickbooks", "match_type": "EXACT"},
        {"text": "bank csv to qbo", "match_type": "EXACT"},
        {"text": "post journal entries quickbooks", "match_type": "EXACT"},
        {"text": "xero auto categorize", "match_type": "EXACT"}
      ]
    }
  ],
  "conversions": [
    {
      "name": "purchase",
      "action": "PRIMARY",
      "value": "DYNAMIC"
    },
    {
      "name": "export_paywalled",
      "action": "SECONDARY",
      "value": "NONE"
    }
  ]
}
```

---

## 📞 Monitoring Checklist

### Daily (First Week)
- [ ] Check Google Ads performance (morning)
- [ ] Review GA4 Realtime (spot check)
- [ ] Check Render logs for errors
- [ ] Monitor Stripe Dashboard for new subscriptions
- [ ] Review Search Terms report
- [ ] Add negative keywords as needed

### Weekly (First Month)
- [ ] Performance review (every Monday)
- [ ] Budget optimization
- [ ] Ad copy testing
- [ ] Keyword expansion (if budget allows)
- [ ] Conversion rate optimization

---

## ✅ Ready to Launch

**Once all 8 validation criteria pass:**

1. Create campaign in Google Ads with settings above
2. Add keywords (exact match only)
3. Create 2-3 RSA variants
4. Add extensions (sitelinks, callouts, structured snippets)
5. Set budget to $40/day
6. Enable campaign
7. Monitor first hour closely

**Good luck! 🚀**

