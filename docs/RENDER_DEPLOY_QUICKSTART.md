# Render Deployment Quickstart

**Goal:** Get from Blueprint → Live services in ~10 minutes with clear debug steps.

---

## 🚀 DEPLOY NOW (5 steps)

### 1. Apply the Blueprint

**In Render Dashboard:**

1. Click **"New +"** → **"Blueprint"**
2. Connect repo: `ContrejfC/ai-bookkeeper`
3. Select: `render-split.yaml`
4. Click **"Apply"**

**If you already have services:**
- Option A: Delete old `ai-bookkeeper-web` / `ai-bookkeeper-api` first
- Option B: Rename new services during Blueprint apply (e.g., `ai-bookkeeper-web-v2`)

**Blueprint creates:**
- ✅ `ai-bookkeeper-api` (FastAPI backend)
- ✅ `ai-bookkeeper-web` (Next.js frontend)
- ✅ `ai-bookkeeper-db` (PostgreSQL database)

---

### 2. Configure Web Service (Next.js)

**In `ai-bookkeeper-web` service:**

1. Go to **"Environment"** tab
2. For **EACH** `NEXT_PUBLIC_*` variable:
   - Click **⋮** (three dots)
   - Check **"Available during build"** ✅
   - This passes the var to Docker build as ARG

**Variables to mark:**
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_BASE_URL`

3. Click **"Manual Deploy"** (top right)

---

### 3. Configure API Service (FastAPI)

**In `ai-bookkeeper-api` service:**

1. Go to **"Environment"** tab
2. **Required secrets** (generate first):

```bash
# Run locally to generate secrets:
openssl rand -hex 32  # Use for JWT_SECRET
openssl rand -hex 32  # Use for CSRF_SECRET
```

3. **Add in Render:**

```bash
# Core (REQUIRED for first boot):
JWT_SECRET=<paste generated value>
CSRF_SECRET=<paste generated value>

# Database (auto-injected by Render, verify it exists):
DATABASE_URL=postgresql://...

# Optional (skip for first boot, add later):
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
QBO_CLIENT_ID=...
QBO_CLIENT_SECRET=...
```

4. Click **"Save Changes"** → Auto-redeploys

---

### 4. Verify Health Checks

**Wait for "Live" status (~3-5 minutes), then test:**

```bash
# API health (should return 200 + DB check):
curl https://ai-bookkeeper-api.onrender.com/healthz

# Web health (should return 200):
curl https://ai-bookkeeper-web.onrender.com/healthz

# OpenAPI via Web proxy (should return JSON):
curl https://ai-bookkeeper-web.onrender.com/openapi.json | jq '.info.version'
```

**Expected output:**
- API: `{"status": "healthy", "database": "connected"}`
- Web: `{"status": "ok"}`
- OpenAPI: `"v1.0"` (or current version)

---

### 5. Run Full Smoke Test

**From your local machine:**

```bash
cd /Users/fabiancontreras/ai-bookkeeper

# First, create an API key in Render Shell (ai-bookkeeper-api service):
# python scripts/create_api_key.py --tenant production --name "Smoke Test"
# Copy output: ak_live_XXXXXXXXXXXXXXXXXXXXXXX

# Then run smoke test locally:
./ops/smoke_live.sh \
  --base-url https://ai-bookkeeper-web.onrender.com \
  --api-key ak_live_XXXXXXXXXXXXXXXXXXXXXXX \
  --use-sample-je \
  --spec-version v1.0
```

**Expected:** ✅ 7/7 tests passed

---

## 🔧 FAST TRIAGE (if build fails)

Open **Build** tab → **View Full Log** and match the first error:

### Error: `npm ci` / lockfile errors

**Symptom:**
```
npm ERR! The package-lock.json file does not exist or is too old
```

**Fix:**
- Ensure `package.json` exists and is valid
- Commit a `package-lock.json` (run `npm install` locally)
- Or switch to `npm install` in Dockerfile.web

**Quick test locally:**
```bash
cd frontend
npm ci  # Should succeed without errors
```

---

### Error: `next build` missing env

**Symptom:**
```
Error: NEXT_PUBLIC_API_URL is not defined
```

**Fix:**
1. Go to Web service → Environment tab
2. For each `NEXT_PUBLIC_*` var:
   - Click **⋮** → **"Available during build"** ✅
3. Manual Deploy

**Why:** Next.js bakes these vars into the bundle at **build time**, not runtime.

---

### Error: `server.js not found`

**Symptom:**
```
Error: Cannot find module '/app/server.js'
```

**Fix:**
- Ensure `next.config.js` has `output: 'standalone'`
- Or switch CMD to: `next start -p $PORT`
- Verify Dockerfile.web copies `.next/standalone` and `.next/static`

**Quick test locally:**
```bash
cd frontend
npm run build
ls .next/standalone/server.js  # Should exist
```

---

### Error: Python/alembic during build

**Symptom:**
```
RUN alembic upgrade head
sqlalchemy.exc.OperationalError: database not available
```

**Fix:**
- **NEVER** run migrations in `RUN` steps (no DB at build time)
- Move to `CMD` (runtime):
  ```dockerfile
  CMD ./scripts/db_migrate.sh && exec uvicorn ...
  ```

**Verify:** Check Dockerfile.api for any `RUN` lines with `alembic` or `pytest`

---

### Error: "listening on 3000" / health fails

**Symptom:**
```
Health check failed: connection refused on port 10000
```

**Fix:**
- Ensure both services bind to **`$PORT`**:
  - API: `uvicorn --port ${PORT:-8000}`
  - Web: `next start -p ${PORT:-3000}` or `PORT=$PORT node server.js`
- Health path must be `/healthz` (not `/health` or `/`)

**Quick test locally:**
```bash
# API:
PORT=9999 uvicorn app.api.main:app --port $PORT
curl http://localhost:9999/healthz

