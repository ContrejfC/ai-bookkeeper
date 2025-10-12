# Render Deployment Guide - Production Staging

**Platform:** Render.com  
**Stack:** Docker + Tesseract OCR + Postgres + Redis + RQ  
**Auto-Deploy:** ✅ On git push  
**Auto-Migrate:** ✅ Post-deploy hook  
**Screenshot CI:** ✅ GitHub Actions + Playwright  

---

## Quick Start (15 minutes)

### Prerequisites
- GitHub account with repository
- Render.com account (free tier available)
- Git repository connected to Render

### 1. Push Code to GitHub

```bash
cd ~/ai-bookkeeper

# Stage all files
git add .

# Commit
git commit -m "Add Render deployment with Tesseract Docker + Playwright CI

- Dockerfile with Tesseract OCR and system dependencies
- render.yaml with web + worker + cron services
- Automatic migrations on deploy via postDeployCommand
- .env.local.sample and .env.staging.sample for env split
- GitHub Actions workflow for Playwright screenshots
- capture_screenshots_playwright.py for automated UI testing"

# Push to main
git push origin main
```

### 2. Create PostgreSQL Database

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "PostgreSQL"
3. Configure:
   - **Name:** `ai-bookkeeper-db`
   - **Database:** `ai_bookkeeper_staging`
   - **User:** `bookkeeper`
   - **Region:** Oregon (US West)
   - **Plan:** Starter ($7/month, 1GB storage)
4. Click "Create Database"
5. **Copy Internal Connection String** (starts with `postgresql://`)
   - Format: `postgresql://bookkeeper:xxxx@dpg-xxxxx-a.oregon-postgres.render.com:5432/ai_bookkeeper_staging`

### 3. Create Redis Instance

1. Render Dashboard → "New" → "Redis"
2. Configure:
   - **Name:** `ai-bookkeeper-redis`
   - **Region:** Oregon (US West)
   - **Plan:** Starter ($3/month, 25MB)
   - **Max Memory Policy:** `allkeys-lru`
3. Click "Create Redis"
4. **Copy Internal Connection String** (starts with `redis://`)
   - Format: `redis://:password@red-xxxxx-a.oregon-redis.render.com:6379/0`

### 4. Deploy from Blueprint

1. Render Dashboard → "New" → "Blueprint"
2. Connect your GitHub repository
3. Render will detect `render.yaml`
4. Review services (3 total):
   - **Web:** ai-bookkeeper-web
   - **Worker:** ai-bookkeeper-worker
   - **Cron:** ai-bookkeeper-analytics
5. Click "Apply"

### 5. Configure Secrets

In Render Dashboard → Web Service → Environment:

**Required Secrets:**
```bash
# Database (from step 2)
DATABASE_URL=postgresql://bookkeeper:xxxx@dpg-xxxxx-a.oregon-postgres.render.com:5432/ai_bookkeeper_staging

# Redis (from step 3)
REDIS_URL=redis://:password@red-xxxxx-a.oregon-redis.render.com:6379/0

# JWT Secret (generate new)
JWT_SECRET_KEY=$(openssl rand -hex 32)
# Example: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

# Password Reset Secret (generate new)
PASSWORD_RESET_SECRET=$(openssl rand -hex 32)
```

**Optional Secrets (if using these features):**
```bash
# OpenAI (for LLM categorization)
OPENAI_API_KEY=sk-proj-xxx

# S3 (for artifact storage)
S3_ENDPOINT=https://s3.amazonaws.com
S3_BUCKET=ai-bookkeeper-staging
S3_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
S3_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# SEO Control (important for staging vs production)
SEO_INDEX=0  # Use 0 for staging (noindex), 1 for production

# Email (for notifications)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.xxx
SMTP_FROM_EMAIL=noreply@yourdomain.com

# Slack (for notifications)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx

# Stripe (test mode)
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Xero (test mode)
XERO_CLIENT_ID=xxx
XERO_CLIENT_SECRET=xxx
```

### 6. Wait for First Deploy

- Render will build Docker image (~5-10 minutes first time)
- Watch build logs in Render Dashboard
- After build completes, `postDeployCommand` runs: `alembic upgrade head`
- Health check on `/healthz` must pass before service goes live

### 7. Seed Pilot Tenants

Once deployed, open Render Shell (Dashboard → Web Service → Shell):

```bash
# Seed demo data
python scripts/seed_demo_data.py

# Or create specific pilot tenants
python scripts/create_pilot_tenants.py
```

### 8. Verify Deployment

