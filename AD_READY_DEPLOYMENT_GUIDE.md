# Ad-Ready Deployment Guide

This guide walks you through deploying the AI Bookkeeper ad-ready system with complete pricing, billing, and analytics integration.

## 🎯 Overview

The ad-ready system includes:
- **Frontend:** Next.js App with `/gpt-bridge`, `/tools/csv-cleaner`, `/pricing`, and legal pages
- **Backend:** FastAPI with Stripe billing, usage metering, and entitlements
- **Analytics:** GA4 event tracking for Google Ads conversion optimization
- **SEO:** Optimized metadata, sitemap, and robots.txt

---

## 📋 Prerequisites

- [ ] GitHub repository with latest code
- [ ] Render account (or alternative hosting)
- [ ] Stripe account (test mode for development)
- [ ] Google Analytics 4 property
- [ ] Domain name configured (e.g., `ai-bookkeeper.app`)
- [ ] ChatGPT GPT published (optional)

---

## 🚀 Part 1: Stripe Setup

### Step 1: Create Stripe Products

1. **Go to:** https://dashboard.stripe.com/products
2. **Create products:**

#### Starter Plan
- **Name:** Starter
- **Recurring:** Monthly
- **Price:** $49.00 USD
- **Copy Price ID** → `STRIPE_PRICE_STARTER_MONTHLY`

Repeat for:
- Starter Annual ($41/month)
- Team Monthly ($149/month)
- Team Annual ($124/month)
- Firm Monthly ($499/month)
- Firm Annual ($414/month)
- Pilot Monthly ($99/month)

### Step 2: Create Metered Usage Prices

For each plan, create a metered usage price:

1. **Create product:** "Transaction Overage - Starter"
2. **Pricing model:** Per unit
3. **Unit amount:** $0.03
4. **Usage aggregation:** Sum
5. **Billing period:** Monthly
6. **Copy Price ID** → `STRIPE_PRICE_OVERAGE_STARTER`

Repeat for Team ($0.02), Firm ($0.015), Enterprise ($0.01)

### Step 3: Create Add-on Products

Create recurring products for:
- Extra Entity (Starter/Team) - $25/month
- Extra Entity (Firm) - $15/month
- SSO (SAML) - $99/month
- White-label - $149/month
- Extended Retention - $49/month
- Priority Support - $99/month

### Step 4: Configure Webhook

1. **Go to:** https://dashboard.stripe.com/webhooks
2. **Add endpoint:** `https://api.ai-bookkeeper.app/api/billing/webhook`
3. **Select events:**
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
4. **Copy Webhook Secret** → `STRIPE_WEBHOOK_SECRET`

---

## 🌐 Part 2: Frontend Deployment (Render)

### Step 1: Create Web Service

1. **Go to:** https://dashboard.render.com/
2. **New** → **Web Service**
3. **Connect GitHub repository**
4. **Configure:**
   - **Name:** `ai-bookkeeper-web`
   - **Region:** Oregon (US West)
   - **Branch:** `main`
   - **Root Directory:** (leave empty)
   - **Runtime:** Docker
   - **Dockerfile Path:** `Dockerfile.web`
   - **Instance Type:** Starter ($7/month)

### Step 2: Environment Variables

Add these in Render → Environment:

```
NEXT_PUBLIC_API_URL=https://api.ai-bookkeeper.app
NEXT_PUBLIC_BASE_URL=https://app.ai-bookkeeper.app
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
NEXT_PUBLIC_GPT_DEEPLINK=https://chat.openai.com/g/g-XXXXX
NEXT_PUBLIC_DEMO_LOOM_URL=https://www.loom.com/share/XXXXX
```

**Important:** Mark `NEXT_PUBLIC_*` variables as **"Available during build"**

### Step 3: Custom Domain

1. **Render** → `ai-bookkeeper-web` → **Settings** → **Custom Domains**
2. **Add Custom Domain:** `app.ai-bookkeeper.app`
3. **Go to Cloudflare DNS:**
   - **Type:** CNAME
   - **Name:** `app`
   - **Target:** `ai-bookkeeper-web.onrender.com`
   - **Proxy:** Enabled (orange cloud)
4. **Wait 5-30 minutes** for DNS propagation
5. **Return to Render** → Click **"Verify"**

---

## ⚙️ Part 3: Backend Deployment (Render)

### Step 1: Create Web Service

