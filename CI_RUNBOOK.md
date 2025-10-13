# CI/CD Runbook - Staging Workflows

**Platform:** GitHub Actions  
**Target:** Render Staging Environment  
**Last Updated:** 2025-10-11

---

## Overview

Two automated workflows for staging verification and data seeding:

1. **Staging Smoke Test** - Automated health checks (every 6 hours)
2. **Seed Pilots (Staging)** - One-off manual seeding of pilot tenants

---

## Required GitHub Secrets

Set these in: **GitHub Repo → Settings → Secrets and variables → Actions**

### For Smoke Test

| Secret Name | Example Value | Required |
|-------------|---------------|----------|
| `STAGING_BASE_URL` | `https://ai-bookkeeper-web.onrender.com` | ✅ Yes |
| `SLACK_WEBHOOK_URL` | `https://hooks.slack.com/services/...` | ⚠️ Optional (alerting) |
| `ALERT_EMAIL` | `ops@company.com` | ⚠️ Optional (alerting) |
| `SMTP_HOST` | `smtp.gmail.com` | ⚠️ Optional (if email alerts) |
| `SMTP_PORT` | `587` | ⚠️ Optional (defaults to 587) |
| `SMTP_USER` | `alerts@company.com` | ⚠️ Required if `ALERT_EMAIL` set |
| `SMTP_PASSWORD` | `app-password` | ⚠️ Required if `ALERT_EMAIL` set |

### For Seed Pilots

| Secret Name | Example Value | Required |
|-------------|---------------|----------|
| `STAGING_DATABASE_URL` | `postgresql://user:pass@host:5432/db` | ✅ Yes |
| `STAGING_REDIS_URL` | `redis://:pass@host:6379/0` | ⚠️ Optional |
| `STAGING_JWT_SECRET_KEY` | `<32-byte-hex-string>` | ⚠️ Optional |

**Important:**
- Never commit secrets to the repository
- Use Render's internal connection strings (not external)
- Ensure `STAGING_DATABASE_URL` is Postgres (not SQLite)
- Do not use production database URLs

---

## Workflow 1: Staging Smoke Test

**File:** `.github/workflows/smoke_staging.yml`

### Purpose
Automated health monitoring of staging environment. Runs every 6 hours and on-demand.

### What It Does
1. ✅ Checks `STAGING_BASE_URL` is configured
2. ✅ Hits `GET /healthz` endpoint
3. ✅ Hits `GET /readyz` endpoint
4. ✅ Validates JSON responses with `jq`
5. ✅ Uploads artifacts (`staging-healthz.json`, `staging-readyz.json`)
6. ✅ Displays results in GitHub Actions summary with badges
7. ✅ **Sends Slack alert on failure** (if `SLACK_WEBHOOK_URL` configured)
8. ✅ **Sends email alert on failure** (if `ALERT_EMAIL` configured)

### Trigger
- **Automatic:** Every 6 hours (0, 6, 12, 18 UTC)
- **Manual:** GitHub → Actions → "Staging Smoke Test" → Run workflow

### Expected Output
```json
// staging-healthz.json
{
  "status": "ok",
  "database_status": "healthy",
  "uptime_seconds": 3600.0
}

// staging-readyz.json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "migrations": "ok",
    "dependencies": "ok"
  }
}
```

### Success Criteria
- Both endpoints return HTTP 200
- JSON is well-formed (valid object)
- `status` field exists in both responses
- Migration info present in readyz (optional)

### Troubleshooting

**Issue:** `STAGING_BASE_URL secret is not set`
```bash
# Fix: Add secret in GitHub
# Repo → Settings → Secrets → Actions → New secret
# Name: STAGING_BASE_URL
# Value: https://your-app.onrender.com
```

**Issue:** `curl failed with exit code 22 (HTTP 404/500)`
```bash
# Fix: Check Render service status
# 1. Verify web service is "Live" in Render Dashboard
# 2. Check logs for errors
# 3. Verify health check endpoint exists
```

**Issue:** `JSON validation failed`
```bash
# Fix: Check endpoint response format
curl https://your-app.onrender.com/healthz | jq .
# Ensure it returns valid JSON with 'status' field
```

