# 🚀 Staging Go-Live Checklist

**Environment:** Render.com  
**App URL:** https://ai-bookkeeper-app.onrender.com  
**Target State:** Pilot-Ready with Safety Guardrails

---

## ✅ Pre-Flight Verification

### 1. Health Checks (5 minutes)
Run the verification script locally:
```bash
chmod +x scripts/verify_staging.sh
./scripts/verify_staging.sh https://ai-bookkeeper-app.onrender.com
```

**Expected Output:**
- ✅ /healthz returns `status: "ok"`
- ✅ /readyz returns `status: "ready"` or `status: "ok"`
- ✅ Database status: `healthy`
- ✅ Alembic version: `008_xero_export` or latest

**Manual Fallback:**
```bash
curl https://ai-bookkeeper-app.onrender.com/healthz | jq .
curl https://ai-bookkeeper-app.onrender.com/readyz | jq .
```

---

### 2. Render Dashboard Screenshots 📸

**Go to:** https://dashboard.render.com/

#### Screenshot 1: Services Overview
- **Navigate to:** Dashboard > Services
- **Capture:** List showing:
  - ✅ `ai-bookkeeper-web` (green/live)
  - ✅ `ai-bookkeeper-db` (PostgreSQL, active)
  - ✅ `ai-bookkeeper-redis` (Redis, active)
- **Save as:** `render-services-overview.png`

#### Screenshot 2: Web Service Details
- **Navigate to:** Dashboard > ai-bookkeeper-web
- **Capture:** Header showing:
  - Service URL: `https://ai-bookkeeper-app.onrender.com`
  - Status: Live (green checkmark)
  - Last deploy time
  - Git commit SHA
- **Save as:** `render-web-service-status.png`

#### Screenshot 3: Environment Variables
- **Navigate to:** Dashboard > ai-bookkeeper-web > Environment
- **Capture:** List showing (with values redacted):
  - ✅ `DATABASE_URL` = ***
  - ✅ `REDIS_URL` = ***
  - ✅ `JWT_SECRET_KEY` = ***
  - ✅ `AUTOPOST_ENABLED` = `false`
  - ✅ `GATING_THRESHOLD` = `0.90`
  - ✅ `UI_ASSESSMENT` = `1`
  - ✅ `OCR_PROVIDER` = `tesseract`
- **Save as:** `render-env-vars.png`

#### Screenshot 4: Recent Logs
- **Navigate to:** Dashboard > ai-bookkeeper-web > Logs
- **Capture:** Last 50 lines showing:
  - Successful startup messages
  - No error tracebacks
  - Health check requests (200 OK)
- **Save as:** `render-logs-healthy.png`

#### Screenshot 5: Deployment History
- **Navigate to:** Dashboard > ai-bookkeeper-web > Events
- **Capture:** Recent deploys showing:
  - Latest deploy: "Deploy live"
  - Commit message
  - Deploy duration
- **Save as:** `render-deploy-history.png`

---

### 3. Database Migrations (2 minutes)

**Access Render Shell:**
1. Go to: Dashboard > ai-bookkeeper-web > Shell tab
2. Wait for shell to connect (~10 seconds)

**Run these commands:**
```bash
# 1. Check current migration
alembic current

# Expected output:
# 008_xero_export (head)

# 2. Verify all migrations applied
alembic history | head -n 20

# Expected: 001 → 002 → ... → 008 all present

# 3. Confirm no pending migrations
alembic upgrade head

# Expected: "INFO  [alembic.runtime.migration] Running upgrade -> 008_xero_export"
# Or: "INFO  [alembic.runtime.migration] Context impl PostgresqlImpl."
#     "INFO  [alembic.runtime.migration] Target database is up to date."
```

**Save output as:** `staging-migrations-verified.txt`

---

### 4. Database Seed Verification (5 minutes)

**Option A: Via GitHub Actions** (Recommended)
1. Go to: https://github.com/ContrejfC/ai-bookkeeper/actions
2. Select workflow: **"Seed Pilots (Staging)"**
3. Click **"Run workflow"**
4. Set inputs:
   - `confirm`: `I_UNDERSTAND`
   - `tenant_prefix`: `pilot`
   - `count`: `3`
