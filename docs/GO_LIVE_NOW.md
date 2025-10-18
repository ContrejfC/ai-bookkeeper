# 🚀 GO LIVE NOW - Production Launch Runbook

**Target:** Paid posting to QuickBooks via ChatGPT GPT  
**Mode:** Stripe LIVE + QBO Production  
**Time to Launch:** ~2 hours

---

## 📋 Pre-Flight Checklist

Before starting, ensure you have:
- [ ] Stripe LIVE account with payment methods test completed
- [ ] QuickBooks Production app approved by Intuit
- [ ] Render account with services deployed
- [ ] Access to ChatGPT Team/Enterprise for custom GPT

---

## 🎯 Phase 1: Deploy to Render (30 minutes)

### A. Deploy Services

**Using Render Blueprint:**
1. Go to Render Dashboard → **New** → **Blueprint**
2. Select repository: `ContrejfC/ai-bookkeeper`
3. **Blueprint file:** `render-split.yaml`
4. Click **Apply Blueprint**

**Manual Service Creation (if blueprint fails):**

#### 1. Create Database
- **New** → **PostgreSQL**
- Name: `ai-bookkeeper-db`
- Database: `ai_bookkeeper`
- Plan: **Starter**
- Region: **Oregon**
- Click **Create Database**

#### 2. Create API Service
- **New** → **Web Service**
- Repository: `ContrejfC/ai-bookkeeper`
- Name: `ai-bookkeeper-api`
- Runtime: **Docker**
- Dockerfile Path: `./Dockerfile.api`
- Branch: `main`
- Plan: **Starter**
- Health Check Path: `/healthz`
- Click **Create Web Service**

#### 3. Create Web Service
- **New** → **Web Service**
- Repository: `ContrejfC/ai-bookkeeper`
- Name: `ai-bookkeeper-web`
- Runtime: **Docker**
- Dockerfile Path: `./Dockerfile.web`
- Branch: `main`
- Plan: **Starter**
- Health Check Path: `/healthz`
- Click **Create Web Service**

### B. Configure Environment Variables

#### API Service Environment Variables

**Core Application:**
```
ENV=production
BASE_URL=https://ai-bookkeeper-api.onrender.com
PUBLIC_BASE_URL=https://ai-bookkeeper.onrender.com
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=https://ai-bookkeeper.onrender.com,https://ai-bookkeeper-web.onrender.com
```

**Secrets (Generate):**
```bash
# Generate locally, then paste in Render:
openssl rand -hex 32  # For JWT_SECRET
openssl rand -hex 32  # For CSRF_SECRET
```

**Database:**
- Link `ai-bookkeeper-db` database
- `DATABASE_URL` auto-populated

**Billing & Limits:**
```
FREE_PROPOSE_CAP_DAILY=50
AUTOPOST=false
ENABLE_LABELS=true
LABEL_SALT_ROUNDS=12
```

**⚠️ Leave blank for now (will set in Phase 2):**
- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_STARTER`
- `STRIPE_PRICE_PRO`
- `STRIPE_PRICE_FIRM`
- `QBO_CLIENT_ID`
- `QBO_CLIENT_SECRET`
- `QBO_BASE`
- `QBO_REDIRECT_URI`

#### Web Service Environment Variables

**⚠️ IMPORTANT:** Mark these as **"Available during build"** in Render:

```
NEXT_PUBLIC_API_URL=https://ai-bookkeeper-api.onrender.com
NEXT_PUBLIC_BASE_URL=https://ai-bookkeeper.onrender.com
```

### C. Verify Initial Deployment

```bash
# Wait for services to show "Live" status, then test:

# API Health
curl https://ai-bookkeeper-api.onrender.com/healthz
# Expected: {"status":"healthy","database":"connected"}

# Web Health
curl https://ai-bookkeeper.onrender.com/healthz
# Expected: {"status":"ok"}
```

---

## 💳 Phase 2: Configure Stripe LIVE (30 minutes)

### A. Create Production Products & Prices

**On your local machine:**
```bash
# Set Stripe LIVE key temporarily
export STRIPE_SECRET_KEY=sk_live_YOUR_KEY_HERE

# Run bootstrap script
python3 scripts/stripe_bootstrap.py

