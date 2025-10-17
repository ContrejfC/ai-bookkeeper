# Render Split Services Deployment Guide

**Architecture:** Clean two-service deployment (API + Web)

---

## Why Split Services?

**Benefits over monolithic Docker:**
- ✅ **Independent Scaling** - Scale API and Web separately based on load
- ✅ **Simpler Builds** - Each service builds only what it needs
- ✅ **Faster Deploys** - Changes to one service don't rebuild the other
- ✅ **Better Caching** - Docker layers cache more efficiently
- ✅ **Easier Debugging** - Clear service boundaries, isolated logs
- ✅ **Cost Optimization** - Scale down Web during low traffic, keep API up

---

## Architecture Overview

```
┌─────────────────┐
│   User/GPT      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  ai-bookkeeper-web (Next.js)        │
│  - Serves UI at /                   │
│  - Proxies /api/* to API service    │
│  - Proxies /openapi.json to API     │
│  Port: $PORT (Render-provided)      │
└────────┬────────────────────────────┘
         │ HTTPS (internal)
         ▼
┌─────────────────────────────────────┐
│  ai-bookkeeper-api (FastAPI)        │
│  - Serves /api/* endpoints          │
│  - Serves /openapi.json             │
│  - Connects to PostgreSQL           │
│  Port: $PORT (Render-provided)      │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  ai-bookkeeper-db (PostgreSQL)      │
│  - Stores all application data      │
│  - Managed by Render                │
└─────────────────────────────────────┘
```

---

## Deployment Steps

### Option A: Using render-split.yaml (Blueprint)

1. **Push code to GitHub:**
   ```bash
   git add Dockerfile.api Dockerfile.web render-split.yaml
   git commit -m "feat(deploy): split into clean API + Web services"
   git push origin main
   ```

2. **In Render Dashboard:**
   - New → Blueprint
   - Connect to your GitHub repo
   - Select `render-split.yaml`
   - Click "Apply"
   - Render creates 3 resources: API, Web, Database

3. **Set secrets in Dashboard:**
   - Go to each service → Environment
   - Set `JWT_SECRET`, `CSRF_SECRET` (generate with `openssl rand -hex 32`)
   - Set Stripe keys (if using billing)
   - Set QBO credentials (if using QuickBooks)

### Option B: Manual Service Creation

#### 1. Create Database
1. Render Dashboard → New → PostgreSQL
2. Name: `ai-bookkeeper-db`
3. Plan: Starter (or Free for testing)
4. Region: Oregon (or nearest to you)
5. Copy connection string

#### 2. Create API Service
1. New → Web Service
2. Connect GitHub repo
3. Configure:
   - **Name:** `ai-bookkeeper-api`
   - **Runtime:** Docker
   - **Dockerfile Path:** `./Dockerfile.api`
   - **Branch:** main
   - **Plan:** Starter
   - **Health Check Path:** `/healthz`

4. Environment Variables:
   ```
   DATABASE_URL=[paste from database]
   JWT_SECRET=[openssl rand -hex 32]
   CSRF_SECRET=[openssl rand -hex 32]
   BASE_URL=https://ai-bookkeeper-api.onrender.com
   PUBLIC_BASE_URL=https://ai-bookkeeper.onrender.com
   ... (see render-split.yaml for full list)
   ```

5. Click "Create Web Service"

#### 3. Create Web Service
1. New → Web Service
2. Connect GitHub repo  
3. Configure:
   - **Name:** `ai-bookkeeper-web`
   - **Runtime:** Docker
   - **Dockerfile Path:** `./Dockerfile.web`
   - **Branch:** main
   - **Plan:** Starter

4. Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://ai-bookkeeper-api.onrender.com
   NEXT_PUBLIC_BASE_URL=https://ai-bookkeeper.onrender.com
   ```

5. Click "Create Web Service"

---

## Service URLs

After deployment:

- **Web (Public):** https://ai-bookkeeper-web.onrender.com
- **API (Internal):** https://ai-bookkeeper-api.onrender.com
- **Database:** Internal only (Render private network)

**For users/GPT:**
- Main app: https://ai-bookkeeper-web.onrender.com
- OpenAPI: https://ai-bookkeeper-web.onrender.com/openapi.json (proxied)
- API endpoints: https://ai-bookkeeper-web.onrender.com/api/* (proxied)

---

## Custom Domain (Optional)

**Recommended setup:**
- **Main domain:** `app.yourdomain.com` → ai-bookkeeper-web
- **API subdomain:** `api.yourdomain.com` → ai-bookkeeper-api

**Configuration:**
1. Add custom domain to each service in Render
2. Update environment variables:
   ```
   BASE_URL=https://app.yourdomain.com
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com
   QBO_REDIRECT_URI=https://app.yourdomain.com/api/auth/qbo/callback
   ```
3. Update Stripe webhook URL
4. Update QBO app redirect URI in Intuit portal

---

## Environment Variables Reference

### API Service (Required)

| Variable | Example | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `postgres://...` | Auto from Render DB |
| `JWT_SECRET` | `[random 32 hex]` | Generate fresh |
| `CSRF_SECRET` | `[random 32 hex]` | Generate fresh |
| `BASE_URL` | `https://your-domain.com` | Public URL |

