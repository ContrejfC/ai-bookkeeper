# Split Services Deployment Guide
## AI Bookkeeper - Production Architecture

**Date**: October 19, 2025  
**Architecture**: API (FastAPI) + Web (Next.js) - Separate Services  
**Status**: ✅ **READY TO DEPLOY**

---

## 🎯 Overview

This guide walks you through deploying AI Bookkeeper using **two separate Render services**:

1. **`ai-bookkeeper-api`** - FastAPI backend (Python)
2. **`ai-bookkeeper-web`** - Next.js frontend (Node.js)

**Why this approach**:
- ✅ Industry standard (like Stripe, GitHub, Slack)
- ✅ Clean separation of concerns
- ✅ Independent scaling
- ✅ Easier debugging
- ✅ Reliable deployment
- ✅ Won't break again

---

## 📋 Prerequisites

Before starting, ensure you have:
- ✅ Render account (free tier works)
- ✅ Custom domain: `api.ai-bookkeeper.app` (for API)
- ✅ Custom domain: `app.ai-bookkeeper.app` (for Web) - **NEW, configure DNS**
- ✅ External PostgreSQL (Neon.tech) OR will create on Render
- ✅ Stripe account (for billing)
- ✅ QuickBooks developer account (for QBO integration)

---

## 🚀 Deployment Steps

### **OPTION A: Deploy via Render Blueprint** ⭐ **EASIEST**

#### Step 1: Apply Blueprint

1. Go to: https://dashboard.render.com/blueprints
2. Click: **New Blueprint Instance**
3. Connect your GitHub repository: `ContrejfC/ai-bookkeeper`
4. **IMPORTANT**: Select blueprint file: `render-split.yaml`
5. Click: **Apply**

Render will create:
- `ai-bookkeeper-api` (Web Service)
- `ai-bookkeeper-web` (Web Service)
- `ai-bookkeeper-db` (PostgreSQL Database)

#### Step 2: Configure Secrets

After services are created, add secrets to **`ai-bookkeeper-api`**:

1. Go to: Dashboard → **ai-bookkeeper-api** → **Environment**
2. Add these secrets:

```bash
# Security (generate with: openssl rand -hex 32)
JWT_SECRET=<generate_32_char_hex>
CSRF_SECRET=<generate_32_char_hex>

# Stripe (from Stripe Dashboard)
STRIPE_SECRET_KEY=sk_live_YOUR_KEY
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET
STRIPE_PRICE_STARTER=price_YOUR_STARTER
STRIPE_PRICE_PRO=price_YOUR_PRO
STRIPE_PRICE_FIRM=price_YOUR_FIRM

# QuickBooks (from Intuit Developer)
QBO_CLIENT_ID=YOUR_CLIENT_ID
QBO_CLIENT_SECRET=YOUR_CLIENT_SECRET

# Optional: Monitoring
SENTRY_DSN=YOUR_SENTRY_DSN
```

3. Click: **Save Changes** (will trigger redeploy)

#### Step 3: Mark Build-Time Variables

For **`ai-bookkeeper-web`** service:

1. Go to: Dashboard → **ai-bookkeeper-web** → **Environment**
2. Find: `NEXT_PUBLIC_API_URL`
3. Click the ⚙️ icon next to it
4. Check: ☑️ **"Available during build"**
5. Find: `NEXT_PUBLIC_BASE_URL`
6. Click the ⚙️ icon next to it
7. Check: ☑️ **"Available during build"**
8. Click: **Save Changes**

---

### **OPTION B: Manual Service Creation** (If Blueprint Fails)

<details>
<summary>Click to expand manual steps</summary>

#### Step 1: Create PostgreSQL Database

1. Go to: Dashboard → **New** → **PostgreSQL**
2. Name: `ai-bookkeeper-db`
3. Database Name: `ai_bookkeeper`
4. Region: `Oregon`
5. Plan: `Starter` (or `Free` for testing)
6. Click: **Create Database**
7. **Copy the External Database URL** (starts with `postgresql://`)

#### Step 2: Create API Service

1. Go to: Dashboard → **New** → **Web Service**
2. Connect Repository: `ContrejfC/ai-bookkeeper`
3. Configure:
   - **Name**: `ai-bookkeeper-api`
   - **Region**: Oregon
   - **Branch**: main
   - **Runtime**: Docker
   - **Dockerfile Path**: `./Dockerfile.api`
   - **Plan**: Starter

4. **Environment Variables**:

