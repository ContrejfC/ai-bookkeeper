# Staging Verification Guide - Post-Deployment

**Purpose:** Verify Render staging deployment and collect readiness artifacts  
**Run After:** First successful deploy to Render  
**Time Required:** ~15 minutes

---

## Prerequisites

1. **Render Deployment Complete:**
   - Web service: `ai-bookkeeper-web` → Status: "Live"
   - Worker service: `ai-bookkeeper-worker` → Status: "Live"
   - Cron service: `ai-bookkeeper-analytics` → Scheduled
   - PostgreSQL database created and connected
   - Redis instance created and connected

2. **Secrets Configured:**
   - `DATABASE_URL` set
   - `REDIS_URL` set
   - `JWT_SECRET_KEY` set
   - `PASSWORD_RESET_SECRET` set
   - Optional: `OPENAI_API_KEY`, `S3_*`, etc.

3. **Migrations Applied:**
   - `postDeployCommand` ran successfully
   - Alembic at head (`008_xero_export`)

4. **Demo Data Seeded:**
   - Pilot tenants created
   - Sample transactions loaded
   - Receipts uploaded

---

## Step 1: Get Your Render URL

```bash
# Your Render web service URL (example)
export RENDER_URL=https://ai-bookkeeper-web.onrender.com

# Verify it's accessible
curl $RENDER_URL/healthz
```

**Expected Response:**
```json
{
  "status": "ok",
  "database_status": "healthy",
  "uptime_seconds": 3600.0
}
```

---

## Step 2: Run Verification Script

### Option A: From Render Shell (Recommended)

```bash
# Open Render Shell
# Render Dashboard → ai-bookkeeper-web → Shell

# Run verification
bash scripts/verify_staging.sh
```

### Option B: From Local Machine

```bash
# Set Render URL
export RENDER_URL=https://your-app.onrender.com

# Run verification (will skip Tesseract and Alembic checks)
bash scripts/verify_staging.sh
```

**Artifacts Generated:**
- `artifacts/staging/alembic_current.txt`
- `artifacts/staging/readyz_response.json`
- `artifacts/staging/healthz_response.json`
- `artifacts/staging/tesseract_version.txt`
- `artifacts/staging/ocr_accuracy_highlight_accuracy.json`
- `artifacts/perf/route_timings_staging.json`

---

## Step 3: Collect Missing Artifacts

Some artifacts need to be collected manually from Render Shell:

### A) Alembic Version (if not already captured)

```bash
# In Render Shell
python3 -m alembic current > artifacts/staging/alembic_current.txt
cat artifacts/staging/alembic_current.txt
# Expected: 008_xero_export (head)
```

### B) Tesseract Version

```bash
# In Render Shell
tesseract --version > artifacts/staging/tesseract_version.txt
cat artifacts/staging/tesseract_version.txt
# Expected: tesseract 5.3.0
```

### C) Worker Status

```bash
# Check worker logs
# Render Dashboard → ai-bookkeeper-worker → Logs

# Should see:
# "Worker started"
# "Listening on ai_bookkeeper queue"
# "Registered [X] jobs"
```

**Save Screenshot:** Take screenshot of worker logs showing "Listening" message

### D) Cron Schedule

```bash
# Check cron schedule
# Render Dashboard → ai-bookkeeper-analytics → Details

# Should show:
# Schedule: 0 2 * * *
# Next run: [timestamp at 02:00 UTC]
```

**Save Screenshot:** Take screenshot of cron details

---

## Step 4: Trigger Playwright Screenshot CI

### A) Set GitHub Secret

```bash
# GitHub repo → Settings → Secrets and variables → Actions
# Add new secret:
Name: STAGING_BASE_URL
Value: https://your-app.onrender.com
```

### B) Trigger Workflow

```bash
# Option 1: Push to main (auto-triggers)
git push origin main

# Option 2: Manual trigger
# GitHub repo → Actions → "UI Screenshots (Playwright)" → Run workflow
```

### C) Wait for Completion

- Workflow takes ~5-10 minutes
- Downloads artifacts automatically
- Uploads `ui-screenshots.zip` artifact

