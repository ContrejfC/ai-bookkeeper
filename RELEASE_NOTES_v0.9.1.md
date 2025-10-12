# AI Bookkeeper v0.9.1 Release Notes

**Release Date:** October 12, 2025  
**Branch:** `feature/cloud-upgrade-ux-legal` → `main`  
**Target:** Render staging environment

---

## Executive Summary

AI Bookkeeper v0.9.1 is a **pilot-readiness release** that adds production-grade infrastructure (worker processes, cron jobs), operational alerting (Slack/email), legal compliance pages (Terms, Privacy, DPA), and accessibility improvements (WCAG 2.1 AA tooltips, toasts, button sizing).

**This release does NOT change core accounting logic or safety guardrails.** AUTOPOST remains disabled (false) and confidence threshold remains at 0.90.

---

## What's New

### 🏗️ Infrastructure: Worker + Cron Services
- **Background worker** (RQ) for async exports and job processing
- **Daily analytics cron** (02:00 UTC) for automated rollups
- **Dry-run mode** for free-tier compatibility (graceful degradation)
- **Plan requirement**: Render Starter ($7/mo each, $14/mo total)

### 🔔 Operational Alerting
- **Slack notifications** on staging health check failures (optional)
- **Email alerts** via SMTP on smoke test failures (optional)
- **Status badges** in GitHub Actions summary (green/red indicators)
- **Graceful degradation**: Works without secrets configured

### 📄 Legal & Compliance Pages
- **Terms of Service** (`/legal/terms`) — Public access, no auth
- **Privacy Policy** (`/legal/privacy`) — GDPR compliance template
- **Data Processing Agreement** (`/legal/dpa`) — GDPR Article 28 template
- **Support page** (`/support`) — Help center with export + security contacts
- **Footer links** site-wide for easy access
- **Disclaimers**: All pages marked "template only / not legal advice"

### ♿ Accessibility & UX
- **Button sizing**: WCAG 2.1 AA compliant (44x44px minimum)
- **Tooltips**: Keyboard accessible with `aria-describedby`
- **Toast notifications**: Queued, `aria-live` for screen readers
- **Consistent timing**: 3.5s (success), 6s (error), ESC to dismiss

### 📚 Documentation
- **Rollback procedures** for web, worker, cron, and database
- **"First-Hour Watch"** post-deploy checklist with quick URLs
- **Alerting setup** guide (Slack webhook, SMTP config)
- **Plan tier requirements** and free-tier limitations

---

## What Changed

| Component | Change | Impact |
|-----------|--------|--------|
| `render.yaml` | Added worker + cron services | Requires Starter plan or gracefully degrades |
| Smoke tests | Slack/email alerting on failure | Optional, non-blocking if not configured |
| Legal pages | 4 new public routes + templates | No auth required, `noindex` meta tags |
| UI/UX | Tooltips, toasts, button sizing | WCAG 2.1 AA compliance, no breaking changes |
| Docs | Rollback, alerting, first-hour watch | Operational readiness for pilots |

---

## Safety & Guardrails

✅ **Unchanged Safety Defaults:**
- `AUTOPOST_ENABLED=false` — Manual review required
- `GATING_THRESHOLD=0.90` — High confidence required for auto-post eligibility
- `UI_ASSESSMENT=1` — Assessment banner visible
- PII stripping — Maintained in analytics and logs

✅ **No Changes To:**
- Core accounting logic (categorization, posting, reconciliation)
- Authentication/authorization (RBAC, JWT, CSRF)
- Database schema (no new migrations in this release)
- API contracts (`/healthz`, `/readyz` schemas unchanged)

✅ **New Guardrails:**
- Legal pages: Public routes intentionally, no sensitive data exposed
- Worker/cron: Dry-run mode prevents failures on free tier
- Alerting: Optional, fails gracefully if secrets missing

---

## Deployment Notes

### Plan Requirements

| Service | Plan | Cost | Required For |
|---------|------|------|--------------|
| Web | Free | $0 | Core app (always required) |
| Worker | Starter | $7/mo | Background jobs (optional) |
| Cron | Starter | $7/mo | Daily rollups (optional) |
| PostgreSQL | Starter | $7/mo | Database (existing) |
| Redis | Starter | $3/mo | Caching + queue (existing) |
| **Total** | | **$24/mo** | Full setup |

**Free Tier Option:**
- Stay on free tier for web only
- Worker and cron gracefully skip (dry-run mode)
- Manual analytics rollup: `python jobs/analytics_rollup.py`

### Rollout Steps

1. **Merge to main** → Auto-deploy via Render webhook
2. **Upgrade plans** (optional): Dashboard → Services → Settings → Plan: Starter
3. **Verify health**: `/healthz` and `/readyz` return 200
4. **Check logs**: Worker "Listening on queue", Cron "Next run: 02:00 UTC"
5. **Test legal pages**: Visit `/legal/terms`, `/support` (no login required)
6. **Run smoke test**: GitHub Actions → "Staging Smoke Test" → Run workflow