### API Service (Optional - Features)

| Variable | Example | Notes |
|----------|---------|-------|
| `STRIPE_SECRET_KEY` | `sk_test_...` | For billing |
| `QBO_CLIENT_ID` | `AB...` | For QuickBooks |
| `QBO_CLIENT_SECRET` | `...` | For QuickBooks |
| `SENTRY_DSN` | `https://...` | Error tracking |

### Web Service (Required)

| Variable | Example | Notes |
|----------|---------|-------|
| `NEXT_PUBLIC_API_URL` | `https://api-service.onrender.com` | API service URL |

---

## Health Checks

### API Service
**Endpoint:** `/healthz`

**Response:**
```json
{
  "status": "healthy",
  "db": "ok",
  "version": "0.9.1"
}
```

### Web Service
**Endpoint:** `/` or `/api/health` (proxied to API)

**Response:** 200 OK

---

## Troubleshooting

### Issue: Web can't reach API

**Symptoms:**
- Frontend loads but API calls fail
- 502 errors on /api/* requests

**Fix:**
1. Check `NEXT_PUBLIC_API_URL` in Web service env vars
2. Verify API service is healthy (`curl https://api-service.onrender.com/healthz`)
3. Check CORS settings in API (`CORS_ALLOWED_ORIGINS`)

### Issue: Database connection failed

**Symptoms:**
- API /healthz returns 500
- Logs show "could not connect to server"

**Fix:**
1. Check `DATABASE_URL` in API service env vars
2. Verify database is running (Render Dashboard → Database)
3. Check if DB plan suspended (upgrade to paid plan)

### Issue: Migrations fail on deploy

**Symptoms:**
- API deployment fails
- Logs show "alembic error"

**Fix:**
1. SSH into API service: Render Dashboard → Shell
2. Run manually: `./scripts/db_migrate.sh`
3. If multiple heads: `ALREADY_DEPLOYED=true ./scripts/db_repair_baseline.sh`

---

## Migration from Monolithic Docker

**If you're currently using Dockerfile (monolithic):**

1. **Backup current env vars** from Render Dashboard
2. **Delete old service** (or keep for rollback)
3. **Deploy split services** (Option A or B above)
4. **Restore env vars** to new API service
5. **Test:** Run smoke test to verify all working
6. **Update DNS** if using custom domain

**Rollback:**
- If issues, redeploy old monolithic service
- Update env vars back
- No data loss (database unchanged)

---

## Scaling Recommendations

### Light Traffic (<1000 users)
- **API:** Starter plan (512MB RAM, 0.5 CPU)
- **Web:** Starter plan
- **DB:** Starter ($7/month, 1GB storage)

### Medium Traffic (1000-10000 users)
- **API:** Standard plan (2GB RAM, 1 CPU) - handles more concurrent QBO/Stripe calls
- **Web:** Starter (static serving is lightweight)
- **DB:** Standard ($20/month, 10GB storage)

### High Traffic (10000+ users)
- **API:** Pro plan (4GB RAM, 2 CPU) + autoscaling
- **Web:** Standard + CDN
- **DB:** Pro ($65/month, 100GB storage) + read replicas

---

## Cost Comparison

**Monolithic (single Docker service):**
- Web Service: $25/month (Standard plan for both frontend + backend)
- Database: $7/month
- **Total: $32/month**

**Split Services:**
- API Service: $7/month (Starter, can scale independently)
- Web Service: $7/month (Starter, mostly static)
- Database: $7/month
- **Total: $21/month**

**Savings: $11/month + better scalability**

---

## Monitoring (Split Services)

### Dashboards to Watch
- **API Service:** Render → ai-bookkeeper-api → Metrics
  - CPU, Memory, Response time
  - Error rate, Request volume
- **Web Service:** Render → ai-bookkeeper-web → Metrics
  - Static asset serving
  - Proxy errors (if any)
- **Database:** Render → ai-bookkeeper-db → Metrics
  - Connection count
  - Query performance

### Alerts to Set
1. API CPU >80% for 5 min → Scale up
2. API error rate >5% → Investigate logs
3. Web 5xx errors → Check API connectivity
4. DB connection count near limit → Scale DB

---

## Best Practices

### Development Workflow
1. **Local:** Run API and Web separately
   ```bash
   # Terminal 1 - API
   cd /path/to/ai-bookkeeper
   uvicorn app.api.main:app --reload --port 8000
   
   # Terminal 2 - Web
   cd frontend
   npm run dev
   ```

2. **Staging:** Deploy to Render with TEST Stripe/Sandbox QBO

3. **Production:** Switch to LIVE Stripe/Production QBO

### CI/CD
- GitHub Actions runs tests on push
- Render auto-deploys on push to `main`
- OpenAPI version guard prevents breaking changes

### Secrets Rotation
- JWT/CSRF: Rotate every 90 days
- Stripe: Rotate if suspected leak
- QBO: Rotates automatically (OAuth refresh)
- API keys: Revoke and regenerate per tenant

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-17  
**Recommended for:** All new deployments