### Alerting on Failure

When smoke tests fail, the workflow can send alerts to Slack and/or email. These are **optional** and only activate if secrets are configured.

#### Slack Notifications

**Setup:**
1. Create an Incoming Webhook in your Slack workspace:
   - Go to: https://api.slack.com/messaging/webhooks
   - Select your workspace and channel (e.g., `#ops-alerts`)
   - Copy the webhook URL (looks like: `https://hooks.slack.com/services/T.../B.../...`)

2. Add as GitHub Secret:
   ```
   Name: SLACK_WEBHOOK_URL
   Value: https://hooks.slack.com/services/T.../B.../...
   ```

**What Gets Sent:**
- 🚨 Alert header
- Service name and staging URL
- Healthz and Readyz statuses
- Quick troubleshooting tips
- Links to GitHub Actions run and Render Dashboard

**When It's Sent:**
- Only on workflow failure (healthz or readyz returns non-200 or invalid JSON)
- Gracefully skipped if `SLACK_WEBHOOK_URL` not set (non-blocking)

**Example Message:**
```
🚨 Staging Smoke Test Failed

Service: AI Bookkeeper Staging
Environment: https://ai-bookkeeper-app.onrender.com
Healthz: unavailable
Readyz: unavailable

💡 Quick Tips:
• Check Render logs: Dashboard → ai-bookkeeper-web → Logs
• Verify worker: Dashboard → ai-bookkeeper-worker → Logs
• Database issues: Check Render DB status
• Recent deploy: May be a cold start (wait 60s)

[View Run Logs] [Render Dashboard]
```

#### Email Notifications

**Setup:**
1. Configure SMTP credentials (Gmail example):
   ```
   ALERT_EMAIL=ops@company.com
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=alerts@company.com
   SMTP_PASSWORD=<app-password>  # Generate at myaccount.google.com/apppasswords
   ```

2. Add all as GitHub Secrets

**What Gets Sent:**
- Subject: "🚨 AI Bookkeeper Staging: Smoke Test Failed"
- Body: Staging URL, status summary, link to GitHub Actions run
- Plain text format

**When It's Sent:**
- Only on workflow failure
- Gracefully skipped if `ALERT_EMAIL` not set (non-blocking)

**Test Alerting:**
To test alerts without breaking staging:
1. Temporarily set `STAGING_BASE_URL` to an invalid URL (e.g., `https://invalid-url-test`)
2. Run workflow manually
3. Verify Slack/email received
4. Restore correct `STAGING_BASE_URL`

---

## Workflow 2: Seed Pilots (Staging)

**File:** `.github/workflows/seed_pilots.yml`

### Purpose
One-off seeding of pilot tenants to staging Postgres. Runs manually with safety confirmation.

### What It Does
1. ✅ Requires confirmation (`I_UNDERSTAND`)
2. ✅ Validates `STAGING_DATABASE_URL` (blocks SQLite/prod)
3. ✅ Runs Alembic migrations
4. ✅ Executes seed scripts:
   - `scripts/create_pilot_tenants.py` (or `seed_demo_data.py`)
   - `scripts/test_notifications.py`
   - `scripts/generate_shadow_reports.py`
   - `jobs/analytics_rollup.py`
5. ✅ Generates database summary (table row counts)
6. ✅ Uploads artifacts (logs + reports)

### Trigger
**Manual only:** GitHub → Actions → "Seed Pilots (Staging)" → Run workflow

### Input Parameters

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `confirm` | Must type `I_UNDERSTAND` | (empty) | ✅ Yes |
| `tenant_prefix` | Prefix for tenant IDs | `pilot` | ❌ No |
| `count` | Number of tenants | `3` | ❌ No |

### Usage Example

```bash
# Step 1: Go to GitHub Actions
# Repo → Actions → "Seed Pilots (Staging)"

# Step 2: Click "Run workflow"

# Step 3: Fill inputs
confirm: I_UNDERSTAND
tenant_prefix: pilot
count: 3

# Step 4: Click "Run workflow" button

# Step 5: Wait ~5 minutes for completion

# Step 6: Download "seed-pilots" artifact
# Contains: seed_log.txt, db_summary.txt, reports/
```