1. **New** → **Web Service**
2. **Connect GitHub repository**
3. **Configure:**
   - **Name:** `ai-bookkeeper-api`
   - **Runtime:** Python 3.11
   - **Build Command:** `pip install -r requirements.txt && alembic upgrade head`
   - **Start Command:** `uvicorn app.api.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Standard ($25/month recommended)

### Step 2: Environment Variables

Add all variables from `env.example`:

**Critical Variables:**
```
DATABASE_URL=postgresql://user:pass@host/db
STRIPE_SECRET_KEY=sk_live_XXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXX
ALLOWED_ORIGINS=https://app.ai-bookkeeper.app,https://ai-bookkeeper-web.onrender.com
SECRET_KEY=generate-secure-random-key
OPENAI_API_KEY=sk-XXXXX
```

**Stripe Price IDs:** (from Part 1)
```
STRIPE_PRICE_STARTER_MONTHLY=price_XXXXX
STRIPE_PRICE_TEAM_MONTHLY=price_XXXXX
... (all price IDs)
```

### Step 3: Database

**Option A: Render PostgreSQL (Recommended)**
1. **New** → **PostgreSQL**
2. **Name:** `ai-bookkeeper-db`
3. **Copy Internal Database URL**
4. **Add to backend env:** `DATABASE_URL=postgresql://...`

**Option B: External PostgreSQL**
- Use your existing PostgreSQL instance
- Set `DATABASE_URL` accordingly

### Step 4: Custom Domain

1. **Render** → `ai-bookkeeper-api` → **Settings** → **Custom Domains**
2. **Add Custom Domain:** `api.ai-bookkeeper.app`
3. **Cloudflare DNS:**
   - **Type:** CNAME
   - **Name:** `api`
   - **Target:** `ai-bookkeeper-api.onrender.com`
   - **Proxy:** Enabled
4. **Verify in Render**

---

## 📊 Part 4: Google Analytics Setup

### Step 1: Create GA4 Property

1. **Go to:** https://analytics.google.com/
2. **Admin** → **Create Property**
3. **Property Name:** AI Bookkeeper
4. **Set timezone and currency**
5. **Create Data Stream** → Web
6. **Website URL:** `https://app.ai-bookkeeper.app`
7. **Copy Measurement ID** (G-XXXXXXXXXX)

### Step 2: Configure Events

Events are automatically tracked by the frontend. Verify in GA4:

**Realtime** → **Events** → Should see:
- `page_view`
- `bridge_viewed`
- `tool_opened`
- `rows_previewed`
- `checkout_clicked`

### Step 3: Link to Google Ads (When Ready)

1. **GA4 Admin** → **Google Ads Links**
2. **Link your Google Ads account**
3. **Import conversions:**
   - `purchase` (value = first month fee)
   - `subscription_started`

---

## 🧪 Part 5: Testing

### Test Checklist

- [ ] **Frontend loads:** `https://app.ai-bookkeeper.app`
- [ ] **API responds:** `https://api.ai-bookkeeper.app/healthz`
- [ ] **GPT Bridge page:** Load and click "Open in ChatGPT"
- [ ] **CSV Cleaner:** Upload CSV, see preview
- [ ] **Pricing page:** All plans display correctly
- [ ] **Checkout flow:**
  - [ ] Click "Start Starter"
  - [ ] Redirects to Stripe Checkout
  - [ ] Use test card: `4242 4242 4242 4242`
  - [ ] Redirects to `/success`
  - [ ] Subscription appears in Stripe Dashboard
- [ ] **GA4 events:**
  - [ ] Open GA4 Realtime
  - [ ] Navigate pages
  - [ ] Verify events fire
- [ ] **Legal pages:** `/privacy`, `/terms`, `/dpa`, `/security` load
- [ ] **SEO:** View page source, check meta tags
- [ ] **Sitemap:** `https://app.ai-bookkeeper.app/sitemap.xml`
- [ ] **Robots.txt:** `https://app.ai-bookkeeper.app/robots.txt`

### Performance Testing

Run Lighthouse audit (Chrome DevTools):
- **Target:** LCP < 2.5s on `/gpt-bridge` and `/tools/csv-cleaner`
- **Target:** CLS < 0.1
- **Target:** INP < 200ms

---

## 🔧 Part 6: Cron Jobs (Monthly Billing)

### Option 1: Render Cron Jobs (Recommended)

1. **Create:** `scripts/bill_monthly_overage.py`
```python
#!/usr/bin/env python3
from app.db.session import get_db_context
from app.services.usage_metering import UsageMeteringService

def main():
    with get_db_context() as db:
        service = UsageMeteringService(db)
        results = service.run_monthly_billing_job()
        print(f"✅ Billed {results['success']} subscriptions")
        print(f"💰 Total: ${results['total_billed']}")
        
if __name__ == "__main__":
    main()
```