```bash
# Core
ENV=production
BASE_URL=https://api.ai-bookkeeper.app
PUBLIC_BASE_URL=https://api.ai-bookkeeper.app
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=https://app.ai-bookkeeper.app,https://ai-bookkeeper.app

# Database (paste from Step 1)
DATABASE_URL=postgresql://...
PGSSLMODE=require

# Security (generate with: openssl rand -hex 32)
JWT_SECRET=<your_secret_here>
CSRF_SECRET=<your_secret_here>

# Stripe
STRIPE_SECRET_KEY=sk_live_YOUR_KEY
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET
STRIPE_PRICE_STARTER=price_YOUR_STARTER
STRIPE_PRICE_PRO=price_YOUR_PRO
STRIPE_PRICE_FIRM=price_YOUR_FIRM

# QuickBooks
QBO_CLIENT_ID=YOUR_CLIENT_ID
QBO_CLIENT_SECRET=YOUR_CLIENT_SECRET
QBO_REDIRECT_URI=https://api.ai-bookkeeper.app/api/auth/qbo/callback
QBO_SCOPES=com.intuit.quickbooks.accounting
QBO_BASE=https://sandbox-quickbooks.api.intuit.com
QBO_ENVIRONMENT=sandbox

# Limits
FREE_PROPOSE_CAP_DAILY=50
AUTOPOST=false

# Privacy
ENABLE_LABELS=true
LABEL_SALT_ROUNDS=12
```

5. **Health Check Path**: `/healthz`
6. Click: **Create Web Service**

#### Step 3: Create Web Service

1. Go to: Dashboard → **New** → **Web Service**
2. Connect Repository: `ContrejfC/ai-bookkeeper`
3. Configure:
   - **Name**: `ai-bookkeeper-web`
   - **Region**: Oregon
   - **Branch**: main
   - **Runtime**: Docker
   - **Dockerfile Path**: `./Dockerfile.web`
   - **Plan**: Starter

4. **Environment Variables**:

```bash
# ⚠️ IMPORTANT: Mark BOTH as "Available during build" after creation

NEXT_PUBLIC_API_URL=https://api.ai-bookkeeper.app
NEXT_PUBLIC_BASE_URL=https://app.ai-bookkeeper.app
```

5. Click: **Create Web Service**

6. **AFTER creation**:
   - Go to: Environment tab
   - For `NEXT_PUBLIC_API_URL`: Click ⚙️ → Check "Available during build"
   - For `NEXT_PUBLIC_BASE_URL`: Click ⚙️ → Check "Available during build"
   - Click: **Save Changes** (triggers rebuild)

</details>

---

## 🌐 Custom Domain Configuration

### **For API Service** (`api.ai-bookkeeper.app`)

1. Go to: Dashboard → **ai-bookkeeper-api** → **Settings** → **Custom Domains**
2. Click: **Add Custom Domain**
3. Enter: `api.ai-bookkeeper.app`
4. Render shows DNS instructions (CNAME record)

**At your domain registrar** (where you bought `ai-bookkeeper.app`):
```
Type: CNAME
Name: api
Value: ai-bookkeeper-api.onrender.com
TTL: 3600
```