### Expected Output

**Artifact Structure:**
```
seed-pilots/
├── seed_log.txt              # Full execution log
├── db_summary.txt            # Table row counts
├── reports/
│   ├── shadow/               # Shadow reports (if generated)
│   │   └── pilot-smb-001_7d.json
│   └── analytics/            # Analytics rollups
│       └── daily_2025-10-11.json
└── exports/                  # CSV exports (if any)
    └── audit_log.csv
```

**seed_log.txt Sample:**
```
============================================
SEED PILOTS - STAGING
============================================
Date: 2025-10-11 20:00:00 UTC
Database: postgresql://bookkeeper:****@dpg-xxx.oregon-postgres.render.com:5432/ai_bookkeeper_staging
Tenant Prefix: pilot
Tenant Count: 3
============================================

📝 Step 1: Creating pilot tenants...
✅ Created tenant: pilot-smb-001
✅ Created tenant: pilot-prof-002
✅ Created tenant: pilot-firm-003

📝 Step 2: Seeding demo data...
✅ Seeded 24 transactions
✅ Seeded 6 receipts

📧 Step 3: Testing notifications...
⚠️  SMTP not configured, skipping email test

📊 Step 4: Generating shadow reports...
✅ Generated 3 shadow reports

📈 Step 5: Running analytics rollup...
✅ Created daily rollup: 2025-10-11

============================================
SEED COMPLETE
============================================
```

**db_summary.txt Sample:**
```
Database: postgresql://bookkeeper:****@dpg-xxx.oregon-postgres.render.com:5432/ai_bookkeeper_staging

Table Row Counts:
----------------------------------------
tenants                              3
users                                6
transactions                        72
journal_entries                     72
rules                               12
audit_log                          156
receipts                            18
receipt_fields                     108
----------------------------------------

Alembic Version: 008_xero_export

✅ Database summary complete
```

### Success Criteria
- Workflow completes without fatal errors
- Seed log shows all 5 steps executed
- Database summary shows non-zero row counts
- At least 3 tenants created
- All tenants have `AUTOPOST=false` and `threshold=0.90`

### Safety Guards

**Guard 1: Confirmation Required**
```
❌ You must type I_UNDERSTAND to run this workflow.
```
**Fix:** Type exactly `I_UNDERSTAND` in the confirm input

**Guard 2: DATABASE_URL Not Set**
```
❌ STAGING_DATABASE_URL secret is not set.
```
**Fix:** Add secret in GitHub → Settings → Secrets

**Guard 3: SQLite Detected**
```
❌ Refusing to run against sqlite.
```
**Fix:** Use Postgres connection string (starts with `postgresql://`)

**Guard 4: Production URL Detected**
```
❌ DATABASE_URL contains 'prod' — refusing to run.
```
**Fix:** Use staging database URL only (should not contain "prod" or "production")

### Troubleshooting

**Issue:** Seed scripts fail with import errors
```bash
# Fix: Ensure all dependencies in requirements.txt
# Workflow installs from requirements.txt automatically
# Check workflow logs for specific missing package
```

**Issue:** Database connection fails
```bash
# Fix: Verify DATABASE_URL is correct
# 1. Copy from Render Dashboard → Postgres → Internal Connection String
# 2. Ensure format: postgresql://user:pass@host:port/dbname
# 3. Test connection locally:
psql "$STAGING_DATABASE_URL" -c "SELECT 1;"
```

**Issue:** Migrations fail
```bash
# Fix: Check Alembic version
# 1. Verify migrations exist in alembic/versions/
# 2. Check current version:
python -m alembic current
# 3. Manually apply if needed:
python -m alembic upgrade head
```

---

## First Run Order (Recommended)

### Initial Setup (One-time)

1. **Deploy to Render**
   - Push code to GitHub
   - Create Postgres + Redis in Render
   - Deploy from Blueprint (`render.yaml`)
   - Set environment secrets in Render Dashboard

2. **Configure GitHub Secrets**
   ```bash
   # Add these secrets:
   STAGING_BASE_URL=https://your-app.onrender.com
   STAGING_DATABASE_URL=postgresql://...  (from Render)
   STAGING_REDIS_URL=redis://...          (from Render)
   STAGING_JWT_SECRET_KEY=$(openssl rand -hex 32)
   ```