# Web:
cd frontend
PORT=9998 npm start
curl http://localhost:9998/healthz
```

---

### Error: Overlapping deploys

**Symptom:**
```
Deploy canceled: another deploy started
```

**Fix:**
1. Go to service → **Settings** tab
2. **Overlapping Deploy Policy** → **"Cancel ongoing deploys"**
3. Save and retry

---

## 🎯 QUICK SANITY CHECKS (no logs needed)

**1. API up?**
```bash
curl https://ai-bookkeeper-api.onrender.com/healthz
```

**2. Web up?**
```bash
curl https://ai-bookkeeper-web.onrender.com/healthz
```

**3. Web → API proxy working?**
```bash
curl https://ai-bookkeeper-web.onrender.com/openapi.json | jq '.info.version'
```

**4. Database connected?**
```bash
# In Render Shell (ai-bookkeeper-api):
python -c "from app.db.session import get_db; next(get_db()); print('✅ DB connected')"
```

**5. API key auth working?**
```bash
# Create key in Render Shell:
python scripts/create_api_key.py --tenant test --name "Sanity Check"

# Test with key:
curl -H "Authorization: Bearer ak_live_XXX" \
  https://ai-bookkeeper-api.onrender.com/actions | jq '.version'
```

---

## 📊 DEPLOYMENT TIMELINE

**Normal deployment (from git push):**
- Blueprint apply: ~30 seconds
- Docker build (API): ~3-5 minutes
- Docker build (Web): ~5-7 minutes
- Health checks stabilize: ~1-2 minutes
- **Total:** ~10 minutes

**If you see longer:**
- Check for cached layers (should speed up 2nd+ deploys)
- Check for overlapping deploys (cancel policy)
- Check for build-time scripts (migrations, tests, verification)

---

## 🚨 COMMON PITFALLS

### ❌ Build-time migrations
**Bad:**
```dockerfile
RUN alembic upgrade head  # DB not available at build time!
```

**Good:**
```dockerfile
CMD ./scripts/db_migrate.sh && exec uvicorn ...
```

---

### ❌ Hardcoded ports
**Bad:**
```dockerfile
CMD uvicorn app.api.main:app --port 8000
```

**Good:**
```dockerfile
CMD uvicorn app.api.main:app --port ${PORT:-8000}
```

---

### ❌ Missing build-time env vars
**Bad:**
```yaml
# render-split.yaml
- key: NEXT_PUBLIC_API_URL
  value: https://...
  # Missing: sync: false for secrets
```

**Good:**
```yaml
- key: NEXT_PUBLIC_API_URL
  value: https://ai-bookkeeper-api.onrender.com
  # + Mark "Available during build" in Dashboard UI
```

---

### ❌ Wrong health path
**Bad:**
```yaml
healthCheckPath: /health  # Does not exist
```

**Good:**
```yaml
healthCheckPath: /healthz  # Matches FastAPI route
```

---

## 🎉 SUCCESS CRITERIA

**You're live when:**

1. ✅ Both services show "Live" (green) in Dashboard
2. ✅ `/healthz` returns 200 on both services
3. ✅ `/openapi.json` returns valid JSON via Web service
4. ✅ API key auth works (`/actions` endpoint)
5. ✅ Database migrations ran successfully (check API logs)
6. ✅ `smoke_live.sh` passes 7/7 tests
7. ✅ ChatGPT GPT can call Actions (if configured)

---

## 📚 NEXT STEPS

**After first successful deploy:**

1. **Set up custom domain** (optional):
   - Web service → Settings → Custom Domain
   - Point DNS CNAME to Render URL

2. **Configure Stripe webhooks**:
   - Stripe Dashboard → Webhooks
   - Endpoint URL: `https://ai-bookkeeper-api.onrender.com/billing/webhook`
   - Events: `checkout.session.completed`, `customer.subscription.*`, etc.

3. **Configure QBO OAuth**:
   - Intuit Developer Portal → Create App
   - Redirect URI: `https://ai-bookkeeper-api.onrender.com/auth/qbo/callback`
   - Copy Client ID/Secret to Render env vars

4. **Create ChatGPT GPT**:
   - Import Actions: `https://ai-bookkeeper-web.onrender.com/openapi.json`
   - Auth: Bearer `ak_live_...`
   - Instructions: `gpt_config/instructions.txt`

5. **Monitor with alerts**:
   - See `docs/OBS_ALERTS.md`
   - Set up Render notification channels (Slack, email)

---

## 🆘 STILL STUCK?

**If none of the above helps:**

1. **Check recent commits:**
   ```bash
   git log --oneline -5
   # Look for changes to Dockerfiles, render-split.yaml, or env vars
   ```

2. **Compare with working local dev:**
   ```bash
   # Does it work locally with same env vars?
   docker build -f Dockerfile.api -t test-api .
   docker run -e DATABASE_URL=sqlite:///./test.db test-api
   ```

3. **Render logs:**
   - API service → Logs tab → filter "ERROR"
   - Web service → Logs tab → filter "Error"
   - Database → Metrics tab → check connections

4. **Ping for help:**
   - Include: service name, first 50 lines of build log, env var list (redact secrets)
   - Describe: expected vs actual behavior

---

**Last updated:** 2025-10-17  
**Deployment target:** Render (Docker + Blueprint)  
**Services:** Split architecture (API + Web + DB)