5. Wait for SSL certificate (automatic via Let's Encrypt, ~5-10 min)

### **For Web Service** (`app.ai-bookkeeper.app`)

1. Go to: Dashboard → **ai-bookkeeper-web** → **Settings** → **Custom Domains**
2. Click: **Add Custom Domain**
3. Enter: `app.ai-bookkeeper.app`

**At your domain registrar**:
```
Type: CNAME
Name: app
Value: ai-bookkeeper-web.onrender.com
TTL: 3600
```

4. Wait for SSL certificate (automatic, ~5-10 min)

---

## 🧪 Verification & Testing

### **1. Wait for Deployments** (~3-5 minutes each)

Check deployment status in Render Dashboard:
- ai-bookkeeper-api: Should show "Live"
- ai-bookkeeper-web: Should show "Live"
- ai-bookkeeper-db: Should show "Available"

### **2. Test API Service**

```bash
# Health check
curl https://api.ai-bookkeeper.app/healthz

# Expected: {"status":"ok", ...}

# API documentation
curl https://api.ai-bookkeeper.app/docs

# Expected: HTML page with Swagger UI

# OpenAPI spec
curl https://api.ai-bookkeeper.app/openapi.json | jq '.info.title'

# Expected: "AI Bookkeeper"

# GPT Actions spec
curl https://api.ai-bookkeeper.app/openapi.gpt.json | jq '.servers'

# Expected: [{"url":"https://api.ai-bookkeeper.app","description":"Production"}]
```

### **3. Test Web Service**

```bash
# Home page (Next.js)
curl -I https://app.ai-bookkeeper.app/

# Expected: HTTP/2 200, content-type: text/html

# Dashboard page
curl -I https://app.ai-bookkeeper.app/dashboard

# Expected: HTTP/2 200 (may redirect to /login if not auth)

# API proxy (should forward to API service)
curl https://app.ai-bookkeeper.app/api/billing/status

# Expected: JSON response or 401 (auth required)
```

### **4. Test Custom Domains** (After DNS propagates)

```bash
# Check DNS
dig api.ai-bookkeeper.app
dig app.ai-bookkeeper.app

# Both should show CNAME records pointing to onrender.com
```

---

## 🔧 Troubleshooting

### **API Service Won't Start**

**Check logs** in Render Dashboard:
- Look for database connection errors
- Verify `DATABASE_URL` is set correctly
- Check Alembic migration errors

**Common fixes**:
```bash
# In Render Shell for ai-bookkeeper-api
alembic current  # Check current migration state
alembic upgrade head  # Manually run migrations
python -c "from app.db.session import engine; print(engine.url)"  # Verify DB URL
```

### **Web Service Won't Start**

**Check logs** in Render Dashboard:
- Look for "Error: NEXT_PUBLIC_*" warnings
- Check if build completed successfully

**Common fixes**:
1. Verify `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_BASE_URL` are marked **"Available during build"**
2. Trigger manual redeploy: Settings → Manual Deploy
3. Check `frontend/next.config.js` has correct API proxy

### **CORS Errors**

If frontend can't reach API:

1. Go to: **ai-bookkeeper-api** → Environment
2. Update: `CORS_ALLOWED_ORIGINS`
3. Add your frontend URL: `https://app.ai-bookkeeper.app`
4. Save and redeploy

### **Database Connection Issues**

```bash
# Verify connection string format
# CORRECT: postgresql://user:pass@host/db?sslmode=require
# WRONG: psql 'postgresql://...'  (don't include 'psql ')
```

---

## 🎯 Post-Deployment Configuration

### **1. Update GPT Actions** (if using custom domain)

In ChatGPT GPT Builder → Configure → Actions:
```
https://api.ai-bookkeeper.app/openapi.gpt.json
```

### **2. Update Stripe Webhook**

In Stripe Dashboard → Developers → Webhooks:
```
https://api.ai-bookkeeper.app/api/billing/stripe_webhook
```

Events to subscribe:
- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_failed`
- `customer.subscription.trial_will_end`

### **3. Update QuickBooks Redirect URI**

In Intuit Developer Portal → Your App → Keys & credentials:
```
https://api.ai-bookkeeper.app/api/auth/qbo/callback
```

---

## 📊 Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                      USERS                                │
└───────────────────┬──────────────────────────────────────┘
                    │
        ┌───────────┴────────────┐
        │                        │
        ▼                        ▼
┌───────────────┐        ┌──────────────────┐
│   Web UI      │        │   GPT Actions    │
│ app.ai-       │        │   (ChatGPT)      │
│ bookkeeper    │        │                  │
│ .app          │        │                  │
└───────┬───────┘        └────────┬─────────┘
        │                         │
        │ /api/* proxy            │ Bearer token
        │                         │
        └─────────────┬───────────┘
                      │
                      ▼
              ┌───────────────┐
              │   API Service │
              │ api.ai-       │
              │ bookkeeper    │
              │ .app          │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │  PostgreSQL   │
              │  (Neon.tech)  │
              └───────────────┘
```

---

## 📂 Files Updated

✅ **Dockerfile.api** - Backend service (Python/FastAPI)
- Removed script dependency on `db_migrate.sh`
- Uses `alembic upgrade head` directly
- Binds to `$PORT` environment variable
- Health check on `/healthz`

✅ **Dockerfile.web** - Frontend service (Next.js)
- Multi-stage build (builder + runner)
- Standalone output mode
- Non-root user for security
- Binds to `$PORT` environment variable

✅ **render-split.yaml** - Render Blueprint
- Configured for custom domains
- API: `api.ai-bookkeeper.app`
- Web: `app.ai-bookkeeper.app`
- All environment variables defined
- PostgreSQL database included

---

## 🎯 Expected Outcome

### **After Deployment**:

**API Service** (`https://api.ai-bookkeeper.app`):
- ✅ FastAPI running on port 8000 (internal) → `$PORT` (external)
- ✅ Serves: `/api/*`, `/docs`, `/openapi.json`, `/healthz`
- ✅ Connected to PostgreSQL database
- ✅ Migrations run automatically on start
- ✅ GPT Actions working via `/openapi.gpt.json`

**Web Service** (`https://app.ai-bookkeeper.app`):
- ✅ Next.js running on port 3000 (internal) → `$PORT` (external)
- ✅ Serves: All pages (`/`, `/dashboard`, `/transactions`, etc.)
- ✅ Proxies `/api/*` requests to API service
- ✅ Full React app with 11 pages accessible
- ✅ Login, signup, dashboard all working

**Database**:
- ✅ PostgreSQL managed by Render
- ✅ Automatic backups
- ✅ Connection string auto-injected into API service

---

## 🔒 Security Checklist

- [ ] All secrets in environment variables (not in code)
- [ ] `JWT_SECRET` and `CSRF_SECRET` are random 32-char hex
- [ ] `DATABASE_URL` includes `?sslmode=require`
- [ ] CORS configured to only allow your frontend domain
- [ ] Stripe webhook signature verification enabled
- [ ] API key authentication working
- [ ] HTTPS/SSL on both services

---

## 📈 Monitoring

### **Key Metrics to Watch**:

**API Service**:
- Response time: < 500ms for most endpoints
- Error rate: < 1%
- Database connections: < 50
- Memory usage: < 512MB

**Web Service**:
- Page load time: < 3s
- Build time: < 5 minutes
- Bundle size: < 500KB

**Database**:
- Connection count: < 50
- Query time: < 100ms average
- Disk usage: Monitor growth

---

## 🎨 URLs After Deployment

### **Production URLs**:
| Service | URL | Purpose |
|---------|-----|---------|
| **API** | `https://api.ai-bookkeeper.app` | Backend API |
| **Web** | `https://app.ai-bookkeeper.app` | Frontend app |
| **Docs** | `https://api.ai-bookkeeper.app/docs` | API documentation |
| **OpenAPI** | `https://api.ai-bookkeeper.app/openapi.gpt.json` | GPT Actions |
| **Database** | Internal connection string | PostgreSQL |

### **Fallback URLs** (if custom domains not configured):
| Service | URL | Purpose |
|---------|-----|---------|
| **API** | `https://ai-bookkeeper-api.onrender.com` | Backend API |
| **Web** | `https://ai-bookkeeper-web.onrender.com` | Frontend app |

---

## ✅ Acceptance Criteria

After deployment, verify:

- [ ] API service shows "Live" in Render Dashboard
- [ ] Web service shows "Live" in Render Dashboard  
- [ ] Database shows "Available" in Render Dashboard
- [ ] `curl https://api.ai-bookkeeper.app/healthz` returns `{"status":"ok"}`
- [ ] `curl https://app.ai-bookkeeper.app/` returns HTML (Next.js)
- [ ] Can access `/dashboard`, `/login`, `/transactions` pages
- [ ] API calls from frontend work (check browser console)
- [ ] GPT Actions still work with API key
- [ ] No CORS errors in browser console

---

## 🚨 Common Issues & Solutions

### **Issue 1: "Couldn't find blueprint file"**

**Solution**: When applying blueprint, manually select `render-split.yaml` from dropdown

### **Issue 2: "Build failed - Dockerfile not found"**

**Solution**: Check `dockerfilePath` in blueprint points to `./Dockerfile.api` or `./Dockerfile.web`

### **Issue 3: "NEXT_PUBLIC_* undefined in production"**

**Solution**: Mark environment variables as "Available during build" in Render Dashboard

### **Issue 4: "Database connection refused"**

**Solution**: Verify `DATABASE_URL` format and ensure it includes `?sslmode=require`

### **Issue 5: "CORS policy blocked"**

**Solution**: Add frontend domain to `CORS_ALLOWED_ORIGINS` in API service env vars

---

## 🎉 Success Indicators

You'll know it's working when:

1. ✅ Both services show **green "Live"** status in Render
2. ✅ API health check returns JSON: `{"status":"ok"}`
3. ✅ Web home page returns HTML (view source shows React/Next.js)
4. ✅ You can navigate to `/dashboard` and see the app
5. ✅ Browser console shows no errors
6. ✅ API calls from frontend succeed (check Network tab)
7. ✅ Custom domains resolve (DNS propagated)
8. ✅ SSL certificates valid (green padlock in browser)

---

## 📞 Next Steps After Deployment

1. **Test full user flow**:
   - Sign up → Dashboard → Connect QBO → Review transactions → Post

2. **Configure integrations**:
   - Stripe webhook
   - QuickBooks OAuth redirect
   - GPT Actions URL

3. **Enable monitoring**:
   - Sentry for error tracking
   - Uptime monitoring
   - Log aggregation

4. **Marketing**:
   - Update GPT Store listing with new domains
   - Update documentation
   - Share with beta users

---

## 🔗 Quick Reference

**Repository**: https://github.com/ContrejfC/ai-bookkeeper  
**Render Dashboard**: https://dashboard.render.com  
**Blueprint File**: `render-split.yaml`  
**API Dockerfile**: `Dockerfile.api`  
**Web Dockerfile**: `Dockerfile.web`  

**Support Docs**:
- `CUSTOM_DOMAIN_SETUP.md` - Domain configuration
- `PRODUCTION_ENV_VARS.md` - All environment variables
- `CLOUD_FRONTEND_AUDIT_REPORT.md` - Deployment analysis

---

**Ready to deploy? Let's do this!** 🚀

Follow **Option A** (Blueprint) for the easiest deployment, or **Option B** (Manual) if you prefer more control.