3. **Verify Deployment**
   ```bash
   # Manually test endpoints
   curl https://your-app.onrender.com/healthz
   curl https://your-app.onrender.com/readyz
   ```

### Workflow Execution Order

#### Step 1: Run Smoke Test (First)
```bash
# GitHub → Actions → "Staging Smoke Test" → Run workflow
# Expected: ✅ Both health checks pass
# Download artifact: staging-smoke
```

#### Step 2: Seed Pilots (Second)
```bash
# GitHub → Actions → "Seed Pilots (Staging)" → Run workflow
# Inputs:
#   confirm: I_UNDERSTAND
#   tenant_prefix: pilot
#   count: 3
# Expected: ✅ 3 tenants created, data seeded
# Download artifact: seed-pilots
```

#### Step 3: Run Smoke Test Again (Verify)
```bash
# GitHub → Actions → "Staging Smoke Test" → Run workflow
# Expected: ✅ Health checks still pass with seeded data
```

#### Step 4: Trigger Screenshot CI
```bash
# GitHub → Actions → "UI Screenshots (Playwright)" → Run workflow
# Expected: ✅ 33 screenshots captured
# Download artifact: ui-screenshots
```

---

## Monitoring & Maintenance

### Smoke Test Schedule
- Runs **every 6 hours** automatically
- Check GitHub Actions tab for results
- Failed runs send GitHub notifications (if configured)

### Manual Triggers
Both workflows support manual trigger via `workflow_dispatch`:
```bash
# GitHub → Actions → [Workflow Name] → Run workflow
```

### Artifact Retention
- Artifacts kept for **30 days**
- Download before expiration if needed for records
- Older artifacts automatically deleted

### When to Re-Seed
Re-run "Seed Pilots" workflow if:
- Testing a new feature requiring fresh data
- Database was reset/migrated
- Pilot tenant data became corrupted
- Need to test with different tenant configurations

---

## Common Scenarios

### Scenario 1: New Migration Deployed
```bash
# 1. Deploy new code to Render (with migration)
git push origin main

# 2. Wait for Render deploy (auto-runs postDeployCommand)

# 3. Verify migration via Smoke Test
# GitHub → Actions → "Staging Smoke Test" → Run

# 4. Check readyz response for new migration version
```

### Scenario 2: Reset Staging Data
```bash
# 1. Drop and recreate database in Render Dashboard
# OR manually: DROP SCHEMA public CASCADE; CREATE SCHEMA public;

# 2. Trigger deploy to run migrations
# Render Dashboard → Manual Deploy

# 3. Seed fresh data
# GitHub → Actions → "Seed Pilots" → Run (I_UNDERSTAND)

# 4. Verify
# GitHub → Actions → "Staging Smoke Test" → Run
```

### Scenario 3: Debug Failed Seed
```bash
# 1. Download seed-pilots artifact
# GitHub → Actions → Failed run → Artifacts → seed-pilots

# 2. Check seed_log.txt for errors

# 3. Identify failing script (e.g., create_pilot_tenants.py)

# 4. Fix script locally and test:
export DATABASE_URL="postgresql://..."
python scripts/create_pilot_tenants.py

# 5. Commit fix and re-run workflow
```

---

## First-Hour Watch (Post-Deploy Checklist)

After merging and deploying to Render, monitor these indicators for the first hour:

### 1. Check Web Service Logs
```bash
# Render Dashboard → ai-bookkeeper-web → Logs
# Look for:
✅ "Application startup complete"
✅ "Uvicorn running on http://0.0.0.0:10000"
✅ "/healthz" requests returning 200
❌ Any ERROR or CRITICAL log lines
```

### 2. Check Worker Service Logs
```bash
# Render Dashboard → ai-bookkeeper-worker → Logs
# Look for:
✅ "Worker started"
✅ "Listening on queue: ai_bookkeeper"
✅ "Connected to Redis"
❌ Connection errors or import failures
```

### 3. Check Cron Service Status
```bash
# Render Dashboard → ai-bookkeeper-analytics-cron → Overview
# Verify:
✅ "Next run" shows 02:00 UTC (or next scheduled time)
✅ No failed runs in history
✅ Service status: "Live"
```