5. Click **"Run workflow"** (green button)
6. Wait ~2 minutes for completion
7. Download artifacts: `seed-pilots.zip`
8. Extract and verify:
   - `seed_log.txt` shows 3 tenants created
   - `db_summary.txt` shows row counts > 0

**Option B: Via Render Shell**
```bash
# In Render Shell (Dashboard > ai-bookkeeper-web > Shell)
python scripts/seed_demo_data.py --prefix pilot --count 3
```

---

### 5. Safety Guardrails Verification ⚠️

**Critical Settings - MUST BE TRUE:**

| Setting | Expected Value | Risk if Wrong |
|---------|---------------|---------------|
| `AUTOPOST_ENABLED` | `false` | ⚠️  **CRITICAL** - Will auto-post to GL |
| `GATING_THRESHOLD` | `0.90` | ⚠️  Confidence threshold too low |
| `UI_ASSESSMENT` | `1` | ℹ️ No visible banner (minor) |
| PII Stripping | Enabled | ⚠️  GDPR compliance risk |

**Verify in Render:**
```bash
# In Render Shell:
env | grep -E "(AUTOPOST|GATING|UI_ASSESSMENT)"
```

**Expected Output:**
```
AUTOPOST_ENABLED=false
GATING_THRESHOLD=0.90
UI_ASSESSMENT=1
```

**Verify PII stripping in code:**
```bash
# Check analytics sink has PII stripping enabled:
grep -r "pii.*strip" app/analytics/
```

---

### 6. Test Login & Core Flows (10 minutes)

**Manual UI Testing:**

#### Step 1: Login
- **URL:** https://ai-bookkeeper-app.onrender.com/login
- **Credentials:**
  - Email: `owner@pilot-smb-001.demo`
  - Password: `demo-password-123`
- **Expected:** Redirect to `/review`
- **Screenshot:** `ui-login-success.png`

#### Step 2: Review Dashboard
- **URL:** https://ai-bookkeeper-app.onrender.com/review
- **Expected:**
  - See list of transactions
  - "Propose to GL" button disabled (AUTOPOST=false)
  - UI Assessment banner visible
- **Screenshot:** `ui-review-dashboard.png`

#### Step 3: Receipts
- **URL:** https://ai-bookkeeper-app.onrender.com/receipts
- **Expected:**
  - Receipt list or empty state
  - OCR provider showing: "tesseract"
- **Screenshot:** `ui-receipts.png`

#### Step 4: Analytics
- **URL:** https://ai-bookkeeper-app.onrender.com/analytics
- **Expected:**
  - Metrics dashboard
  - No PII visible in event logs
- **Screenshot:** `ui-analytics.png`

#### Step 5: Rules Console
- **URL:** https://ai-bookkeeper-app.onrender.com/rules
- **Expected:**
  - Rules list
  - Threshold showing: 0.90
- **Screenshot:** `ui-rules-console.png`

---

### 7. GitHub Actions Verification (10 minutes)

**Required Secrets (GitHub → Settings → Secrets → Actions):**
- ✅ `STAGING_BASE_URL` = `https://ai-bookkeeper-app.onrender.com`
- ✅ `STAGING_DATABASE_URL` = `postgresql://...` (from Render)
- ✅ `STAGING_REDIS_URL` = `redis://...` (from Render)

**Run These Workflows:**

#### Workflow 1: Staging Smoke Test
1. Go to: Actions → "Staging Smoke Test"
2. Click "Run workflow"
3. Wait ~30 seconds
4. Download artifact: `staging-smoke.zip`
5. Verify: `staging-healthz.json` and `staging-readyz.json` exist

#### Workflow 2: UI Screenshots (Playwright)
1. Go to: Actions → "UI Screenshots (Playwright)"
2. Click "Run workflow"
3. Wait ~5 minutes (builds Playwright, captures 33 screenshots)
4. Download artifact: `ui-screenshots.zip`
5. Extract and verify: 33 PNG files present

---

### 8. Log Tailing Commands (Render Shell)

**Access Shell:**
Dashboard > ai-bookkeeper-web > Shell

