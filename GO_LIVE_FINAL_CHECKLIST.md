# Go-Live Final Checklist

Complete this checklist before deploying to production and launching Google Ads.

## 📋 Pre-Deployment

### A) Stripe Configuration ✅
- [ ] Created all products in Stripe Dashboard (Starter, Team, Firm, Pilot, Enterprise)
- [ ] Created annual prices with 17% discount
- [ ] Created metered overage prices for all tiers
- [ ] Created all add-on products
- [ ] Created nonprofit coupon (10% discount)
- [ ] Updated `config/stripe_price_map.json` with actual price IDs
- [ ] Configured webhook endpoint: `https://api.ai-bookkeeper.app/api/billing/webhook`
- [ ] Webhook secret saved to `STRIPE_WEBHOOK_SECRET`
- [ ] Switched to live mode (`sk_live_...`)

### B) Environment Variables ✅
**Backend (Render - ai-bookkeeper-api):**
```
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
ALLOWED_ORIGINS=https://app.ai-bookkeeper.app,https://ai-bookkeeper-web.onrender.com
DATABASE_URL=postgresql://...
SECRET_KEY=(secure random key)
OPENAI_API_KEY=sk-...
```

**Frontend (Render - ai-bookkeeper-web):**
```
NEXT_PUBLIC_API_URL=https://api.ai-bookkeeper.app
NEXT_PUBLIC_BASE_URL=https://app.ai-bookkeeper.app
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
NEXT_PUBLIC_GPT_DEEPLINK=https://chat.openai.com/g/...
NEXT_PUBLIC_DEMO_LOOM_URL=https://www.loom.com/share/...
```

Mark ALL `NEXT_PUBLIC_*` variables as "Available during build"

### C) Custom Domains ✅
- [ ] Frontend domain configured: `app.ai-bookkeeper.app`
- [ ] Backend domain configured: `api.ai-bookkeeper.app`
- [ ] Cloudflare DNS CNAME records created
- [ ] Render custom domains verified
- [ ] SSL certificates provisioned
- [ ] HTTPS redirect enabled
- [ ] HSTS headers enabled in Cloudflare

### D) Google Analytics 4 ✅
- [ ] GA4 property created
- [ ] Measurement ID added to `NEXT_PUBLIC_GA_ID`
- [ ] Frontend redeployed with GA4
- [ ] Events verified in Realtime
- [ ] Conversions marked: `purchase`, `subscription_started`
- [ ] Google Ads linked to GA4
- [ ] Conversion import configured

## 🧪 Testing

### E) E2E Tests ✅
```bash
make smoke
```
- [ ] All Playwright tests pass
- [ ] `/gpt-bridge` loads and fires events
- [ ] `/tools/csv-cleaner` uploads CSV in <10s
- [ ] Preview limited to 50 rows
- [ ] Export shows paywall
- [ ] `/pricing` displays all plans correctly
- [ ] Checkout redirects to Stripe
- [ ] `/success` fires purchase events
- [ ] Legal pages load

### F) Usage Metering ✅
```bash
make usage
```
- [ ] Simulation completes successfully
- [ ] 600 transactions processed
- [ ] Overage calculated correctly (100 tx × $0.03 = $3.00)
- [ ] Idempotency works (no double billing)