### 4. Run Smoke Test
```bash
# GitHub → Actions → "Staging Smoke Test" → Run workflow
# Manual trigger to verify immediately
# Expected artifacts: staging-healthz.json, staging-readyz.json
# Verify: Both show status: "ok" / "ready"
```

### 5. Verify Health Endpoints
```bash
# Direct curl (replace with your Render URL)
curl https://ai-bookkeeper-app.onrender.com/healthz | jq .
# Expected: {"status":"ok", "database_status":"healthy", ...}

curl https://ai-bookkeeper-app.onrender.com/readyz | jq .
# Expected: {"status":"ready", "checks":{"database":"ok","migrations":"ok"}}
```

### 6. Test Legal Pages (No Auth)
```bash
# Visit in browser (should load without login):
https://ai-bookkeeper-app.onrender.com/legal/terms
https://ai-bookkeeper-app.onrender.com/legal/privacy
https://ai-bookkeeper-app.onrender.com/support

# Verify: "Template Only" banner visible, footer links present
```

### 7. Re-run Seed Pilots (If Needed)
```bash
# Only if database was wiped or first-time deploy
# GitHub → Actions → "Seed Pilots (Staging)" → Run workflow
# Input: I_UNDERSTAND
# Check artifacts: seed_log.txt confirms tenants created
```

### Quick Reference URLs
| Check | URL |
|-------|-----|
| Render Dashboard | https://dashboard.render.com |
| Web Logs | Dashboard → ai-bookkeeper-web → Logs |
| Worker Logs | Dashboard → ai-bookkeeper-worker → Logs |
| Cron Status | Dashboard → ai-bookkeeper-analytics-cron → Overview |
| Healthz | `https://YOUR-APP.onrender.com/healthz` |
| Readyz | `https://YOUR-APP.onrender.com/readyz` |
| GitHub Actions | `https://github.com/YOUR_ORG/ai-bookkeeper/actions` |

### Alert Verification (If Configured)
```bash
# Test Slack/Email alerts:
# 1. Temporarily set STAGING_BASE_URL to invalid URL in GitHub secrets
# 2. Run smoke test workflow
# 3. Check Slack channel or email inbox for alert
# 4. Restore correct STAGING_BASE_URL
```

---

## Links to Workflows

Once pushed to GitHub, access workflows at:

- **Staging Smoke Test:**  
  `https://github.com/YOUR_ORG/ai-bookkeeper/actions/workflows/smoke_staging.yml`

- **Seed Pilots (Staging):**  
  `https://github.com/YOUR_ORG/ai-bookkeeper/actions/workflows/seed_pilots.yml`

- **UI Screenshots (Playwright):**  
  `https://github.com/YOUR_ORG/ai-bookkeeper/actions/workflows/ui_screenshots.yml`

---

## Security Notes

✅ **Passwords redacted** in logs (replaced with `****`)  
✅ **No secrets printed** in workflow output  
✅ **Safety guards** block SQLite and production databases  
✅ **Confirmation required** for destructive operations  
✅ **AUTOPOST=false** enforced in seed environment  

⚠️ **Do not:**
- Commit secrets to repository
- Use production database URLs
- Share artifact URLs publicly (may contain data)
- Run seed workflow against production

---

## Support

**Issues:**
- Check GitHub Actions logs for detailed error messages
- Review Render service logs for deployment issues
- Consult RENDER_DEPLOYMENT.md for deployment troubleshooting

**Questions:**
- See RENDER_DEPLOYMENT.md for Render-specific help
- See STAGING_VERIFICATION_GUIDE.md for post-deploy verification
- Check test files in `tests/` for script usage examples

---

**Last Updated:** 2025-10-11  
**Version:** 1.0  
**Status:** ✅ Production-ready


---

## SOC 2 Compliance Workflows

**Added:** 2025-10-13 (v0.9.2)

### Overview

Automated compliance workflows for SOC 2 evidence generation:
1. **Weekly Access Snapshot** - User/tenant access reports
2. **Backup & Restore Check** - Database backup verification
3. **Data Retention Report** - Monthly retention policy execution
4. **Compliance Posture Check** - SSO/MFA verification
5. **PR Label Gate** - Change control enforcement