**Useful Commands:**
```bash
# 1. Watch health check requests (live tail)
tail -f /var/log/render/service.log | grep -E "(healthz|readyz)"

# 2. Watch for errors
tail -f /var/log/render/service.log | grep -i error

# 3. Watch Alembic/migration logs
tail -f /var/log/render/service.log | grep -i alembic

# 4. Check recent analytics events
ls -lh reports/analytics/ | tail -n 10

# 5. Verify no PII in analytics logs
tail -n 100 logs/analytics/events_*.jsonl | grep -i "email\|ssn\|phone" | wc -l
# Expected: 0 (no PII should be logged)

# 6. Check OCR status
tesseract --version

# 7. Quick DB row count check
python -c "
from app.db.session import get_db
from app.db import models
db = next(get_db())
print(f'Tenants: {db.query(models.TenantDB).count()}')
print(f'Users: {db.query(models.UserDB).count()}')
print(f'Transactions: {db.query(models.TransactionDB).count()}')
"
```

---

## 🎯 Success Criteria Checklist

Before declaring "GO LIVE":

- [ ] ✅ All health checks return 200 OK
- [ ] ✅ Database migrations at `008_xero_export` (head)
- [ ] ✅ At least 3 pilot tenants seeded with transactions
- [ ] ✅ `AUTOPOST_ENABLED=false` confirmed in Environment
- [ ] ✅ `GATING_THRESHOLD=0.90` confirmed
- [ ] ✅ Login works with demo credentials
- [ ] ✅ Review dashboard shows transactions
- [ ] ✅ No PII detected in analytics logs
- [ ] ✅ OCR (Tesseract) available and functional
- [ ] ✅ GitHub Actions workflows running successfully
- [ ] ✅ UI Screenshots captured (33 files)
- [ ] ✅ No critical errors in recent logs (last 1000 lines)
- [ ] ✅ Response times < 2s for all tested routes

---

## 🚨 Troubleshooting

### Issue: Health checks fail with 503
**Cause:** Service not fully started or database connection issue  
**Fix:**
```bash
# In Render Shell:
curl -v localhost:10000/healthz
# Check DATABASE_URL is set:
echo $DATABASE_URL
```

### Issue: Migrations not at head
**Cause:** `postDeployCommand` didn't run or failed  
**Fix:**
```bash
# In Render Shell:
alembic upgrade head
# Then trigger manual deploy in Render dashboard
```

### Issue: No tenants after seeding
**Cause:** Database URL in GitHub secret is wrong  
**Fix:**
1. Go to Render → ai-bookkeeper-db → Connection String (Internal)
2. Copy the full PostgreSQL URL
3. Update GitHub secret: `STAGING_DATABASE_URL`
4. Re-run "Seed Pilots" workflow

### Issue: Login fails (invalid credentials)
**Cause:** Tenants not seeded yet  
**Fix:** Run seed workflow (see Section 4)

---

## 📦 Artifact Deliverables

**Package these for stakeholders:**

1. **Screenshots** (9 files minimum):
   - `render-services-overview.png`
   - `render-web-service-status.png`
   - `render-env-vars.png`
   - `render-logs-healthy.png`
   - `render-deploy-history.png`
   - `ui-login-success.png`
   - `ui-review-dashboard.png`
   - `ui-receipts.png`
   - `ui-analytics.png`

2. **Verification Logs** (5 files):
   - `staging-migrations-verified.txt`
   - `staging-healthz.json`
   - `staging-readyz.json`
   - `seed_log.txt` (from GitHub Actions artifact)
   - `db_summary.txt` (from GitHub Actions artifact)

3. **Playwright Screenshots** (33 files):
   - Full set from GitHub Actions: `ui-screenshots.zip`

4. **Deployment Report** (`DEPLOYMENT_REPORT.md`):
   - Live URL
   - Database details (host, size, backup status)
   - Redis details
   - Git commit SHA
   - Deploy timestamp
   - Alembic migration head
   - Safety settings summary
   - Known issues (if any)

---

## 🎓 Post-Deployment Notes

**Free Tier Limitations:**
- ⚠️ **Cold Starts:** First request after 15min inactivity takes 50+ seconds
- 💾 **Database:** 256MB limit (PostgreSQL free tier)
- 🔄 **Redis:** 25MB limit (monitor usage)
- 📊 **Logs:** Retained for 7 days only