```bash
# Get your Render URL (e.g., https://ai-bookkeeper-web.onrender.com)
export RENDER_URL=https://YOUR_SERVICE.onrender.com

# Health check
curl $RENDER_URL/healthz
# Expected: {"status":"ok","database_status":"healthy"}

# Readiness check
curl $RENDER_URL/readyz
# Expected: {"status":"ready","checks":{"database":"ok","migrations":"ok"}}

# Verify Tesseract OCR
curl $RENDER_URL/api/storage/info -H "Authorization: Bearer TOKEN"
# Should show OCR_PROVIDER=tesseract in environment
```

### 9. Login and Test

```bash
# Get JWT token
curl -X POST $RENDER_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@pilot-smb-001.demo","password":"demo-password-123"}' \
  | jq -r .access_token

# Save token
export JWT_TOKEN="<token_from_above>"

# Test review page
curl $RENDER_URL/review -H "Authorization: Bearer $JWT_TOKEN"

# Test receipts with OCR
curl $RENDER_URL/api/receipts?tenant_id=pilot-smb-001 \
  -H "Authorization: Bearer $JWT_TOKEN" | jq .
```

---

## Automated Screenshot CI (GitHub Actions + Playwright)

### Setup

1. **Add Staging URL as GitHub Secret:**
   - Go to GitHub repo → Settings → Secrets and variables → Actions
   - Add new secret: `STAGING_BASE_URL` = `https://your-app.onrender.com`

2. **Trigger Workflow:**
   ```bash
   # Push to main or staging branch (auto-triggers)
   git push origin main
   
   # Or manually trigger
   # GitHub repo → Actions → "UI Screenshots" → Run workflow
   ```

3. **View Results:**
   - GitHub repo → Actions → Click on workflow run
   - Download `ui-screenshots` artifact (zip file with all PNGs)
   - Download `screenshot-index` to see list of captured screenshots

### Local Testing

```bash
# Install Playwright
pip install playwright
python -m playwright install --with-deps chromium

# Capture screenshots locally
python scripts/capture_screenshots_playwright.py \
  --base-url http://localhost:8000 \
  --manifest artifacts/ui-assessment/screenshot_manifest.json \
  --out artifacts/ui-assessment

# Or run in headed mode (see browser)
python scripts/capture_screenshots_playwright.py \
  --base-url http://localhost:8000 \
  --manifest artifacts/ui-assessment/screenshot_manifest.json \
  --out artifacts/ui-assessment \
  # (remove --headless flag)
```

---

## Post-Deployment Checklist

### A) Infrastructure Verification

- [ ] **Web service running:** Check Render Dashboard → Status = "Live"
- [ ] **Worker service running:** Check Render Dashboard → Status = "Live"
- [ ] **Cron job scheduled:** Check Render Dashboard → Next run time
- [ ] **Postgres connected:** `curl $RENDER_URL/healthz | jq .database_status` = `"healthy"`
- [ ] **Redis connected:** Worker logs show "Listening on ai_bookkeeper queue"

### B) Migrations & Data

- [ ] **Migrations at head:** `curl $RENDER_URL/readyz | jq .checks.migrations` = `"ok"`
- [ ] **Pilot tenants created:** Login as `owner@pilot-smb-001.demo` succeeds
- [ ] **Safety settings verified:** AUTOPOST=false, threshold=0.90 confirmed

### C) OCR Provider

- [ ] **Tesseract installed:** Render Shell → `tesseract --version` shows v5.x
- [ ] **Provider active:** Environment shows `OCR_PROVIDER=tesseract`
- [ ] **Receipts working:** `/api/receipts` returns bbox fields

### D) Analytics & Monitoring

- [ ] **Event logging active:** Logs show "Logged event: page_view"
- [ ] **Cron job scheduled:** Dashboard shows next run at 02:00 UTC
- [ ] **Analytics endpoint working:** `/api/analytics/last7` returns data

### E) Security & Performance

- [ ] **HTTPS enabled:** URL starts with `https://`
- [ ] **Security headers present:** `curl -I $RENDER_URL` shows CSP, HSTS
- [ ] **CORS restricted:** Only staging domain allowed
- [ ] **CSRF active:** State-changing requests require CSRF token
- [ ] **Route timings:** All routes <300ms p95 (check Render Metrics)

---

## Render-Specific Configuration

### Environment Variables Set in render.yaml

**App Config (already set):**
- `UI_ASSESSMENT=1` - Assessment banner visible
- `AUTOPOST_ENABLED=false` - Auto-posting disabled
- `GATING_THRESHOLD=0.90` - High confidence required
- `DEFAULT_THRESHOLD=0.90` - Default threshold
- `LLM_BUDGET_CAP_USD=50` - Cost controls
- `OCR_PROVIDER=tesseract` - OCR engine