# Copy the output price IDs:
# - STRIPE_PRICE_STARTER=price_xxxxxxxxxxxxx
# - STRIPE_PRICE_PRO=price_xxxxxxxxxxxxx
# - STRIPE_PRICE_FIRM=price_xxxxxxxxxxxxx
```

### B. Create Stripe LIVE Webhook

1. Go to **Stripe Dashboard** → **Developers** → **Webhooks**
2. Click **Add endpoint**
3. **Endpoint URL:** `https://ai-bookkeeper-api.onrender.com/api/billing/stripe_webhook`
4. **Events to listen to:**
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
   - `customer.subscription.trial_will_end`
5. Click **Add endpoint**
6. Copy the **Signing secret** (starts with `whsec_`)

### C. Set Stripe Environment Variables in Render

**In Render Dashboard → API Service → Environment:**

```
STRIPE_SECRET_KEY=sk_live_YOUR_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SIGNING_SECRET
STRIPE_PRICE_STARTER=price_xxxxxxxxxxxxx
STRIPE_PRICE_PRO=price_xxxxxxxxxxxxx
STRIPE_PRICE_FIRM=price_xxxxxxxxxxxxx
```

**Click "Save Changes"** - API service will redeploy automatically.

### D. Verify Stripe Configuration

**After API service redeploys:**
```bash
# SSH into Render API service:
# Render Dashboard → API Service → Shell

# Run verification
python3 scripts/verify_stripe_webhook.py

# Expected: ✅ Stripe LIVE webhook configured
```

---

## 📊 Phase 3: Configure QBO Production (30 minutes)

### A. Create Intuit Production App

1. Go to **Intuit Developer** → **Dashboard**
2. Select your app → **Production** tab
3. Click **Get production keys**
4. Complete **App Assessment** (if not already done)
5. Copy **Client ID** and **Client Secret**

### B. Set QBO Redirect URI

**In Intuit Developer Dashboard:**
- **Redirect URI:** `https://ai-bookkeeper.onrender.com/api/auth/qbo/callback`

### C. Set QBO Environment Variables in Render

**In Render Dashboard → API Service → Environment:**

```
QBO_CLIENT_ID=YOUR_PRODUCTION_CLIENT_ID
QBO_CLIENT_SECRET=YOUR_PRODUCTION_CLIENT_SECRET
QBO_BASE=https://quickbooks.api.intuit.com
QBO_REDIRECT_URI=https://ai-bookkeeper.onrender.com/api/auth/qbo/callback
QBO_SCOPES=com.intuit.quickbooks.accounting
QBO_ENVIRONMENT=production
```

**Click "Save Changes"** - API service will redeploy automatically.

### D. Verify QBO Configuration

**After API service redeploys:**
```bash
# SSH into Render API service:
# Render Dashboard → API Service → Shell

# Run verification
python3 scripts/check_qbo_env.py

# Expected: ✅ QBO configured for production
```

---

## 🧪 Phase 4: Run Production Verification (10 minutes)

### Run Complete Launch Script

**SSH into Render API service shell:**
```bash
# Run the one-command launch script
./ops/launch_live.sh

# This will:
# 1. Verify all environment variables
# 2. Verify QBO production configuration
# 3. Verify Stripe LIVE webhook
# 4. Generate production API key
# 5. Run comprehensive smoke tests
```

**Expected Output:**
```
============================================================================
  ✅ LIVE LAUNCH VERIFICATION COMPLETE
============================================================================

📋 Next Steps:
1. Configure ChatGPT GPT with Actions:
   - OpenAPI URL: https://ai-bookkeeper.onrender.com/openapi.json
   - Auth: API Key (Bearer)
   - Authorization Header: Bearer ak_live_xxxxxxxxxxxxx

2. Follow the GPT publish checklist:
   - See: gpt_config/public_publish_checklist.md
```

**If any step fails:**
- Check error message for specific issue
- Verify environment variables in Render Dashboard
- Check service logs for detailed errors
- See **Troubleshooting** section below

---

## 🤖 Phase 5: Configure ChatGPT GPT (40 minutes)

### Follow the detailed checklist:
📄 **See:** `gpt_config/public_publish_checklist.md`

**Quick summary:**
1. Import OpenAPI from production URL
2. Configure API Key authentication with generated key
3. Paste GPT instructions and conversation starters
4. Set name, description, and icon from listing guide
5. Toggle **Public** and publish
6. Test with 3 validation prompts

---

## ✅ Success Criteria

