# Changelog

All notable changes to AI Bookkeeper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.9.1] - 2025-10-12

### 🚀 Cloud Upgrade + UX Polish + Legal Pages

This release prepares the system for pilot deployment with worker services, cron jobs, alerting, legal pages, and accessibility improvements.

---

### Added

#### A) Render Services: Worker + Cron
- **RQ Worker service**: Background job processing for exports and async operations
- **Analytics Cron job**: Daily rollup at 02:00 UTC (`jobs/analytics_rollup.py`)
- **Dry-run worker test**: `scripts/test_rq_worker.py` gracefully handles missing Redis
- **`render.yaml` updates**: Three services (web, worker, cron) with proper env vars
- **Starter plan requirement**: Worker and cron require Render Starter plan ($7/mo each)

#### B) Alerting: Slack + Email on Failure
- **Slack notifications**: Smoke test failures post to webhook (if `SLACK_WEBHOOK_URL` configured)
  - Rich message with service status, troubleshooting tips, and action buttons
  - Gracefully skipped if webhook not configured (non-blocking)
- **Email notifications**: Optional SMTP-based alerts (if `ALERT_EMAIL` configured)
  - Uses `dawidd6/action-send-mail` GitHub Action
  - Configurable SMTP server (defaults to Gmail)
- **Enhanced GitHub Actions summary**: Green/red status badges in workflow output

#### C) Legal & Support Pages
- **Public routes** (no authentication required):
  - `GET /legal/terms` — Terms of Service
  - `GET /legal/privacy` — Privacy Policy
  - `GET /legal/dpa` — Data Processing Agreement (GDPR Article 28 compliant template)
  - `GET /support` — Support & Help Center
- **Templates with disclaimers**: All legal pages include "template only / not legal advice" banner
- **noindex meta tags**: Legal pages excluded from search engine indexing
- **Footer links**: Terms, Privacy, DPA, Support visible site-wide
- **Tests**: `tests/test_legal_support_pages.py` (17 tests, all passing)

#### D) UX Polish & Accessibility
- **Consistent button sizing**: `.btn-md` (44x44px) and `.btn-lg` (48x48px) CSS classes for WCAG 2.1 AA compliance
- **Accessible tooltips**: `app/ui/static/tooltips.js`
  - Keyboard accessible (focus + hover)
  - `aria-describedby` for screen readers
  - ESC to close, auto-positioning with viewport detection
- **Toast notifications**: `app/ui/static/toast.js`
  - Success/info: 3.5s, Warning: 4.5s, Error: 6s
  - Queued notifications with `aria-live="polite"`
  - ESC to dismiss, semantic color coding
- **Site-wide utility scripts**: Toast and tooltip included in `base.html`

#### E) Documentation Updates
- **`RENDER_DEPLOYMENT.md`**:
  - Rollback procedures (web, worker, cron, database)
  - Plan tier requirements and limitations
  - Manual re-run instructions for cron jobs
  - Worker troubleshooting guide
- **`CI_RUNBOOK.md`**:
  - Slack webhook setup instructions
  - Email alert configuration (SMTP)
  - Test alerting procedure
  - Required GitHub Secrets matrix
- **`UI_ISSUES.md`**:
  - Marked 4 items as fixed (button sizing, tooltips, toasts, legal pages)
  - Updated status counts (7 fixed, 11 backlog)
- **`CHANGELOG.md`**: This entry

---

### Changed

- **`render.yaml`**: Now includes worker and cron services (requires Starter plan)
- **`.github/workflows/smoke_staging.yml`**: Enhanced with Slack/email alerting and status badges
- **`app/ui/templates/base.html`**: 
  - Updated footer with legal/support links
  - Included toast.js and tooltips.js site-wide
  - Added `.btn-md` and `.btn-lg` CSS utility classes
- **`scripts/test_rq_worker.py`**: Made dry-run friendly (exits 0 if Redis unavailable)

---

### Fixed

- **Button touch targets**: All interactive buttons now meet WCAG 2.1 AA minimum size (44x44px)
- **Tooltip accessibility**: Replaced bare `title` attributes with keyboard-accessible tooltips
- **Toast timing consistency**: Standardized notification durations across all pages
- **Missing legal pages**: Terms, Privacy, DPA, and Support now publicly accessible

---

### Infrastructure

