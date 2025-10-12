# Release v0.9.1: Cloud Upgrade + UX Polish + Legal Pages

**Branch:** `feature/cloud-upgrade-ux-legal` → `main`  
**Target Deploy:** Render staging  
**Risk Level:** 🟡 Medium (new services, no code changes to core logic)

---

## 📋 Summary

This release prepares AI Bookkeeper for pilot deployment by adding:
- **Render worker + cron services** for background processing
- **Slack/email alerting** on staging health check failures
- **Legal pages** (Terms, Privacy, DPA, Support) with GDPR compliance templates
- **UX accessibility improvements** (tooltips, toasts, button sizing)
- **Comprehensive documentation** for deployment and rollback

**No changes to safety guardrails:** AUTOPOST=false, threshold=0.90 maintained.

---

## 🎯 What Changed

### A) Render Infrastructure (Worker + Cron)
- **New services** in `render.yaml`:
  - `ai-bookkeeper-worker` (RQ background jobs) — **Requires Starter plan ($7/mo)**
  - `ai-bookkeeper-analytics-cron` (daily rollup @ 02:00 UTC) — **Requires Starter plan ($7/mo)**
- **Migration commands** added: `preDeployCommand: "alembic current || true"` and `postDeployCommand: "alembic upgrade head"`
- **Dry-run mode** in `scripts/test_rq_worker.py` for free-tier compatibility

### B) Alerting (Slack + Email)
- **Enhanced smoke tests** (`.github/workflows/smoke_staging.yml`):
  - Sends Slack webhook on failure (if `SLACK_WEBHOOK_URL` configured)
  - Sends email alert on failure (if `ALERT_EMAIL` + SMTP configured)
  - Graceful degradation if secrets missing
  - Status badges in GitHub Actions summary

### C) Legal & Support Pages
- **4 new public routes** (no auth required):
  - `/legal/terms` — Terms of Service
  - `/legal/privacy` — Privacy Policy
  - `/legal/dpa` — Data Processing Agreement (GDPR Article 28 template)
  - `/support` — Support & Help Center
- **Footer links** visible site-wide (Terms | Privacy | DPA | Support | Health | Readiness)
- **Templates** include "not legal advice" disclaimers and `noindex` meta tags
- **17 new tests** in `tests/test_legal_support_pages.py` (all passing ✅)

### D) UX Polish & Accessibility
- **Button sizing**: `.btn-md` (44x44px) and `.btn-lg` (48x48px) CSS classes for WCAG 2.1 AA
- **Tooltips**: `app/ui/static/tooltips.js` (keyboard accessible, `aria-describedby`, ESC to close)
- **Toasts**: `app/ui/static/toast.js` (queued, `aria-live`, 3.5s/6s duration)
- **Site-wide includes** in `base.html`

### E) Documentation
- **Updated**:
  - `RENDER_DEPLOYMENT.md` — Rollback procedures, worker/cron docs
  - `CI_RUNBOOK.md` — Alerting setup, "First-Hour Watch" checklist
  - `UI_ISSUES.md` — Marked 4 items as fixed
  - `CHANGELOG.md` — Full [0.9.1] entry
- **Added**:
  - `app/VERSION` — Single source of truth: `0.9.1`
  - `FEATURE_COMPLETE_SUMMARY.md` — Implementation summary
  - `RELEASE_NOTES_v0.9.1.md` — Executive summary

---

## 📸 Screenshots

<!-- TODO: Add screenshots after deploy -->
- [ ] `/legal/terms` with "Template Only" banner
- [ ] `/support` page with support email and export link
- [ ] Footer showing Terms | Privacy | DPA | Support links
- [ ] Toast notification example (success, error, warning, info)
- [ ] Render Dashboard showing web + worker + cron services

---

## ⚠️ Risk Assessment

### Medium Risk Items:
1. **Worker/Cron services** require Render Starter plan ($14/mo total)
   - **Mitigation**: Free tier gracefully degrades (dry-run mode)
   - **Rollback**: Suspend worker/cron in Render Dashboard

2. **New public routes** (legal/support pages)
   - **Mitigation**: No auth bypass (routes are intentionally public)
   - **Rollback**: Routes can be disabled by removing from `app/ui/routes.py`

3. **Alerting configuration** (Slack/email)
   - **Mitigation**: Optional, fails gracefully if secrets missing
   - **Rollback**: Remove GitHub secrets to disable

