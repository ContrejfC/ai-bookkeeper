# SOC 2 Minimum Controls & Evidence Automation

## Summary

This PR implements **minimum viable SOC 2 controls** that generate durable evidence with **zero regressions** to core app behavior. All safety guardrails remain intact (AUTOPOST=false, threshold ≥0.90, /healthz & /readyz unchanged).

**Version:** 0.9.2  
**Status:** ✅ Ready for Review  
**Test Coverage:** 52 new tests, 100% pass rate

---

## What's Included

### 1. ✅ Centralized Logging with PII Redaction
- **Module:** `app/ops/logging.py`
- JSON structured logging with automatic PII redaction
- Optional external HTTPS log drain (Datadog, Logtail, etc.)
- Graceful degradation to stdout when drain unavailable
- Environment: `LOG_LEVEL`, `LOG_DRAIN_URL`, `LOG_DRAIN_API_KEY`

### 2. ✅ Weekly Access Snapshot
- **Job:** `jobs/dump_access_snapshot.py`
- Automated user/tenant access reports (CSV + JSON)
- Includes: app users, tenant settings, GitHub org, Render team
- **CI:** Weekly Sunday 02:00 UTC (`.github/workflows/compliance_weekly.yml`)
- Artifacts retained 90 days

### 3. ✅ Change-Control Guardrails
- **PR Template:** `.github/pull_request_template.md`
- **CI Gate:** `.github/workflows/pr_label_gate.yml`
- Enforces: linked issue, risk assessment, rollback plan, test evidence
- Exemption tracking for hotfixes (audit trail)

### 4. ✅ Backup & Restore Evidence
- **Script:** `scripts/backup_restore_check.sh`
- Database backup verification (Postgres + SQLite)
- Test restore to temp schema with data verification
- Evidence reports: `artifacts/compliance/backup_restore_*.txt` (PASS/FAIL)
- **CI:** Manual workflow (`.github/workflows/backup_restore_check.yml`)

### 5. ✅ Data Retention Job
- **Job:** `jobs/data_retention.py`
- Automated retention policy enforcement
- Policies: Receipts 365d, Analytics 365d, Logs 30d
- Dry-run by default (`RETENTION_DELETE=true` to enable)
- **CI:** Monthly 1st at 03:00 UTC (`.github/workflows/data_retention_report.yml`)

### 6. ✅ Admin Audit Exports API
- **Module:** `app/api/admin_compliance.py`
- Owner-only endpoints for compliance exports
- `GET /api/admin/audit/export.jsonl?days=90` - Streaming JSONL
- `GET /api/admin/audit/export.csv?days=90` - Streaming CSV
- `GET /api/admin/compliance/status` - Compliance posture

### 7. ✅ SSO/MFA Verification Script
- **Script:** `scripts/check_mfa_sso.py`
- GitHub org MFA requirement checks
- Member MFA status verification
- **CI:** Weekly Monday 08:00 UTC (`.github/workflows/compliance_posture_check.yml`)

### 8. ✅ Evidence Index
- **File:** `artifacts/compliance/EVIDENCE_INDEX.md`
- Auto-updated by jobs with links to latest evidence
- Simplifies evidence gathering for auditors

---

## Test Coverage

**Total: 52 new tests (100% pass rate)**

| Test Suite | Tests | Status |
|------------|-------|--------|
| `test_logging_redaction.py` | 12 | ✅ Passing |
| `test_logging_drain.py` | 10 | ✅ Passing |
| `test_access_snapshot.py` | 9 | ✅ Passing |
| `test_data_retention.py` | 10 | ✅ Passing |
| `test_admin_audit_exports.py` | 11 | ✅ Passing |

**Run tests:**
```bash
pytest tests/test_logging_redaction.py -v
pytest tests/test_logging_drain.py -v
pytest tests/test_access_snapshot.py -v
pytest tests/test_data_retention.py -v
pytest tests/test_admin_audit_exports.py -v
```

---

## CI/CD Workflows

**5 new automated workflows:**

1. **PR Label Gate** - Change control enforcement (on PR open/edit)
2. **Weekly Access Snapshot** - User/tenant reports (Sunday 02:00 UTC)
3. **Backup/Restore Check** - Database verification (manual)
4. **Data Retention Report** - Retention policy (monthly, 1st at 03:00 UTC)
5. **Compliance Posture Check** - SSO/MFA status (Monday 08:00 UTC)

**All workflows:**
- ✅ Degrade gracefully when secrets missing (free-tier compatible)
- ✅ Upload artifacts with 90-day retention
- ✅ Generate workflow summaries
- ✅ Exit with appropriate status codes

---

## Documentation

### New Documentation
- ✅ `SOC2_MIN_CONTROLS_README.md` - Complete user guide (400+ lines)
- ✅ `SOC2_MIN_CONTROLS_FINAL_REPORT.md` - Delivery report
- ✅ `artifacts/compliance/EVIDENCE_INDEX.md` - Evidence index
- ✅ `.github/pull_request_template.md` - PR template

### Updated Documentation
- ✅ `RENDER_DEPLOYMENT.md` - Added log drain config section
- ✅ `CI_RUNBOOK.md` - Added compliance workflows (300+ lines)
- ✅ `STAGING_GO_LIVE_CHECKLIST.md` - Added compliance verification
- ✅ `CHANGELOG.md` - Added v0.9.2 release notes (150+ lines)