- **Plan requirements**: Worker and cron require Render Starter plan ($7/mo each, $14/mo total)
- **Free tier limitations**: Worker and cron not available on free tier (documented in `RENDER_DEPLOYMENT.md`)
- **Alerting is optional**: Slack and email alerts only fire if secrets configured (graceful degradation)

---

## [0.9.0-rc] - 2024-10-11

### 🎉 Release Candidate — Sprint 9 Complete

This release candidate includes all Sprint 9 (P0 Audit Compliance) deliverables, achieving production-grade performance, accuracy, and security.

---

### Added

#### Stage A — PostgreSQL + Base Fixtures
- **PostgreSQL 15** as primary database (deprecating SQLite)
- **Alembic migrations** for schema versioning
- **Base fixtures**: 2 tenants (Alpha, Beta) with ≥1,200 transactions each
- **Health endpoints**: `/healthz` (lightweight) and `/readyz` (comprehensive)
- **CI automation**: Automated evidence collection for Stage A acceptance
- **DB smoke CLI**: `scripts/db_smoke.py` for ops testing

#### Stage B — Receipts + OCR + Noise
- **Synthetic receipts**: ≥600 text receipts with 8–10% OCR-like noise
- **PDF golden set**: 100 PDFs rendered from text receipts
- **OCR parser stub**: `app/ocr/parser.py` with ≥90% field-level accuracy
- **Noise validation tests**: Deterministic noise recipe (typos 5%, casing 3%, spacing 2%)

#### Stage C — Calibration
- **Isotonic regression calibration**: ECE 0.029 (target: minimize)
- **Vendor normalization**: Enhanced normalization to prevent data leakage
- **Holdout strategy**: Last 30 days per tenant, 0 vendor overlap
- **Calibration metrics**: Brier 0.118, Accuracy 93.4%, all groups ≥80%
- **Vendor leakage tests**: Unit tests confirm 0 overlap in train/holdout

#### Stage D — Calibrated_p Enforcement + Cold-Start
- **Pre-blender auto-post gating**: `calibrated_p ≥ 0.90` required
- **Cold-start policy**: Require 3 consistent labels before auto-post eligibility
- **Enhanced explain API**: Includes `calibrated_p`, `auto_post_eligible`, `not_auto_post_reason`, `cold_start` status
- **Per-tenant threshold overrides**: Tenant-specific gating thresholds
- **Reason codes**: 6 reason codes for audit trails (below_threshold, cold_start, imbalance, budget_fallback, anomaly, rule_conflict)

#### Stage E — Metrics Endpoint
- **`/api/metrics/latest`**: Comprehensive metrics endpoint with:
  - `automation_rate`, `auto_post_rate`, `review_rate`
  - `brier_score`, `calibration_method`, `ece_bins`
  - `gating_threshold`, `not_auto_post_counts` (reason-coded tallies)
  - `llm_calls_per_txn`, `unit_cost_per_txn`, `llm_budget_status`
  - `ruleset_version_id`, `model_version_id`
- **Metrics window filters**: `?tenant_id` and `?period=7d|30d|90d`
- **Decision audit log**: Persists reason codes for audits

#### Stage F — QBO CSV Export (Idempotent)
- **`POST /api/export/qbo`**: 11-column QBO CSV export
- **ExternalId**: SHA-256 hash (first 32 hex in CSV, full 64 hex internally)
- **Idempotency**: Re-exports skip duplicates via `qbo_export_log` table
- **Concurrency-safe**: ON CONFLICT DO NOTHING for race conditions
- **Balanced totals**: All exports maintain debit = credit balance

#### Stage G — LLM Cost Tracking + Fallback
- **LLM call logging**: Middleware logs all LLM API calls to `llm_call_logs`
- **Rolling 30-day aggregations**: Per-tenant and global spend tracking
- **Guardrails**:
  - Calls/txn cap: ≤ 0.30
  - Tenant budget: $50/month
  - Global budget: $1,000/month
- **Automatic fallback**: Switch to Rules/ML-only when caps breached
- **Metrics integration**: `llm_budget_status` exposed via `/api/metrics/latest`

#### Stage H — SBOM & Security
- **SBOM generation**: CycloneDX v1.4 with 47 components
- **Security scans**: pip-audit, Bandit, Trivy in CI
- **CI gates**: Fail on HIGH/CRITICAL vulnerabilities
- **Security artifacts**: `artifacts/security/` with all scan reports
- **Zero vulnerabilities**: All scans passing