**Set as Secrets (in Dashboard):**
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `JWT_SECRET_KEY` - Authentication secret
- `PASSWORD_RESET_SECRET` - Password reset tokens
- `OPENAI_API_KEY` - Optional LLM
- `S3_*` - Optional S3 storage
- `SMTP_*` - Optional email
- `SLACK_WEBHOOK_URL` - Optional Slack
- `STRIPE_*` - Optional billing
- `XERO_*` - Optional integration

### Automatic Migrations

**How it works:**
- `render.yaml` includes `postDeployCommand: alembic upgrade head`
- After each successful build, Render runs this command
- Migrations are applied before traffic reaches the new version
- If migration fails, deploy is rolled back

**Manual migration (if needed):**
```bash
# In Render Shell
python -m alembic upgrade head

# Or downgrade one version
python -m alembic downgrade -1

# Check current version
python -m alembic current
```

### Worker Service

**Plan Required:** Starter ($7/mo) or higher  
⚠️ **Free tier does not support background workers**

**Starts automatically** with:
```bash
rq worker -u $REDIS_URL ai_bookkeeper
```

**Enable Worker in Render:**
1. Go to: Dashboard → "New" → "Worker"
2. Or: Edit `render.yaml` and apply Blueprint
3. Select **Starter plan** minimum
4. Worker will start automatically on deploy

**Monitor worker logs:**
- Render Dashboard → ai-bookkeeper-worker → Logs
- Should see: 
  ```
  Worker started
  Listening on queue: ai_bookkeeper
  Connected to Redis: redis://...
  ```

**Test worker is processing jobs:**
```bash
# Run the test script (dry-run if Redis unavailable)
python scripts/test_rq_worker.py

# Expected output:
# ✅ WORKER OK - Job completed successfully!
```

**View job queue:**
```bash
# In Render Shell or locally
rq info -u $REDIS_URL ai_bookkeeper

# Shows: queued, started, finished, failed counts
```

**Troubleshooting:**
- **No jobs processing:** Check worker logs for errors
- **Import errors:** Worker must be able to import job functions
- **Redis connection:** Verify REDIS_URL env var is set
- **Restart worker:** Render Dashboard → Worker → Manual Deploy

### Cron Job (Analytics Rollup)

**Plan Required:** Starter ($7/mo) or higher  
⚠️ **Free tier does not support cron jobs**

**Schedule:** Daily at 02:00 UTC (`0 2 * * *`)

**Command:**
```bash
python jobs/analytics_rollup.py
```

**Enable Cron in Render:**
1. Go to: Dashboard → "New" → "Cron Job"
2. Or: Edit `render.yaml` and apply Blueprint
3. Select **Starter plan** minimum
4. Cron will run on schedule automatically

**View next run time:**
- Render Dashboard → ai-bookkeeper-analytics-cron → Overview
- Shows: Next scheduled run, last run status

**View cron logs:**
- Render Dashboard → ai-bookkeeper-analytics-cron → Logs
- Each run creates a new log entry with timestamp

**Manual trigger (for testing):**
```bash
# In Render Shell (or locally with DATABASE_URL set)
python jobs/analytics_rollup.py

# Expected output:
# Processing events from: 2025-10-12
# Found 47 events
# Generated: reports/analytics/daily_20251012.json
# ✅ Analytics rollup complete

# Verify report created
ls reports/analytics/daily_*.json
```

---

## Troubleshooting

### Build Fails

**Issue:** Docker build times out or fails

**Fix:**
1. Check Render build logs for error
2. Common issues:
   - Missing dependency in `requirements.txt`
   - Dockerfile syntax error
   - Out of disk space (upgrade plan)

**Test locally:**
```bash
docker build -t ai-bookkeeper:test .
docker run -p 10000:10000 ai-bookkeeper:test
curl http://localhost:10000/healthz
```

### Health Check Fails

**Issue:** Service shows "Unhealthy" in Render Dashboard

**Fix:**
1. Check web service logs for errors
2. Verify `/healthz` endpoint works:
   ```bash
   # In Render Shell
   curl http://localhost:10000/healthz
   ```
3. Common causes:
   - Database connection failed (check DATABASE_URL)
   - Port mismatch (should be 10000)
   - Missing environment variable

### Migrations Don't Run

**Issue:** `postDeployCommand` fails

**Fix:**
1. Check deploy logs for migration error
2. Run manually in Render Shell:
   ```bash
   python -m alembic upgrade head
   ```
3. If stuck, check `alembic_version` table:
   ```bash
   psql $DATABASE_URL -c "SELECT * FROM alembic_version;"
   ```

### Worker Not Processing Jobs

**Issue:** Background jobs stuck in queue

**Fix:**
1. Check worker service logs
2. Verify Redis connection:
   ```bash
   # In Render Shell
   python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"
   # Expected: True
   ```
3. Restart worker service in Render Dashboard