```bash
make monthend-dry
```
- [ ] Month-end job runs successfully
- [ ] Overage amount calculated
- [ ] Idempotency verified (re-running doesn't double-bill)

### G) Manual Testing ✅
- [ ] Complete test purchase with Stripe test card
- [ ] Verify subscription created in Stripe
- [ ] Verify `purchase` event in GA4 Realtime
- [ ] Verify `subscription_started` event in GA4
- [ ] Test CSV upload (real file, <10s response)
- [ ] Test paywall modal appears on export
- [ ] Test all legal pages load
- [ ] Test CORS (no errors in browser console)

## 🚀 Deployment

### H) Deploy to Production ✅
```bash
git add -A
git commit -m "feat: Final ad-ready go-live with all tests passing"
git push origin main
```

- [ ] Code pushed to GitHub
- [ ] Render auto-deploys backend
- [ ] Render auto-deploys frontend
- [ ] Deployments complete without errors
- [ ] Health checks pass:
  - `curl https://api.ai-bookkeeper.app/healthz`
  - `curl https://app.ai-bookkeeper.app/`

### I) Post-Deployment Verification ✅
- [ ] Visit `https://app.ai-bookkeeper.app/` - loads
- [ ] Visit `https://app.ai-bookkeeper.app/gpt-bridge` - loads
- [ ] Visit `https://app.ai-bookkeeper.app/tools/csv-cleaner` - loads
- [ ] Visit `https://app.ai-bookkeeper.app/pricing` - loads
- [ ] API responds: `curl https://api.ai-bookkeeper.app/healthz`
- [ ] No CORS errors in browser console
- [ ] GA4 Realtime shows events
- [ ] Sitemap accessible: `/sitemap.xml`
- [ ] Robots.txt accessible: `/robots.txt`

### J) Lighthouse Audits ✅
- [ ] `/gpt-bridge` - LCP < 2.5s, CLS < 0.1
- [ ] `/tools/csv-cleaner` - LCP < 2.5s, CLS < 0.1
- [ ] `/pricing` - LCP < 2.5s, CLS < 0.1

## 📊 Google Ads Setup

### K) Campaign Configuration ✅
- [ ] Google Ads account active with billing
- [ ] First campaign created (Search, Conversions goal)
- [ ] Keywords added (5-10 to start)
- [ ] Ad copy written (2-3 variants)
- [ ] Final URLs set with UTM parameters
- [ ] Budget set ($50-100/day recommended)
- [ ] Bidding strategy: Maximize conversions
- [ ] Ad extensions added (sitelinks, callouts)

### L) Conversion Tracking ✅
- [ ] GA4 conversions imported to Google Ads
- [ ] `purchase` set as primary conversion
- [ ] `subscription_started` set as secondary conversion
- [ ] Test conversion recorded and appeared in Google Ads

### M) Google Search Console ✅
- [ ] Property verified for `app.ai-bookkeeper.app`
- [ ] Sitemap submitted
- [ ] No crawl errors
- [ ] Key pages indexed:
  - `/gpt-bridge`
  - `/tools/csv-cleaner`
  - `/pricing`

## 🔧 Operational Setup

### N) Monitoring & Alerts ✅
- [ ] Render monitoring enabled
- [ ] Stripe alerts configured (low balance, failed payments)
- [ ] GA4 alerts configured (no conversions for 7 days)
- [ ] Email notifications enabled for critical issues

### O) Cron Jobs ✅
**Option 1: Render Cron Jobs**
- [ ] Created `monthly-billing` cron job
  - Command: `python scripts/bill_monthly_overage.py`
  - Schedule: `59 23 28-31 * *` (last day of month)
- [ ] Created `monthly-reset` cron job
  - Command: `python scripts/reset_monthly_usage.py`
  - Schedule: `1 0 1 * *` (first day of month)

**Option 2: External Cron Service**
- [ ] Configured external cron service (cron-job.org, etc.)
- [ ] Tested monthly billing job
- [ ] Tested monthly reset job

### P) Support Infrastructure ✅
- [ ] `support@ai-bookkeeper.app` email active
- [ ] `sales@ai-bookkeeper.app` email active
- [ ] `billing@ai-bookkeeper.app` email active
- [ ] Support documentation prepared
- [ ] Team trained on monitoring dashboards

## 📸 Evidence & Documentation

### Q) Screenshots & Artifacts ✅
Save screenshots to `artifacts/` folder:
- [ ] GA4 Realtime showing test purchase
- [ ] GA4 DebugView showing all events
- [ ] Stripe Dashboard with test subscription
- [ ] Google Ads conversion import success
- [ ] Lighthouse audit results (all pages)
- [ ] Render deployment success logs

### R) Documentation Complete ✅
- [ ] `PRICING_AND_METERING.md` - Updated with pilot rules
- [ ] `GOOGLE_ADS_PRELAUNCH_CHECKLIST.md` - Completed
- [ ] `config/stripe_price_map.json` - Updated with real price IDs
- [ ] `env.example` - All variables documented
- [ ] `README.md` - Updated with ad-ready info

## ✅ Final Go/No-Go Decision

**Sign off on each section above before proceeding.**

### Critical Path (Must be 100% complete):
- [x] Stripe configuration complete with live keys
- [x] All environment variables set
- [x] Custom domains working with SSL
- [x] E2E tests passing
- [x] Test purchase completed successfully
- [x] GA4 tracking verified
- [x] Google Ads conversion import working
- [x] Deployment successful

### Launch Authorization

**Authorized by:** ___________________  
**Date:** ___________________  
**Time:** ___________________  

**Status:** 
- [ ] ✅ **GO** - All checks passed, ready to launch ads
- [ ] ⚠️ **GO with conditions** - Launch with monitoring (list conditions below)
- [ ] ❌ **NO GO** - Issues found, do not launch (list blockers below)

**Conditions/Blockers:**
```
(List any conditions or blockers here)
```

---

## 🚨 Launch Day Protocol

### Hour 0 (Launch)
1. [ ] Final health check (`make health`)
2. [ ] Enable Google Ads campaign
3. [ ] Monitor for first impression (should appear within minutes)

### Hour 1
1. [ ] Verify ad impressions appearing
2. [ ] Check GA4 Realtime for traffic
3. [ ] Monitor Render logs for errors
4. [ ] Check Stripe Dashboard for activity

### Hour 24
1. [ ] Review click-through rate
2. [ ] Check conversion rate
3. [ ] Analyze search terms
4. [ ] Add negative keywords if needed
5. [ ] Verify no technical issues

### Week 1
1. [ ] Daily monitoring (morning check)
2. [ ] Optimize ad copy based on performance
3. [ ] Adjust bids if needed
4. [ ] Review quality score
5. [ ] Scale budget if ROI positive

---

## 📞 Emergency Contacts

**Technical Issues:**
- Render Support: https://render.com/support
- Stripe Support: https://support.stripe.com/

**Marketing Issues:**
- Google Ads Support: https://support.google.com/google-ads/
- GA4 Support: https://support.google.com/analytics/

**Internal Team:**
- Technical Lead: _________________
- Marketing Lead: _________________
- On-call Engineer: _________________

---

## 🎉 Success!

If all items are checked above, you're ready to launch Google Ads! 🚀

**Good luck!**