---

### Tests

**Total Tests:** 28/28 passing (100%)

- **Stage D**: 11/11 tests (gating + cold-start)
- **Stage F**: 12/12 tests (idempotency + balanced + concurrency)
- **Stage G**: 5/5 tests (budget caps + fallback)

---

### Security

- ✅ **0 known vulnerabilities** (pip-audit)
- ✅ **0 HIGH/CRITICAL issues** (Trivy)
- ✅ **0 SAST issues** (Bandit, 2,850 lines scanned)
- ✅ **SBOM published**: `artifacts/security/sbom.json`

---

### Performance

- **Calibration**:
  - Brier Score: **0.118** (target ≤0.15)
  - ECE (isotonic): **0.029**
  - Overall Accuracy: **93.4%** (target ≥92%)
  - All account groups: **≥80%**

- **OCR Accuracy**: **≥90%** field-level (date, amount, vendor)

- **Automation Rate**: **82.3%** auto-post, **17.7%** review

---

### Configuration

**Feature Flags (Defaults):**

```bash
# Auto-post gating
AUTOPOST_ENABLED=false          # Tenant-level override required
AUTOPOST_THRESHOLD=0.90         # Calibrated_p threshold

# Cold-start policy
COLDSTART_MIN_LABELS=3          # Min consistent labels for auto-post

# LLM budget caps
LLM_TENANT_CAP_USD=50           # Per tenant/month
LLM_GLOBAL_CAP_USD=1000         # Global/month
LLM_CALLS_PER_TXN_CAP=0.30      # Rolling average

# Database
DATABASE_URL=postgresql://...   # PostgreSQL 15+ required

# Calibration
CALIBRATION_METHOD=isotonic     # Isotonic regression
```

---

### Database Migrations

**Alembic Head:** `001_initial_schema`

**New Tables:**
- `decision_audit_log` — Reason code persistence
- `qbo_export_log` — Export idempotency tracking
- `llm_call_logs` — LLM usage tracking
- `cold_start_tracking` — Vendor label counts
- `calibration_metadata` — Calibration model storage

---

### API Endpoints

**New:**
- `GET /healthz` — Lightweight health check
- `GET /readyz` — Comprehensive readiness check
- `GET /api/metrics/latest` — Metrics endpoint with filters
- `POST /api/export/qbo` — QBO CSV export
- `GET /api/explain/{txn_id}` — Enhanced with reason codes

**Updated:**
- All decision endpoints now include `calibrated_p` and `not_auto_post_reason`

---

### Breaking Changes

⚠️  **PostgreSQL Required**: SQLite is deprecated. Migrate to PostgreSQL 15+.

⚠️  **Auto-post disabled by default**: `AUTOPOST_ENABLED=false` requires tenant-level opt-in.

⚠️  **Calibration required**: Models must be calibrated before deployment.

---

### Deprecated

- SQLite as primary database (dev fallback only)
- Uncalibrated model probabilities (must use `calibrated_p`)

---

### Fixed

- Vendor leakage in holdout strategy (0 overlap confirmed)
- OCR noise determinism (fixed seeds)
- QBO export race conditions (concurrency-safe)
- LLM budget tracking precision

---

### Documentation

**New Docs:**
- `STAGE_A_EVIDENCE.md` — PostgreSQL setup evidence
- `STAGE_B_FINAL_REPORT.md` — OCR accuracy report
- `STAGE_C_FINAL_REPLY.md` — Calibration metrics
- `STAGE_D_E_FINAL_REPLY.md` — Gating + metrics
- `STAGES_F_G_H_FINAL_REPLY.md` — Export + LLM + security
- `DEPLOYMENT_CHECKLIST.md` — Production deployment guide
- `PILOT_ENABLEMENT.md` — Pilot onboarding guide

---

### Contributors

- AI Bookkeeper Engineering Team

---

## [0.8.0] - 2024-09-15

### Added
- Sprint 8: Adaptive Rules, Explainability, and Decision Blending
- Sprint 7: Drift Detection + Auto-Retraining
- Sprint 6: System Diagnostic & Validation
- Sprint 5: Training Pipeline + Unit Tests + Benchmarking
- Sprint 4: Async + ML Uplift to 80%

---

## [0.1.0] - 2024-08-01

### Added
- Initial release
- Basic rule-based categorization
- FastAPI application structure
- SQLite database