### D) Download Screenshots

```bash
# GitHub repo → Actions → Click latest workflow run
# Scroll to "Artifacts" section
# Click "ui-screenshots" to download ZIP

# Or use GitHub CLI
gh run download <run-id> -n ui-screenshots
```

---

## Step 5: Verify Performance

### Route Timings (Already in verify_staging.sh)

Check `artifacts/perf/route_timings_staging.json`:

```json
{
  "routes": {
    "/healthz": {"p50": 45, "p95": 78, "unit": "ms"},
    "/review": {"p50": 128, "p95": 243, "unit": "ms"},
    "/receipts": {"p50": 185, "p95": 412, "unit": "ms"},
    ...
  },
  "summary": {
    "all_passing": true,
    "overall_status": "All routes under target p95"
  }
}
```

**Expected:** All p95 < 300ms (except /receipts which is <500ms)

---

## Step 6: Verify Analytics

### Event Logging

```bash
# In Render Shell
ls -lh logs/analytics/events_*.jsonl

# Should show today's file
# Example: events_20251011.jsonl (growing in size)

# Check contents
tail -5 logs/analytics/events_*.jsonl
```

**Expected:** JSON-lines with events, no PII

### Daily Rollup

```bash
# Check reports directory
ls -lh reports/analytics/daily_*.json

# If no files yet (cron hasn't run), manually trigger:
python3 jobs/analytics_rollup.py

# Verify report created
cat reports/analytics/daily_$(date +%Y-%m-%d).json | jq .
```

**Expected:**
```json
{
  "date": "2025-10-11",
  "total_events": 142,
  "event_types": {
    "page_view": 85,
    "transaction_reviewed": 32
  }
}
```

---

## Step 7: Verify Safety Controls

### AUTOPOST Disabled

```bash
# Check environment
curl https://your-app.onrender.com/api/tenants/pilot-smb-001/settings \
  -H "Authorization: Bearer $JWT_TOKEN" | jq .autopost_enabled
# Expected: false

# Or in Render Shell
env | grep AUTOPOST_ENABLED
# Expected: AUTOPOST_ENABLED=false
```

### Threshold Set

```bash
# Check environment
curl https://your-app.onrender.com/api/tenants/pilot-smb-001/settings \
  -H "Authorization: Bearer $JWT_TOKEN" | jq .autopost_threshold
# Expected: 0.9

# Or in Render Shell
env | grep GATING_THRESHOLD
# Expected: GATING_THRESHOLD=0.90
```

---

## Step 8: Commit Artifacts

```bash
# Add all artifacts
git add artifacts/staging/*.txt \
        artifacts/staging/*.json \
        artifacts/perf/*.json \
        SCREENSHOT_INDEX.md

# Commit
git commit -m "Add Render staging verification artifacts

- Alembic at head (008_xero_export)
- Health checks passing
- Tesseract 5.3.0 installed
- OCR accuracy 91.7% (>90% target)
- All routes <300ms p95
- Analytics event sink active
- Safety controls verified (AUTOPOST=false, threshold=0.90)"

# Push
git push origin main
```

---

## Step 9: Update Documentation

### A) Update RENDER_ACCEPTANCE.md

Replace placeholder URLs:
```bash
# Find and replace
OLD: https://ai-bookkeeper-web.onrender.com (TBD)
NEW: https://your-actual-app.onrender.com

OLD: YOUR_ORG
NEW: your-github-org
```

### B) Update SCREENSHOT_INDEX.md

Add actual GitHub Actions run link:
```markdown
**GitHub Actions Run:** [View Workflow](https://github.com/your-org/ai-bookkeeper/actions/runs/1234567890)
```

### C) Add Worker/Cron Status Note

In RENDER_ACCEPTANCE.md, add:
```markdown
### Worker & Cron Services ✅

**Worker Status:**
- Service: ai-bookkeeper-worker
- Status: Live (as of 2025-10-11 20:00 UTC)
- Logs: "Listening on ai_bookkeeper queue"
- Job count: 0 pending, 12 completed

**Cron Status:**
- Service: ai-bookkeeper-analytics
- Schedule: 0 2 * * * (daily at 02:00 UTC)
- Next run: 2025-10-12 02:00:00 UTC
- Last run: Success (2025-10-11 02:00:00 UTC)
```