**Upgrade Triggers:**
- Upgrade to **Starter** ($7/mo) if cold starts impact demos
- Upgrade **Database** ($7/mo) if seed data exceeds 200MB
- Set up **Cron job** for analytics rollup ($1/mo)

**Monitoring:**
- Schedule GitHub Action "Staging Smoke Test" to run every 6 hours (already configured)
- Set up alerting if healthz fails 3 times in a row (manual monitoring for now)

---

## ✅ Sign-Off

**Verified by:** ________________  
**Date:** ________________  
**Staging URL:** https://ai-bookkeeper-app.onrender.com  
**Git SHA:** ________________  
**Ready for Pilots:** YES ☐ / NO ☐

**Notes:**
_________________________________________________________________
_________________________________________________________________


---

## SOC 2 Compliance Verification

**Added:** 2025-10-13 (v0.9.2)

### Backup & Restore Evidence

- [ ] Run backup/restore check script
  ```bash
  ./scripts/backup_restore_check.sh
  ```
- [ ] Verify evidence report: `artifacts/compliance/backup_restore_<timestamp>.txt`
- [ ] Confirm "RESULT: PASS" in report
- [ ] Check row counts match between backup and restore
- [ ] Archive evidence report for auditors

### Access Control Snapshot

- [ ] Generate access snapshot
  ```bash
  python jobs/dump_access_snapshot.py
  ```
- [ ] Review CSV: `reports/compliance/access_snapshot_YYYYMMDD.csv`
- [ ] Verify all users have appropriate roles
- [ ] Confirm autopost settings (false by default)
- [ ] Check gating thresholds (≥0.90)

### Data Retention Policy

- [ ] Run retention report (dry-run)
  ```bash
  python jobs/data_retention.py
  ```
- [ ] Review report: `reports/compliance/data_retention_YYYYMMDD.txt`
- [ ] Verify retention policies:
  - Receipts: 365 days
  - Analytics logs: 365 days
  - Application logs: 30 days

### Security Posture

- [ ] Run SSO/MFA check
  ```bash
  python scripts/check_mfa_sso.py
  ```
- [ ] Verify GitHub org MFA requirement enabled
- [ ] Confirm all team members have MFA enabled
- [ ] Verify Render team SSO/MFA (manual check)

### Change Control

- [ ] PR template present: `.github/pull_request_template.md`
- [ ] PR label gate enabled: `.github/workflows/pr_label_gate.yml`
- [ ] Test PR creation with template
- [ ] Verify gate enforces required sections

### Logging & Monitoring

- [ ] Log drain configured (if using external aggregation)
  - `LOG_DRAIN_URL` set in Render environment
  - `LOG_DRAIN_API_KEY` set (if required)
- [ ] Verify PII redaction in logs
  ```bash
  tail -f logs/app.log | grep REDACTED
  ```
- [ ] Test log shipping to external provider (if configured)

### CI/CD Evidence Collection

- [ ] Weekly access snapshot workflow enabled
- [ ] Monthly data retention workflow scheduled
- [ ] Weekly compliance posture check enabled
- [ ] GitHub secrets configured:
  - `DATABASE_URL`
  - `GITHUB_ORG` (optional)
  - `GITHUB_TOKEN` (optional)
  - `COMPLIANCE_GITHUB_TOKEN` (optional)

### Evidence Archive

- [ ] Create evidence package directory
- [ ] Include access snapshots (last 90 days)
- [ ] Include backup/restore reports (quarterly)
- [ ] Include data retention reports (monthly)
- [ ] Include compliance posture check results
- [ ] Document evidence location for auditors

### Guardrails Verification

- [ ] Confirm AUTOPOST=false by default
- [ ] Verify gating threshold ≥0.90 enforced
- [ ] Test /healthz endpoint (schema unchanged)
- [ ] Test /readyz endpoint (schema unchanged)
- [ ] Verify no PII in logs, exports, or artifacts

**Sign-Off:**
- Date: _________________
- Verified By: _________________
- Evidence Package Location: _________________