2. **Create:** `scripts/reset_monthly_usage.py`
```python
#!/usr/bin/env python3
from app.db.session import get_db_context
from app.services.usage_metering import UsageMeteringService

def main():
    with get_db_context() as db:
        service = UsageMeteringService(db)
        results = service.run_monthly_reset_job()
        print(f"✅ Reset {results['total']} subscriptions")
        
if __name__ == "__main__":
    main()
```

3. **Render Dashboard:**
   - **New** → **Cron Job**
   - **Name:** `monthly-billing`
   - **Command:** `python scripts/bill_monthly_overage.py`
   - **Schedule:** `59 23 28-31 * *` (Last day of month, 11:59 PM UTC)
   
   - **New** → **Cron Job**
   - **Name:** `monthly-reset`
   - **Command:** `python scripts/reset_monthly_usage.py`
   - **Schedule:** `1 0 1 * *` (First day of month, 12:01 AM UTC)

### Option 2: External Cron (cron-job.org)

Use external service like cron-job.org to hit webhook endpoints.

---

## 🎯 Part 7: Google Ads Setup

### Prerequisites
- [ ] Billing active in Google Ads
- [ ] GA4 linked to Google Ads
- [ ] Conversion tracking verified

### Create Campaign

1. **Campaign Type:** Search
2. **Goal:** Conversions
3. **Budget:** Start with $50-100/day
4. **Bidding:** Maximize conversions

### Keywords

Target high-intent keywords:
- `ai bookkeeping software`
- `automated bookkeeping`
- `bookkeeping automation`
- `quickbooks ai`
- `accounting automation`

### Ad Copy Examples

**Headline 1:** AI Bookkeeping from $49/mo
**Headline 2:** Automate Journal Entries
**Headline 3:** QuickBooks & Xero Ready

**Description:** Upload bank statements and get AI-powered categorization. Try our free CSV cleaner. Plans start at $49/month.

**Final URL:** `https://app.ai-bookkeeper.app/pricing`

### Tracking

Set up conversion tracking for:
- `purchase` event (Primary conversion, value-based)
- `subscription_started` event (Secondary)
- `tool_opened` event (Micro-conversion)

---

## 📈 Part 8: Monitoring

### Application Monitoring

**Check daily:**
- Render service health
- Error logs in Render dashboard
- Database size (upgrade if needed)
- API response times

### Business Metrics

**Track in Stripe:**
- MRR (Monthly Recurring Revenue)
- Churn rate
- Overage charges
- Average transaction count per customer

**Track in GA4:**
- Conversion rate (pricing page → checkout)
- CSV tool usage
- GPT bridge clicks
- Session duration

---

## 🚨 Troubleshooting

### Frontend Issues

**Problem:** Page won't load
- Check Render logs
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check DNS propagation: `nslookup app.ai-bookkeeper.app`

**Problem:** API calls failing (CORS errors)
- Verify `ALLOWED_ORIGINS` includes frontend URL
- Check browser console for specific error

### Backend Issues

**Problem:** Stripe checkout fails
- Verify `STRIPE_SECRET_KEY` is set
- Check Stripe Dashboard → Logs
- Verify price IDs are correct

**Problem:** Usage not incrementing
- Check `UsageMeteringService` logs
- Verify database writes
- Check `BillingSubscriptionDB.metadata`

### Billing Issues

**Problem:** Overage not charged
- Check cron job ran: Render → Cron Jobs → Logs
- Verify Stripe usage records: Stripe → Usage
- Check `BillingEventDB` table

---

## ✅ Launch Checklist

Before going live with Google Ads:

- [ ] Switch Stripe to live mode (`sk_live_`)
- [ ] Update all `STRIPE_PRICE_*` to live price IDs
- [ ] Update `STRIPE_WEBHOOK_SECRET` to live webhook
- [ ] Verify SSL certificates on both domains
- [ ] Test full checkout flow with real card
- [ ] Confirm GA4 events firing correctly
- [ ] Set up billing alerts in Stripe
- [ ] Create support@ai-bookkeeper.app email
- [ ] Document internal processes
- [ ] Set up status page (optional)
- [ ] Configure backup strategy

---

## 📞 Support

For deployment issues:
- **Render Support:** https://render.com/docs
- **Stripe Support:** https://support.stripe.com/
- **GA4 Help:** https://support.google.com/analytics/

---

## 🎉 You're Ready!

Your AI Bookkeeper is now ad-ready with:
- ✅ Complete billing integration
- ✅ Usage-based metering
- ✅ Conversion tracking
- ✅ Professional landing pages
- ✅ Free CSV tool for lead generation
- ✅ SEO optimization

**Next Steps:**
1. Create your first Google Ads campaign
2. Monitor conversion rates
3. Iterate on ad copy based on data
4. Scale budget as ROI improves

Good luck! 🚀