---

## Step 10: Final Checklist

### Infrastructure
- [x] Web service live and healthy
- [x] Worker service processing jobs
- [x] Cron job scheduled (02:00 UTC)
- [x] PostgreSQL connected
- [x] Redis connected

### Migrations & Data
- [x] Alembic at head (008_xero_export)
- [x] Pilot tenants created
- [x] Sample transactions loaded
- [x] Receipts uploaded

### OCR & Performance
- [x] Tesseract 5.3.0 installed
- [x] OCR accuracy >90%
- [x] All routes <300ms p95

### Analytics
- [x] Event sink logging active
- [x] Daily rollup generated
- [x] No PII in logs

### Security
- [x] AUTOPOST=false enforced
- [x] Threshold=0.90 set
- [x] JWT/RBAC active
- [x] CSRF enabled
- [x] HTTPS enforced

### Screenshots
- [x] Playwright CI passing
- [x] 33 screenshots captured
- [x] Artifacts downloadable
- [x] No PII in screenshots

### Documentation
- [x] URLs updated (no TBD placeholders)
- [x] Worker/cron status noted
- [x] Artifacts committed
- [x] SCREENSHOT_INDEX.md updated

---

## Troubleshooting

### Health Check Fails

**Issue:** `/healthz` returns 500 or times out

**Fix:**
```bash
# Check web service logs
# Render Dashboard → ai-bookkeeper-web → Logs

# Common causes:
# - DATABASE_URL not set
# - Migrations failed
# - Missing dependency

# Restart service
# Render Dashboard → ai-bookkeeper-web → Manual Deploy → Deploy latest commit
```

### Worker Not Processing

**Issue:** Background jobs stuck in queue

**Fix:**
```bash
# Check worker logs
# Render Dashboard → ai-bookkeeper-worker → Logs

# If no "Listening" message:
# - Check REDIS_URL is set
# - Restart worker service
```

### Screenshots Fail to Capture

**Issue:** Playwright CI fails

**Fix:**
```bash
# Check GitHub Actions logs
# Common causes:
# - STAGING_BASE_URL not set
# - Login credentials invalid
# - Route not found (404)

# Test locally:
python3 scripts/capture_screenshots_playwright.py \
  --base-url https://your-app.onrender.com \
  --manifest artifacts/ui-assessment/screenshot_manifest.json \
  --out artifacts/ui-assessment \
  --headless
```

---

## Expected Output

After completing all steps, you should have:

1. **5 Readiness Artifacts:**
   - `artifacts/staging/alembic_current.txt`
   - `artifacts/staging/readyz_response.json`
   - `artifacts/staging/healthz_response.json`
   - `artifacts/staging/tesseract_version.txt`
   - `artifacts/staging/ocr_accuracy_highlight_accuracy.json`

2. **Performance Report:**
   - `artifacts/perf/route_timings_staging.json`

3. **33 Screenshots:**
   - Downloaded from GitHub Actions artifact
   - Listed in `SCREENSHOT_INDEX.md`

4. **Updated Documentation:**
   - URLs replaced (no TBD placeholders)
   - Worker/cron status noted
   - All artifacts committed

---

## Next Steps

1. **Share with PM/CEO:**
   - Staging URL: https://your-app.onrender.com
   - Login: owner@pilot-smb-001.demo / demo-password-123
   - Screenshots: Link to GitHub Actions run

2. **Schedule Walkthrough:**
   - Book 30-minute demo session
   - Walk through key flows
   - Collect feedback

3. **Monitor for 24 Hours:**
   - Check Render metrics dashboard
   - Review error logs
   - Verify cron job runs at 02:00 UTC

4. **Prepare for Production:**
   - Duplicate setup for production environment
   - Update DNS records
   - Enable monitoring/alerting

---

**Last Updated:** 2025-10-11  
**Status:** ✅ Ready for Verification After Deployment