---

## How to Toggle Dry-Run vs. Live Mode

### Data Retention
```bash
# Dry-run (default) - reports but doesn't delete
python jobs/data_retention.py

# Live mode - actually deletes eligible files
RETENTION_DELETE=true python jobs/data_retention.py
```

### CI Workflows
- All workflows default to safe modes (dry-run where applicable)
- Manual workflows support enabling live mode via input parameters
- Scheduled workflows always use dry-run to prevent accidental deletions

---

## Secrets Configuration

### Required (Minimal)
- `DATABASE_URL` - Database connection (defaults to SQLite if not provided)

### Optional (Enhanced Evidence)
- `GITHUB_ORG` + `GITHUB_TOKEN` - GitHub org member lists
- `COMPLIANCE_GITHUB_ORG` + `COMPLIANCE_GITHUB_TOKEN` - MFA verification
- `RENDER_API_KEY` - Render team access
- `LOG_DRAIN_URL` + `LOG_DRAIN_API_KEY` - External log aggregation

**Note:** All workflows run successfully without optional secrets (graceful degradation).

---

## Artifact Paths

**Evidence artifacts generated:**
- `reports/compliance/access_snapshot_YYYYMMDD.{csv,json}`
- `artifacts/compliance/db_backup_<timestamp>.sql`
- `artifacts/compliance/backup_restore_<timestamp>.txt`
- `reports/compliance/data_retention_YYYYMMDD.txt`
- `artifacts/compliance/EVIDENCE_INDEX.md` (auto-updated)

**Access via:**
- GitHub Actions artifacts (90-day retention)
- Local generation via job scripts
- Evidence index for quick reference

---

## Guardrails Verification

✅ **Safety Defaults Intact:**
- AUTOPOST=false by default (unchanged)
- Gating threshold ≥0.90 (unchanged)
- /healthz & /readyz schemas unchanged (only consumed)
- No PII in logs, exports, or artifacts (automatic redaction)
- Render free-tier compatible (graceful degradation)

✅ **Zero Breaking Changes:**
- All existing tests still pass
- Additive-only release (no removals)
- No regressions to core app behavior

---

## Files Changed

**36 files changed** (32 new, 4 modified)  
**~5,400 lines added** (code + tests + docs)

**New Files (32):**
- 2 modules (`app/ops/`)
- 2 jobs (`jobs/`)
- 2 scripts (`scripts/`)
- 1 API module (`app/api/`)
- 5 test suites (`tests/`)
- 5 CI workflows (`.github/workflows/`)
- 5 documentation files

**Modified Files (4):**
- `RENDER_DEPLOYMENT.md`, `CI_RUNBOOK.md`, `STAGING_GO_LIVE_CHECKLIST.md`, `CHANGELOG.md`

---

## How to Review

1. **Review Code Changes:**
   - Check `app/ops/logging.py` for PII redaction logic
   - Review `jobs/` for evidence generation
   - Verify `tests/` for comprehensive coverage

2. **Run Tests:**
   ```bash
   pytest tests/test_logging_*.py -v
   pytest tests/test_access_snapshot.py -v
   pytest tests/test_data_retention.py -v
   pytest tests/test_admin_audit_exports.py -v
   ```

3. **Test Locally:**
   ```bash
   # Generate access snapshot
   python jobs/dump_access_snapshot.py
   
   # Run retention report (dry-run)
   python jobs/data_retention.py
   
   # Test backup/restore
   ./scripts/backup_restore_check.sh
   ```

4. **Review Documentation:**
   - Read `SOC2_MIN_CONTROLS_README.md` for usage guide
   - Check `SOC2_MIN_CONTROLS_FINAL_REPORT.md` for delivery summary

5. **Verify Workflows:**
   - Check `.github/workflows/` for CI configuration
   - Verify graceful degradation without secrets

---

## Next Steps After Merge

1. **Configure Secrets (Optional):**
   - Add GitHub secrets for full evidence collection
   - Configure Render environment for log drain (if desired)

2. **Enable Workflows:**
   - Workflows automatically enabled after merge
   - First runs: Sunday (access), Monday (posture), 1st of month (retention)

3. **Generate Initial Evidence:**
   - Run manual workflows to populate initial evidence
   - Verify artifacts appear in expected locations

4. **Quarterly Audit Prep:**
   - Download evidence packages from GitHub Actions
   - Compile evidence index
   - Provide to auditors with README

---

## Links

- **Detailed Guide:** [SOC2_MIN_CONTROLS_README.md](./SOC2_MIN_CONTROLS_README.md)
- **Final Report:** [SOC2_MIN_CONTROLS_FINAL_REPORT.md](./SOC2_MIN_CONTROLS_FINAL_REPORT.md)
- **Changelog:** [CHANGELOG.md](./CHANGELOG.md) (v0.9.2 section)
- **CI Runbook:** [CI_RUNBOOK.md](./CI_RUNBOOK.md) (compliance section)

---

## Summary

**✅ Deliverables Complete:**
- 7 compliance controls implemented
- 52 tests (100% pass rate)
- 5 automated CI workflows
- Comprehensive documentation
- Zero breaking changes
- Render free-tier compatible

**✅ Ready for:**
- Code review
- Merge to main
- Production deployment
- Audit evidence collection

**Questions?** See `SOC2_MIN_CONTROLS_README.md` or ask in PR comments.