**All these must be true:**

- [ ] Both services show **"Live"** in Render Dashboard
- [ ] Health checks return 200 OK
- [ ] `ops/launch_live.sh` completes with SUCCESS
- [ ] OpenAPI accessible at `/openapi.json`
- [ ] GPT Actions discovery at `/actions` returns valid JSON
- [ ] Stripe webhook receives test events
- [ ] QBO OAuth flow completes successfully
- [ ] GPT can call all Actions endpoints
- [ ] End-to-end posting workflow works in GPT

---

## 🚨 Troubleshooting

### Issue: API Service Won't Start

**Symptoms:** Service stuck in "Deploying" or crashes immediately

**Check:**
```bash
# View logs in Render Dashboard
# Common issues:
# - DATABASE_URL not set → Link database
# - Missing environment variables → Check all required vars
# - Alembic migration failed → Check database connectivity
```

**Fix:**
- Ensure database is linked to API service
- Verify all environment variables are set
- Check logs for specific error messages

### Issue: Stripe Webhook Verification Fails

**Symptoms:** `verify_stripe_webhook.py` returns error

**Check:**
```bash
# Verify webhook secret format
echo $STRIPE_WEBHOOK_SECRET
# Should start with: whsec_

# Verify webhook endpoint URL matches
curl https://ai-bookkeeper-api.onrender.com/api/billing/stripe_webhook
# Should return: "Method not allowed" (POST only)
```

**Fix:**
- Verify webhook endpoint URL is exactly: `https://ai-bookkeeper-api.onrender.com/api/billing/stripe_webhook`
- Ensure signing secret copied correctly (starts with `whsec_`)
- Test webhook with Stripe Dashboard → Send test event

### Issue: QBO OAuth Fails

**Symptoms:** Redirect loop or "Invalid client" error

**Check:**
```bash
# Verify redirect URI matches exactly
echo $QBO_REDIRECT_URI
# Should be: https://ai-bookkeeper.onrender.com/api/auth/qbo/callback

# Verify production credentials
echo $QBO_BASE
# Should be: https://quickbooks.api.intuit.com (no trailing slash)
```

**Fix:**
- Ensure redirect URI in Intuit Dashboard matches exactly
- Verify production credentials (not sandbox)
- Check `QBO_BASE` has no trailing slash

### Issue: GPT Actions Return 401 Unauthorized

**Symptoms:** GPT shows authentication error

**Check:**
```bash
# Test API key directly
curl -H "Authorization: Bearer ak_live_xxxxx" \
  https://ai-bookkeeper.onrender.com/actions

# Should return: JSON with version, links, etc.
```

**Fix:**
- Verify API key was generated correctly
- Check GPT Actions auth is set to "API Key (Bearer)"
- Ensure authorization header format: `Bearer ak_live_xxxxx` (with space)

---

## 🔄 Rollback Plan

**If critical issues arise during launch:**

### 1. Rollback Services
```bash
# In Render Dashboard:
# - API Service → Deploy → Select previous deployment
# - Web Service → Deploy → Select previous deployment
```

### 2. Revert to TEST/Sandbox Mode
```bash
# In Render Dashboard → API Service → Environment:
# Change these back to TEST/Sandbox values:
STRIPE_SECRET_KEY=sk_test_YOUR_TEST_KEY
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_TEST_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_TEST_SECRET
QBO_BASE=https://sandbox-quickbooks.api.intuit.com
QBO_ENVIRONMENT=sandbox

# Click "Save Changes"
```

### 3. Disable GPT Public Access
```bash
# In ChatGPT GPT Builder:
# - Toggle "Public" to OFF
# - Save changes
```

---

## 📞 Support

**Critical Issues:**
- Check service logs in Render Dashboard
- Review error messages in `ops/launch_live.sh` output
- Verify all environment variables are set correctly
- Ensure health checks pass before running smoke tests

**Documentation:**
- Full deployment guide: `docs/RENDER_DEPLOY_QUICKSTART.md`
- Docker configuration: `status_now/DOCKER_AUDIT.md`
- Render settings: `docs/RENDER_SETTINGS.md`
- OpenAPI versioning: `docs/OPENAPI_VERSIONING.md`

---

**Launch Date:** _______________  
**Launch Engineer:** _______________  
**Status:** ⬜ READY | ⬜ IN PROGRESS | ⬜ COMPLETE