### Low Risk Items:
- Tooltips/toasts: Vanilla JS, no dependencies, isolated
- Button sizing: CSS-only changes
- Documentation: No runtime impact

---

## 🚀 Rollout Plan

### Pre-Merge Checklist:
- [x] All tests passing (17/17 in `test_legal_support_pages.py`)
- [x] Version bumped to `0.9.1` in `app/VERSION`
- [x] CHANGELOG updated with full feature list
- [x] Documentation updated (4 files)
- [x] No secrets in code (all via env vars)
- [x] Safety guardrails maintained (AUTOPOST=false, threshold=0.90)

### Post-Merge Steps:
1. **Merge to `main`**
   ```bash
   git checkout main
   git merge feature/cloud-upgrade-ux-legal --no-ff
   git push origin main
   ```

2. **Render auto-deploys** (via GitHub webhook)
   - Web service rebuilds
   - Worker and cron services deploy (if enabled)
   - Migrations run via `postDeployCommand`

3. **Upgrade Render plans** (if using worker/cron):
   - Dashboard → ai-bookkeeper-worker → Settings → Plan: Starter ($7/mo)
   - Dashboard → ai-bookkeeper-analytics-cron → Settings → Plan: Starter ($7/mo)

4. **Verify deployment** (see "First-Hour Watch" below)

5. **Optional: Configure alerting**:
   - GitHub → Settings → Secrets → Actions
   - Add `SLACK_WEBHOOK_URL` (optional)
   - Add `ALERT_EMAIL` + SMTP secrets (optional)

---

## 🔍 First-Hour Watch

After merge, verify these indicators:

### 1. Health Checks
```bash
curl https://ai-bookkeeper-app.onrender.com/healthz | jq .
# Expected: {"status":"ok", "database_status":"healthy"}

curl https://ai-bookkeeper-app.onrender.com/readyz | jq .
# Expected: {"status":"ready", "checks":{"database":"ok","migrations":"ok"}}
```

### 2. Worker Service (Render Dashboard)
```bash
# Dashboard → ai-bookkeeper-worker → Logs
# Look for: "Worker started", "Listening on queue: ai_bookkeeper"
```

### 3. Cron Service (Render Dashboard)
```bash
# Dashboard → ai-bookkeeper-analytics-cron → Overview
# Verify: "Next run" shows 02:00 UTC
```

### 4. Run Smoke Test
```bash
# GitHub → Actions → "Staging Smoke Test" → Run workflow
# Download artifacts: staging-healthz.json, staging-readyz.json
# Verify: Both show status: "ok"
```

### 5. Test Legal Pages (Public Access)
```bash
# Visit in browser (no login required):
https://ai-bookkeeper-app.onrender.com/legal/terms
https://ai-bookkeeper-app.onrender.com/legal/privacy
https://ai-bookkeeper-app.onrender.com/support

# Verify: "Template Only" banner visible, footer links present
```

### 6. Test Worker (Optional)
```bash
# In Render Shell or locally:
python scripts/test_rq_worker.py
# Expected: "✅ WORKER OK" or "🔄 DRY-RUN"
```

**Full checklist:** See `CI_RUNBOOK.md` → "First-Hour Watch"

---

## 🔄 Rollback Procedure

### If deployment fails:

#### Option 1: Rollback via Render Dashboard
1. Dashboard → ai-bookkeeper-web → Manual Deploy
2. Click "Redeploy" on previous successful deploy
3. Verify `/healthz` returns 200

#### Option 2: Revert Git commit
```bash
git revert HEAD
git push origin main
# Render auto-deploys reverted version
```

#### Option 3: Suspend services temporarily
```bash
# Dashboard → ai-bookkeeper-worker → Suspend
# Dashboard → ai-bookkeeper-analytics-cron → Suspend
# Web service continues running
```

### If worker/cron causing issues:
```bash
# Suspend worker/cron in Render Dashboard
# Does NOT affect web service
# Background jobs will queue but not process
```

### If legal pages causing issues:
```bash
# Unlikely (no auth, no DB access)
# If needed, revert routes.py or disable routes individually
```

**Full rollback guide:** See `RENDER_DEPLOYMENT.md` → "Rollback & Recovery"

---

## 📦 Files Changed (19 total)