### Workflow 1: Weekly Access Snapshot

**Schedule:** Every Sunday at 02:00 UTC  
**File:** `.github/workflows/compliance_weekly.yml`

**What It Does:**
- Generates snapshot of all app users, roles, and tenant assignments
- Exports tenant config flags (autopost_enabled, threshold)
- Optionally includes GitHub org members and Render team
- Saves artifacts: `access_snapshot_YYYYMMDD.{csv,json}`

**Required Secrets:**
- `DATABASE_URL` (optional, defaults to SQLite)

**Optional Secrets:**
- `GITHUB_ORG` - GitHub organization name
- `GITHUB_TOKEN` - GitHub API token (org:read scope)
- `RENDER_API_KEY` - Render API key

**Manual Trigger:**
```bash
gh workflow run compliance_weekly.yml
```

**Download Artifacts:**
```bash
gh run download <run-id> -n access-snapshot-<number>
```

**Use Case:**
Quarterly access reviews for auditors. CSV format for easy spreadsheet review.

### Workflow 2: Backup & Restore Check

**Schedule:** Manual only  
**File:** `.github/workflows/backup_restore_check.yml`

**What It Does:**
- Performs database backup (pg_dump or SQLite dump)
- Restores to temporary schema/database
- Verifies data integrity (row counts)
- Runs smoke test (/healthz)
- Generates evidence report with PASS/FAIL status

**Required Secrets:**
- `DATABASE_URL` - Database connection string

**Manual Trigger:**
```bash
gh workflow run backup_restore_check.yml
```

**Download Evidence:**
```bash
gh run download <run-id> -n backup-evidence-<number>
```

**Use Case:**
Disaster recovery readiness verification. Provide evidence report to auditors quarterly.

### Workflow 3: Data Retention Report

**Schedule:** Monthly (1st of month at 03:00 UTC)  
**File:** `.github/workflows/data_retention_report.yml`