### Playwright CI Fails

**Issue:** GitHub Actions workflow errors

**Fix:**
1. Check Actions logs for specific error
2. Common issues:
   - `STAGING_BASE_URL` secret not set
   - Login credentials invalid
   - Manifest file missing
3. Test locally:
   ```bash
   python scripts/capture_screenshots_playwright.py \
     --base-url http://localhost:8000 \
     --manifest artifacts/ui-assessment/screenshot_manifest.json \
     --out artifacts/ui-assessment
   ```

---

## Cost Summary

| Service | Plan | Cost/Month |
|---------|------|------------|
| Web (Starter) | 0.5 GB RAM, 0.5 CPU | $7 |
| Worker (Starter) | 0.5 GB RAM, 0.5 CPU | $7 |
| Cron (Starter) | Pay per run | ~$1 |
| PostgreSQL (Starter) | 1 GB storage | $7 |
| Redis (Starter) | 25 MB memory | $3 |
| **Total** | | **~$25/month** |

**Free Tier:**
- 750 hours/month free for web services
- Covers web + worker (both run 24/7 = 1,440 hours combined)
- First month: ~$15 (Postgres + Redis + overage)

---

## Rollback & Recovery

### Rollback to Previous Deploy

**If new deploy fails or has issues:**

1. **Via Render Dashboard:**
   - Go to: Dashboard → ai-bookkeeper-web → Manual Deploy
   - Click "Redeploy" on a previous successful deploy
   - This restores the previous Docker image

2. **Via Git:**
   ```bash
   # Revert to previous commit
   git revert HEAD
   git push origin main
   
   # Or reset to specific commit
   git reset --hard <commit-sha>
   git push origin main --force  # ⚠️  Use with caution
   ```

3. **Verify rollback:**
   ```bash
   curl https://ai-bookkeeper-app.onrender.com/healthz | jq .git_sha
   # Should show previous commit SHA
   ```

### Database Rollback (Migrations)

**If migration breaks the database:**

1. **Downgrade one version:**
   ```bash
   # In Render Shell
   alembic downgrade -1
   
   # Verify
   alembic current
   ```

2. **Restore from backup:**
   - Render Dashboard → ai-bookkeeper-db → Backups
   - Select backup from before migration
   - Click "Restore" (creates new database)
   - Update DATABASE_URL in web/worker/cron services

3. **Emergency fix:**
   ```bash
   # Skip broken migration and deploy fix
   alembic stamp head
   # Then deploy fixed migration
   ```

### Worker/Cron Rollback

**If worker or cron job fails:**

1. **Disable temporarily:**
   - Render Dashboard → Worker/Cron → Suspend
   - This stops processing but keeps config

2. **Rollback code:**
   - Worker and cron use same Docker image as web
   - Rolling back web deployment rolls back worker/cron too

3. **Clear stuck jobs:**
   ```bash
   # In Python
   from redis import Redis
   from rq import Queue
   
   redis_conn = Redis.from_url(os.getenv('REDIS_URL'))
   queue = Queue('ai_bookkeeper', connection=redis_conn)
   
   # Clear all jobs
   queue.empty()
   
   # Or remove failed jobs only
   from rq.registry import FailedJobRegistry
   registry = FailedJobRegistry(queue=queue)
   for job_id in registry.get_job_ids():
       registry.remove(job_id)
   ```

### Recovery Checklist

After rollback, verify:
- [ ] `/healthz` returns `status: ok`
- [ ] `/readyz` shows correct migration version
- [ ] Worker logs show "Listening on queue"
- [ ] Cron next-run time is scheduled
- [ ] Test login works
- [ ] Test one transaction review flow

---

## Next Steps

1. **✅ Deploy Complete** - Verify all checklist items above
2. **📸 Capture Screenshots** - Run Playwright CI workflow
3. **🧪 Test Key Flows** - Login, review, receipts, analytics
4. **📊 Monitor Metrics** - Check Render Dashboard for performance
5. **🚀 Share URL** - Provide staging URL to PM/CEO for review
6. **📝 Document Changes** - Update team wiki with Render specifics
7. **🔄 Iterate** - Push updates to main, auto-deploys

---

**Documentation:**
- `render.yaml` - Service configuration
- `.env.staging.sample` - Environment reference
- `Dockerfile` - Docker image definition
- `.github/workflows/ui_screenshots.yml` - CI workflow
- `scripts/capture_screenshots_playwright.py` - Screenshot automation

**Support:**
- Render Docs: https://render.com/docs
- Playwright Docs: https://playwright.dev/python/
- GitHub Actions Docs: https://docs.github.com/en/actions

**Last Updated:** 2025-10-11  
**Version:** 1.0 (Production-ready)

