# 🔧 Render Configuration Settings

**Complete copy/paste reference for Render Dashboard**  
**Architecture:** Split services (API + Web + Database)

---

## 🗄️ Database Service

### Basic Settings
```
Service Type: PostgreSQL
Name: ai-bookkeeper-db
Database Name: ai_bookkeeper
Region: Oregon (US West)
PostgreSQL Version: 15 (or latest)
Plan: Starter (or higher for production)
```

### IP Allow List
```
No restrictions (leave empty)
```

### Backups
```
✓ Enable automatic backups (recommended)
Retention: 7 days (or longer for production)
```

---

## 🐍 API Service (FastAPI Backend)

### Basic Settings
```
Service Type: Web Service
Name: ai-bookkeeper-api
Runtime: Docker
Region: Oregon (US West)
Branch: main
Dockerfile Path: ./Dockerfile.api
Docker Build Context: ./ (root)
Plan: Starter (or higher for production)
```

### Start Command
```
(Leave empty - uses CMD from Dockerfile)
```

### Health Check
```
Health Check Path: /healthz
```

### Auto-Deploy
```
✓ Auto-Deploy: Yes
```

---

### Environment Variables (API Service)

#### Core Application
```yaml
ENV: production
BASE_URL: https://ai-bookkeeper-api.onrender.com
PUBLIC_BASE_URL: https://ai-bookkeeper.onrender.com
LOG_LEVEL: INFO
CORS_ALLOWED_ORIGINS: https://ai-bookkeeper.onrender.com,https://ai-bookkeeper-web.onrender.com
```

#### Secrets (Generate Locally)
```bash
# Run these commands locally to generate secrets:
openssl rand -hex 32  # Use for JWT_SECRET
openssl rand -hex 32  # Use for CSRF_SECRET
```

```yaml
JWT_SECRET: [paste generated hex - 64 characters]
CSRF_SECRET: [paste generated hex - 64 characters]
```

#### Database
```yaml
DATABASE_URL: [Auto-populated when database linked]
```

**To link database:**
1. In API Service → Environment tab
2. Click "Link Database"
3. Select `ai-bookkeeper-db`
4. Save changes

#### Stripe LIVE (Set after Phase 2)
```yaml
STRIPE_SECRET_KEY: sk_live_YOUR_LIVE_KEY_HERE
STRIPE_PUBLISHABLE_KEY: pk_live_YOUR_LIVE_KEY_HERE
STRIPE_WEBHOOK_SECRET: whsec_YOUR_WEBHOOK_SIGNING_SECRET
STRIPE_PRICE_STARTER: price_xxxxxxxxxxxxx
STRIPE_PRICE_PRO: price_xxxxxxxxxxxxx
STRIPE_PRICE_FIRM: price_xxxxxxxxxxxxx
```

**How to get these values:**
1. Run `python3 scripts/stripe_bootstrap.py` locally with LIVE key
2. Copy price IDs from output
3. Create webhook in Stripe Dashboard
4. Copy webhook signing secret

#### QuickBooks Production (Set after Phase 3)
```yaml
QBO_CLIENT_ID: YOUR_PRODUCTION_CLIENT_ID
QBO_CLIENT_SECRET: YOUR_PRODUCTION_CLIENT_SECRET
QBO_BASE: https://quickbooks.api.intuit.com
QBO_REDIRECT_URI: https://ai-bookkeeper.onrender.com/api/auth/qbo/callback
QBO_SCOPES: com.intuit.quickbooks.accounting
QBO_ENVIRONMENT: production
```

**How to get these values:**
1. Go to Intuit Developer Dashboard
2. Create production app (or get prod keys for existing)
3. Copy Client ID and Client Secret
4. Set redirect URI in Intuit Dashboard

#### Billing & Limits
```yaml
FREE_PROPOSE_CAP_DAILY: 50
AUTOPOST: false
```

#### Privacy & Security
```yaml
ENABLE_LABELS: true
LABEL_SALT_ROUNDS: 12
```

#### Monitoring (Optional)
```yaml
SENTRY_DSN: [Your Sentry DSN - optional]
```

---

## 🌐 Web Service (Next.js Frontend)

### Basic Settings
```
Service Type: Web Service
Name: ai-bookkeeper-web
Runtime: Docker
Region: Oregon (US West)
Branch: main
Dockerfile Path: ./Dockerfile.web
Docker Build Context: ./ (root)
Plan: Starter (or higher for production)
```

### Start Command
```
(Leave empty - uses CMD from Dockerfile)
```

### Health Check
```
Health Check Path: /healthz
```

### Auto-Deploy
```
✓ Auto-Deploy: Yes
```

---

### Environment Variables (Web Service)

⚠️ **CRITICAL:** Both variables below MUST be marked as **"Available during build"**

**To mark as "Available during build":**
1. After adding each variable, hover over it
2. Click the **three dots menu (⋮)**
3. Select **"Available during build"**
4. Repeat for both variables

```yaml
NEXT_PUBLIC_API_URL: https://ai-bookkeeper-api.onrender.com
NEXT_PUBLIC_BASE_URL: https://ai-bookkeeper.onrender.com
```