**What It Does:**
- Scans receipts, analytics logs, app logs
- Identifies files older than retention periods
- DRY-RUN by default (reports but doesn't delete)
- Generates report: `data_retention_YYYYMMDD.txt`

**Retention Policies:**
- Receipts: 365 days (default)
- Analytics logs: 365 days (default)
- Application logs: 30 days (default)

**Manual Trigger (dry-run):**
```bash
gh workflow run data_retention_report.yml
```

**Manual Trigger (live delete):**
```bash
gh workflow run data_retention_report.yml -f delete_enabled=true
```

**Download Report:**
```bash
gh run download <run-id> -n data-retention-report-<number>
```

**Use Case:**
Evidence of data retention policy enforcement. Provide monthly reports to auditors.

### Workflow 4: Compliance Posture Check

**Schedule:** Every Monday at 08:00 UTC  
**File:** `.github/workflows/compliance_posture_check.yml`

**What It Does:**
- Checks GitHub org MFA requirement
- Verifies all GitHub members have MFA enabled
- Provides guidance for Render team SSO/MFA
- Fails workflow if MFA not enforced

**Required Secrets:**
- `COMPLIANCE_GITHUB_ORG` - GitHub organization name
- `COMPLIANCE_GITHUB_TOKEN` - GitHub token (admin:org scope)

**Optional Secrets:**
- `RENDER_API_KEY` - Render API key (for future SSO checks)

**Manual Trigger:**
```bash
gh workflow run compliance_posture_check.yml
```

**Download Log:**
```bash
gh run download <run-id> -n compliance-posture-<number>
```

**Use Case:**
Continuous security posture monitoring. Evidence of MFA enforcement for auditors.

### Workflow 5: PR Label Gate

**Trigger:** On PR open, edit, label change  
**File:** `.github/workflows/pr_label_gate.yml`

**What It Does:**
- Verifies PR body contains linked issue/ticket URL
- Requires label `has-ticket` or `change-control-exempt`
- Checks for required template sections (Risk, Rollback, Tests)
- Logs all PRs and exemptions for audit trail

**How to Pass PR Checks:**

1. **Use PR template** (auto-populated when creating PR)
2. **Fill required sections:**
   - Linked Issue/Ticket URL (must include actual URL)
   - Risk/Impact Assessment
   - Rollback Plan
   - Tests/Evidence
3. **Add label:** `has-ticket` (or `change-control-exempt` for hotfixes)

**Exemptions:**
- Add label `change-control-exempt` for emergency hotfixes
- All exemptions are logged in workflow output for audit trail
- Use sparingly (auditors will review exemption logs)

**Troubleshooting:**
- ❌ "PR must include linked issue URL" → Add full URL to "Issue URL:" section
- ❌ "PR must have label has-ticket" → Add label in PR sidebar
- ❌ "PR template missing required sections" → Ensure all headers present

### Weekly Access Review Process

**Cadence:** Weekly (or as required by audit schedule)

**Steps:**
1. **Download Snapshot:**
   ```bash
   gh run list --workflow=compliance_weekly.yml --limit 1
   gh run download <run-id> -n access-snapshot-<number>
   ```

2. **Review CSV:**
   - Open `access_snapshot_YYYYMMDD.csv` in spreadsheet
   - Filter by section: `app_user`, `tenant_setting`, `github_member`
   - Verify:
     - All users have appropriate roles
     - No unexpected tenant assignments
     - Autopost settings are correct (false by default)
     - Thresholds are ≥0.90

3. **Document Review:**
   - Create issue: "Weekly Access Review - YYYY-MM-DD"
   - Note any anomalies or required actions
   - Close with "Reviewed, no issues" or action items

4. **Quarterly Sign-Off:**
   - Compile last 12 weekly reviews
   - Provide to auditors as evidence package
   - Include CSV snapshots + review issue links

### Backup/Restore Quarterly Verification

**Cadence:** Quarterly

**Steps:**
1. **Trigger Check:**
   ```bash
   gh workflow run backup_restore_check.yml
   ```

2. **Wait for Completion:**
   ```bash
   gh run watch
   ```

3. **Download Evidence:**
   ```bash
   gh run download <run-id> -n backup-evidence-<number>
   ```

4. **Review Report:**
   - Open `backup_restore_<timestamp>.txt`
   - Verify "RESULT: PASS"
   - Check row counts match between backup and restore
   - Confirm smoke test (/healthz) passed

5. **Archive for Auditors:**
   - Save report with timestamp
   - Add to quarterly evidence package

### Required GitHub Secrets (Compliance)

| Secret Name | Purpose | Required |
|-------------|---------|----------|
| `DATABASE_URL` | Database connection for backups | ✅ Yes |
| `GITHUB_ORG` | GitHub org for access snapshots | ⚠️ Optional |
| `GITHUB_TOKEN` | GitHub API token (org:read) | ⚠️ Optional |
| `COMPLIANCE_GITHUB_ORG` | GitHub org for posture checks | ⚠️ Optional |
| `COMPLIANCE_GITHUB_TOKEN` | GitHub token (admin:org) | ⚠️ Optional |
| `RENDER_API_KEY` | Render API for team access | ⚠️ Optional |

**Notes:**
- All workflows degrade gracefully if optional secrets are missing
- `GITHUB_TOKEN` requires `org:read` scope (for member lists)
- `COMPLIANCE_GITHUB_TOKEN` requires `admin:org` scope (for MFA checks)
- Never use personal access tokens with broad permissions

### Troubleshooting

**Issue:** Access snapshot shows "SKIPPED: no creds"
- **Fix:** Add `GITHUB_ORG` and `GITHUB_TOKEN` secrets

**Issue:** Backup/restore fails with "pg_dump not found"
- **Fix:** Workflow auto-installs postgres-client; check logs for errors

**Issue:** Data retention report shows 0 files scanned
- **Fix:** Directories may not exist; run locally to populate

**Issue:** Posture check fails with 403
- **Fix:** Ensure `COMPLIANCE_GITHUB_TOKEN` has `admin:org` scope

**Issue:** PR gate fails even with ticket URL
- **Fix:** Ensure URL is in "Issue URL:" section (not just PR description)
- **Fix:** Add label `has-ticket` via PR sidebar