### Created:
- `app/VERSION` — Version string: `0.9.1`
- `app/ui/static/toast.js` — Toast notifications
- `app/ui/static/tooltips.js` — Accessible tooltips
- `app/ui/templates/legal/terms.html` — Terms of Service
- `app/ui/templates/legal/privacy.html` — Privacy Policy
- `app/ui/templates/legal/dpa.html` — Data Processing Agreement
- `app/ui/templates/support.html` — Support page
- `tests/test_legal_support_pages.py` — 17 tests (all passing)
- `PR_BODY_v0.9.1.md` — This document
- `RELEASE_NOTES_v0.9.1.md` — Executive summary

### Modified:
- `.github/workflows/smoke_staging.yml` — Slack/email alerting
- `render.yaml` — Worker + cron services
- `app/ui/routes.py` — 4 new public routes
- `app/ui/templates/base.html` — Footer links, toast/tooltip includes
- `scripts/test_rq_worker.py` — Dry-run friendly
- `RENDER_DEPLOYMENT.md` — Rollback procedures
- `CI_RUNBOOK.md` — "First-Hour Watch" section
- `UI_ISSUES.md` — Marked 4 items fixed
- `CHANGELOG.md` — [0.9.1] entry

---

## ✅ Post-Merge Checklist

After merging and deploying, confirm:

- [ ] `/healthz` returns HTTP 200 with `status: "ok"`
- [ ] `/readyz` returns HTTP 200 with `status: "ready"`
- [ ] Worker logs show "Listening on queue: ai_bookkeeper"
- [ ] Cron status shows "Next run: 02:00 UTC"
- [ ] Legal pages load without authentication:
  - [ ] `/legal/terms`
  - [ ] `/legal/privacy`
  - [ ] `/legal/dpa`
  - [ ] `/support`
- [ ] Footer links visible on all pages
- [ ] Smoke test workflow completes successfully
- [ ] No ERROR logs in Render web/worker/cron services
- [ ] (Optional) Slack/email alerts configured and tested

---

## 💰 Cost Impact

### Current (Free Tier):
- Web service: $0/mo (750 hours free)
- Worker: Not available (requires Starter)
- Cron: Not available (requires Starter)
- **Total: $0/mo**

### After Upgrade (Starter Plans):
- Web service: $0/mo (can stay on free tier)
- Worker: $7/mo (Starter plan required)
- Cron: $7/mo (Starter plan required)
- PostgreSQL: $7/mo (existing)
- Redis: $3/mo (existing)
- **Total: $24/mo** (or $10/mo if web stays free)

### Defer Upgrade (Stay on Free Tier):
- Worker and cron will not deploy (render.yaml skips them)
- `test_rq_worker.py` exits 0 with "DRY-RUN" message
- Background jobs won't process (but API remains functional)
- Daily analytics rollup won't run (manual: `python jobs/analytics_rollup.py`)

---

## 🎯 Success Metrics

Within 24 hours of deploy:
- [ ] Zero ERROR-level logs in Render
- [ ] Smoke test passes on schedule (every 6 hours)
- [ ] Worker processes at least 1 test job
- [ ] Cron completes first run (after 02:00 UTC)
- [ ] Legal pages accessed by at least 1 user (check analytics)
- [ ] No increase in `/healthz` p95 latency

---

## 📚 Additional Documentation

- **Implementation details:** `FEATURE_COMPLETE_SUMMARY.md`
- **Release summary:** `RELEASE_NOTES_v0.9.1.md`
- **Deployment guide:** `RENDER_DEPLOYMENT.md`
- **CI workflows:** `CI_RUNBOOK.md`
- **Changelog:** `CHANGELOG.md` (lines 10-103)

---

## 👥 Reviewers

- [ ] @CEO — Business requirements, legal page disclaimers, cost approval
- [ ] @Tech-Lead — Architecture, Render config, alerting setup
- [ ] @QA — Test coverage, WCAG compliance, manual testing

---

## 🚦 Merge Criteria

All boxes must be checked before merging:
- [x] All tests passing (17/17 new tests, 0 regressions)
- [x] Documentation complete (4 files updated, 3 files added)
- [x] Version bumped (`app/VERSION` = `0.9.1`)
- [x] CHANGELOG updated with full feature list
- [x] No secrets in code (env vars only)
- [x] Safety guardrails maintained (AUTOPOST=false, threshold=0.90)
- [x] WCAG 2.1 AA compliance (button sizing, tooltips, toasts)
- [ ] Code review approved (2+ reviewers)
- [ ] Render plan upgrade confirmed (or defer decision documented)

---

**Ready to merge?** ✅ Yes, pending code review approval  
**Deploy after merge:** ✅ Auto-deploy via Render  
**Monitor for:** 1 hour post-deploy (see "First-Hour Watch")