**Why this is critical:**
- Next.js needs these at BUILD time to embed API URLs
- Without this, frontend will fail to connect to backend
- Render won't auto-mark these - you must do it manually

---

## 🔍 Verification Commands

### After Deployment

**Check API Health:**
```bash
curl https://ai-bookkeeper-api.onrender.com/healthz
# Expected: {"status":"healthy","database":"connected"}
```

**Check Web Health:**
```bash
curl https://ai-bookkeeper.onrender.com/healthz
# Expected: {"status":"ok"}
```

**Check OpenAPI:**
```bash
curl https://ai-bookkeeper.onrender.com/openapi.json | jq '.info.version'
# Expected: "0.2.1-beta"
```

**Check Actions Discovery:**
```bash
curl https://ai-bookkeeper.onrender.com/actions | jq '.version'
# Expected: "0.2.1-beta"
```

---

## 🚀 Deployment Order

**For fresh deployment:**

1. **Create Database First**
   - Wait for status: "Available"

2. **Create API Service**
   - Link database before first deploy
   - Set core env vars (ENV, BASE_URL, etc.)
   - Set secrets (JWT_SECRET, CSRF_SECRET)
   - Leave Stripe/QBO vars blank initially
   - Wait for status: "Live"

3. **Create Web Service**
   - Set NEXT_PUBLIC_* vars
   - Mark both as "Available during build"
   - Wait for status: "Live"

4. **Configure Stripe LIVE**
   - Run `stripe_bootstrap.py` locally
   - Add Stripe env vars to API service
   - API will auto-redeploy

5. **Configure QBO Production**
   - Get production credentials from Intuit
   - Add QBO env vars to API service
   - API will auto-redeploy

6. **Run Launch Verification**
   - SSH into API service
   - Run `./ops/launch_live.sh`

---

## 🔄 Updating Environment Variables

**After adding/changing environment variables:**

1. Click **"Save Changes"** in Render
2. Service will auto-redeploy
3. Wait for new deployment to complete
4. Verify health checks pass

**To avoid downtime:**
- Update API and Web services separately
- Wait for each to complete before updating the next
- Monitor logs during deployment

---

## 📊 Monitoring & Logs

### View Logs
```
Render Dashboard → Service → Logs tab
```

**Watch for:**
- ✅ `Database migrations completed`
- ✅ `CSRF protection middleware enabled`
- ✅ `Entitlement gate middleware enabled`
- ✅ `QBO integration routes loaded`
- ✅ `GPT Actions discovery route loaded`
- ✅ `Uvicorn running on...`
- ❌ Any ERROR or CRITICAL level messages

### View Metrics
```
Render Dashboard → Service → Metrics tab
```

**Monitor:**
- CPU usage (should be < 50% normally)
- Memory usage (should be < 80% of plan limit)
- Request rate (varies by usage)
- Response time (should be < 1s for most requests)

---

## 🚨 Troubleshooting

### Issue: "Build Failed"

**Check:**
- Dockerfile path is correct (`./Dockerfile.api` or `./Dockerfile.web`)
- Branch is correct (`main`)
- No recent commits broke the build

**Fix:**
- View build logs for specific error
- Verify Dockerfile hasn't changed
- Try manual rebuild

### Issue: "Deploy Failed" or Service Won't Start

**Check API Service:**
- `DATABASE_URL` is set (database linked)
- All required env vars are set
- Health check passes: `/healthz`

**Check Web Service:**
- `NEXT_PUBLIC_*` vars marked "Available during build"
- Build completed successfully
- Health check passes: `/healthz`

**Fix:**
- Check logs for specific startup errors
- Verify environment variables
- Ensure health check paths are correct

### Issue: "Health Check Failed"

**API Service:**
```bash
# Test directly:
curl https://ai-bookkeeper-api.onrender.com/healthz

# Should return 200 OK with:
{"status":"healthy","database":"connected"}
```

**Web Service:**
```bash
# Test directly:
curl https://ai-bookkeeper.onrender.com/healthz

# Should return 200 OK with:
{"status":"ok"}
```

**Fix:**
- Ensure services are fully started (check logs)
- Verify health check path is `/healthz` (not `/health`)
- Check if database connection is working (API service)

---

## 📞 Support Resources

**Documentation:**
- Full launch guide: `docs/GO_LIVE_NOW.md`
- Docker audit: `status_now/DOCKER_AUDIT.md`
- Troubleshooting: `status_now/RENDER_TROUBLESHOOT.md`

**Scripts:**
- Environment verification: `scripts/verify_prod_env.py`
- QBO verification: `scripts/check_qbo_env.py`
- Stripe verification: `scripts/verify_stripe_webhook.py`
- Launch script: `ops/launch_live.sh`

**Render Documentation:**
- [Docker Deployments](https://render.com/docs/docker)
- [Environment Variables](https://render.com/docs/configure-environment-variables)
- [Health Checks](https://render.com/docs/health-checks)
- [PostgreSQL](https://render.com/docs/databases)