**Full checklist:** See `CI_RUNBOOK.md` → "First-Hour Watch"

### Rollback Options

1. **Render Dashboard** → Redeploy previous version
2. **Git revert** → `git revert HEAD && git push`
3. **Suspend services** → Disable worker/cron temporarily

**Full guide:** See `RENDER_DEPLOYMENT.md` → "Rollback & Recovery"

---

## Testing

### Test Coverage
- **17 new tests** in `tests/test_legal_support_pages.py` (all passing ✅)
- **Test categories:**
  - Legal pages return 200, contain expected content, have `noindex` meta
  - Support page has email, export link, security contact
  - Public access control (no auth required)
  - Footer links present on all pages

### Manual Testing Checklist
- [x] Legal pages load without authentication
- [x] Footer links visible on all pages
- [x] Tooltips trigger on focus/hover, ESC closes
- [x] Toast notifications queue, dismiss with ESC
- [x] Button sizing meets 44x44px minimum (WCAG 2.1 AA)
- [x] Worker test script handles missing Redis gracefully
- [x] Smoke test workflow shows status badges

---

## Pilot Safety

### What Pilots Will See:
- **Legal pages** in footer (Terms, Privacy, DPA, Support)
- **Assessment banner** at top (UI_ASSESSMENT=1 still enabled)
- **Improved UX**: Tooltips on hover/focus, toasts for feedback
- **No functional changes** to transaction review, categorization, or export

### What Pilots Won't See:
- Background worker (processing happens instantly for now)
- Daily analytics cron (data is real-time)
- Alerting (internal ops tool, not user-facing)

### Pilot Communication:
> "We've added legal pages (Terms, Privacy, DPA) accessible from the footer. These are templates for transparency while we finalize production terms with our legal team. You can also visit /support for help and data export options. The core app functionality remains unchanged—your transactions still require manual review before posting (AUTOPOST disabled)."

---

## Known Limitations

1. **Legal pages are templates**: Marked "not legal advice", require attorney review before production
2. **Worker/cron require Starter plan**: Free tier gracefully degrades to dry-run mode
3. **Alerting is optional**: Requires GitHub secrets (SLACK_WEBHOOK_URL, ALERT_EMAIL)
4. **Filter persistence not implemented**: Marked as backlog (post-pilot enhancement)
5. **Audit pagination not implemented**: Marked as backlog (performance optimization)

---

## Migration Notes

**No database migrations in this release.**
- Existing schema unchanged
- No data migration required
- Alembic version remains at current head

**Configuration changes:**
- **New optional env vars**:
  - `SUPPORT_EMAIL` — Display email on /support page (defaults to support@yourdomain.tld)
  - `SLACK_WEBHOOK_URL` — GitHub secret for alerting (optional)
  - `ALERT_EMAIL` — GitHub secret for email alerts (optional)
  - SMTP secrets: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` (optional)

**No breaking changes to existing env vars.**

---

## Post-Release Tasks

### Immediate (First Hour):
- [ ] Verify `/healthz` and `/readyz` return 200
- [ ] Check worker logs for "Listening on queue"
- [ ] Check cron status for "Next run: 02:00 UTC"
- [ ] Test legal pages (no auth required)
- [ ] Run smoke test workflow

### Next 24 Hours:
- [ ] Monitor Render logs for ERROR/CRITICAL entries
- [ ] Verify worker processes at least 1 test job
- [ ] Confirm cron completes first run (after 02:00 UTC)
- [ ] Check legal page analytics (visits, bounce rate)

### Next Week:
- [ ] Review legal page content with attorney
- [ ] Customize support email (`SUPPORT_EMAIL` env var)
- [ ] Configure Slack webhook for alerting (optional)
- [ ] Gather pilot feedback on UX improvements

---

## Support & Resources

**Documentation:**
- Implementation details: `FEATURE_COMPLETE_SUMMARY.md`
- Deployment guide: `RENDER_DEPLOYMENT.md`
- CI workflows: `CI_RUNBOOK.md`
- Changelog: `CHANGELOG.md` (lines 10-103)
- PR body: `PR_BODY_v0.9.1.md`

**Troubleshooting:**
- Health check failing → See `RENDER_DEPLOYMENT.md` → "Troubleshooting"
- Worker not processing → See `CI_RUNBOOK.md` → "First-Hour Watch" → Step 2
- Cron not running → Dashboard → ai-bookkeeper-analytics-cron → Logs
- Legal pages not loading → Check `app/ui/routes.py` routes are enabled

**Quick Links:**
- Render Dashboard: https://dashboard.render.com
- GitHub Actions: https://github.com/YOUR_ORG/ai-bookkeeper/actions
- Smoke Test Workflow: `.github/workflows/smoke_staging.yml`

---

**Release Manager:** AI Assistant  
**Approved By:** _Pending CEO + Tech Lead review_  
**Deployed To:** Render staging (auto-deploy on merge)  
**Status:** ✅ Ready for pilot deployment

