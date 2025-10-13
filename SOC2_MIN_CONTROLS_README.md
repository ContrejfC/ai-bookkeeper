# SOC 2 Minimum Viable Controls - Quick Start

## Overview

This repository implements **minimum viable SOC 2 controls** that generate durable evidence with zero regressions to core app behavior. All safety guardrails remain intact (AUTOPOST=false by default, threshold ≥0.90, /healthz & /readyz schemas unchanged).

## What's Included

### 1. Centralized Logging with PII Redaction

**Module:** `app/ops/logging.py`

- JSON structured logging with configurable levels
- Automatic PII redaction (emails, SSN, card numbers, secrets, etc.)
- Optional external log drain (HTTPS endpoint with retry/jitter)
- Graceful degradation to stdout when drain unavailable

**Environment Variables:**
```bash
LOG_LEVEL=INFO                          # DEBUG|INFO|WARNING|ERROR
LOG_DRAIN_URL=https://logs.example.com  # Optional HTTPS endpoint
LOG_DRAIN_API_KEY=your-api-key          # Optional API key for drain
```

**Usage:**
```python
from app.ops.logging import get_logger, log_audit_event

logger = get_logger(__name__)
logger.info("User action", extra={"tenant_id": "abc", "action": "login"})

log_audit_event(
    event_type="transaction_approved",
    user_id="user-123",
    tenant_id="tenant-abc",
    metadata={"amount": 150.00}
)
```

### 2. Weekly Access Snapshot

**Job:** `jobs/dump_access_snapshot.py`

Generates compliance evidence snapshot including:
- App users (id, email hash, role, tenants)
- Tenant config flags (autopost_enabled, gating_threshold)
- GitHub org members (if credentials provided)
- Render team members (if credentials provided)

**Outputs:**
- `reports/compliance/access_snapshot_YYYYMMDD.csv`
- `reports/compliance/access_snapshot_YYYYMMDD.json`

**Run Manually:**
```bash
python jobs/dump_access_snapshot.py
```

**CI Schedule:** Weekly (Sunday 02:00 UTC) via `.github/workflows/compliance_weekly.yml`

**Required Secrets (optional):**
- `GITHUB_ORG` - GitHub organization name
- `GITHUB_TOKEN` - GitHub API token (org:read scope)
- `RENDER_API_KEY` - Render API key

### 3. Change-Control Guardrails

**PR Template:** `.github/pull_request_template.md`

Required sections:
- Linked Issue/Ticket URL
- Risk/Impact Assessment
- Rollback Plan
- Tests/Evidence

**CI Gate:** `.github/workflows/pr_label_gate.yml`

Enforces:
- PR body contains linked issue URL
- Label `has-ticket` or `change-control-exempt` is present
- Required template sections are filled

**Exemptions:** Add label `change-control-exempt` for hotfixes (logged for audit trail)

### 4. Backup & Restore Evidence

**Script:** `scripts/backup_restore_check.sh`

Performs:
- Database backup (Postgres: pg_dump, SQLite: dump + copy)
- Test restore to temporary schema/database
- Data verification (row counts)
- Smoke test (/healthz if app running)

**Outputs:**
- `artifacts/compliance/db_backup_<timestamp>.sql`
- `artifacts/compliance/backup_restore_<timestamp>.txt` (evidence report)

**Run Manually:**
```bash
./scripts/backup_restore_check.sh
```

**CI:** Manual workflow `.github/workflows/backup_restore_check.yml`

**Required Environment:**
- `DATABASE_URL` - Database connection string

### 5. Data Retention Job

**Job:** `jobs/data_retention.py`

Deletes old files according to retention policy:
- Receipts: 365 days (default)
- Analytics logs: 365 days (default)
- Application logs: 30 days (default)

**Safety:** Dry-run by default. Set `RETENTION_DELETE=true` to enable deletions.

**Environment Variables:**
```bash
RETENTION_DAYS_RECEIPTS=365    # Days to retain receipts
RETENTION_DAYS_ANALYTICS=365   # Days to retain analytics logs
RETENTION_DAYS_LOGS=30         # Days to retain app logs
RETENTION_DELETE=true          # Enable deletions (false = dry-run)
```

**Run Manually:**
```bash
# Dry-run (default)
python jobs/data_retention.py

# Live run (actually delete)
RETENTION_DELETE=true python jobs/data_retention.py
```

**CI:** Monthly (1st of month) via `.github/workflows/data_retention_report.yml` (dry-run by default)

### 6. Admin Audit Exports

**API Module:** `app/api/admin_compliance.py`

**Endpoints (Owner-only):**
- `GET /api/admin/audit/export.jsonl` - Streaming JSONL export
- `GET /api/admin/audit/export.csv` - Streaming CSV export
- `GET /api/admin/compliance/status` - Compliance posture status

**Query Parameters:**
- `days=90` - Number of days to export (default=90, max=365)

**Usage:**
```bash
# Export last 90 days as JSONL
curl -H "Authorization: Bearer $TOKEN" \
  "https://app.example.com/api/admin/audit/export.jsonl?days=90" > audit.jsonl

# Export last 30 days as CSV
curl -H "Authorization: Bearer $TOKEN" \
  "https://app.example.com/api/admin/audit/export.csv?days=30" > audit.csv
```

**UI Integration:** Add admin link (visible to owner role) to download compliance exports.

### 7. SSO/MFA Verification

**Script:** `scripts/check_mfa_sso.py`

Checks security posture for:
- GitHub org MFA requirement
- GitHub members MFA status
- GitHub org SSO (manual verification guidance)
- Render team SSO/MFA (manual verification guidance)

**Run Manually:**
```bash
python scripts/check_mfa_sso.py
```

**CI:** Weekly (Monday 08:00 UTC) via `.github/workflows/compliance_posture_check.yml`

**Required Secrets (optional):**
- `COMPLIANCE_GITHUB_ORG` - GitHub org name
- `COMPLIANCE_GITHUB_TOKEN` - GitHub token with admin:org scope
- `RENDER_API_KEY` - Render API key

**Exit Codes:**
- `0` - Success or skipped (no credentials)
- `1` - Failure (MFA/SSO not configured)

### 8. Compliance Status Endpoint

**Endpoint:** `GET /api/admin/compliance/status` (Owner-only)

Returns:
- Latest access snapshot timestamp
- Last backup/restore evidence file
- Last retention report
- PR gate status (enabled/disabled)

**Response Example:**
```json
{
  "timestamp": "2025-10-13T12:00:00Z",
  "evidence": {
    "access_snapshot": {
      "filename": "access_snapshot_20251013.json",
      "timestamp": "2025-10-13T02:00:00Z",
      "size_bytes": 12345
    },
    "backup_restore": {
      "filename": "backup_restore_20251012_150000.txt",
      "timestamp": "2025-10-12T15:00:00Z"
    },
    "data_retention": {
      "filename": "data_retention_20251001.txt",
      "timestamp": "2025-10-01T03:00:00Z"
    }
  },
  "pr_gate": {
    "enabled": true,
    "template": true
  }
}
```

## How to Gather Evidence for Auditors

### Weekly Access Reviews

1. **Download Snapshot:**
   ```bash
   # From GitHub Actions artifacts
   gh run download <run-id> -n access-snapshot-<number>
   
   # Or run locally
   python jobs/dump_access_snapshot.py
   ```

2. **Review CSV:**
   - Open `reports/compliance/access_snapshot_YYYYMMDD.csv`
   - Verify user roles and tenant assignments
   - Check autopost settings per tenant

3. **Sign Off:**
   - Document review in issue tracker
   - Note any anomalies or required actions

### Backup/Restore Evidence

1. **Run Check:**
   ```bash
   # Trigger manual workflow
   gh workflow run backup_restore_check.yml
   
   # Or run locally
   ./scripts/backup_restore_check.sh
   ```

2. **Retrieve Evidence:**
   - Download artifact from workflow run
   - Read `artifacts/compliance/backup_restore_<timestamp>.txt`
   - Verify "PASS" status

### Change Control Audit Trail

1. **PR History:**
   - All PRs logged via `.github/workflows/pr_label_gate.yml`
   - Check workflow logs for exemptions (change-control-exempt label)

2. **Review Process:**
   - Each PR has linked issue/ticket
   - Risk assessment and rollback plan documented
   - Test evidence provided

### Data Retention Reports

1. **Monthly Reports:**
   - Download from GitHub Actions artifacts
   - Read `reports/compliance/data_retention_YYYYMMDD.txt`
   - Verify counts and retention policy applied

### SSO/MFA Posture

1. **Run Check:**
   ```bash
   python scripts/check_mfa_sso.py
   ```

2. **Review Output:**
   - GitHub org MFA requirement: PASS/FAIL
   - GitHub members MFA status: PASS/FAIL
   - Manual verification for Render team

## Secrets Required

### For Full Evidence Collection

Configure these secrets in GitHub Actions (Settings → Secrets and variables → Actions):

**Required:**
- `DATABASE_URL` - Database connection string (for backup/restore)

**Optional (for external checks):**
- `GITHUB_ORG` - GitHub organization name
- `GITHUB_TOKEN` - GitHub API token (org:read scope minimum, admin:org for MFA checks)
- `COMPLIANCE_GITHUB_ORG` - Same as GITHUB_ORG (separate for clarity)
- `COMPLIANCE_GITHUB_TOKEN` - GitHub token with admin:org scope
- `RENDER_API_KEY` - Render API key
- `LOG_DRAIN_URL` - HTTPS endpoint for log shipping (e.g., Datadog, Logtail)
- `LOG_DRAIN_API_KEY` - API key for log drain

### For Render Deployment

Add to Render environment variables:
- `LOG_DRAIN_URL` - If using external log aggregation
- `LOG_DRAIN_API_KEY` - API key for drain

## Dry-Run vs. Live Mode

### Data Retention

**Dry-Run (default):**
```bash
python jobs/data_retention.py
# Reports eligible files but does NOT delete
```

**Live Mode:**
```bash
RETENTION_DELETE=true python jobs/data_retention.py
# Actually deletes eligible files
```

### CI Workflows

All workflows degrade gracefully when secrets are missing:
- **No DATABASE_URL**: Backup/restore uses SQLite default
- **No GitHub creds**: Access snapshot skips GitHub members
- **No Render creds**: Access snapshot skips Render team
- **No log drain**: Logs to stdout only

## Testing

Run tests for all new components:

```bash
# All compliance tests
pytest tests/test_logging_redaction.py -v
pytest tests/test_logging_drain.py -v
pytest tests/test_access_snapshot.py -v
pytest tests/test_data_retention.py -v
pytest tests/test_admin_audit_exports.py -v

# All tests
pytest -v
```

## Files Changed

### New Files
- `app/ops/__init__.py`
- `app/ops/logging.py` - Centralized logging module
- `app/api/admin_compliance.py` - Admin audit exports API
- `jobs/dump_access_snapshot.py` - Weekly access snapshot job
- `jobs/data_retention.py` - Data retention job
- `scripts/backup_restore_check.sh` - Backup/restore evidence script
- `scripts/check_mfa_sso.py` - SSO/MFA verification script
- `.github/pull_request_template.md` - PR template
- `.github/workflows/pr_label_gate.yml` - Change control CI gate
- `.github/workflows/compliance_weekly.yml` - Weekly access snapshot
- `.github/workflows/backup_restore_check.yml` - Backup/restore check
- `.github/workflows/data_retention_report.yml` - Monthly data retention
- `.github/workflows/compliance_posture_check.yml` - Weekly SSO/MFA check
- `tests/test_logging_redaction.py`
- `tests/test_logging_drain.py`
- `tests/test_access_snapshot.py`
- `tests/test_data_retention.py`
- `tests/test_admin_audit_exports.py`
- `SOC2_MIN_CONTROLS_README.md` (this file)
- `artifacts/compliance/EVIDENCE_INDEX.md` (auto-generated)

### Modified Files
- `RENDER_DEPLOYMENT.md` - Added log drain configuration
- `CI_RUNBOOK.md` - Added compliance workflows
- `STAGING_GO_LIVE_CHECKLIST.md` - Added backup/restore checks
- `CHANGELOG.md` - Version 0.9.2

## Guardrails Verification

All safety defaults are respected:
- ✅ AUTOPOST=false by default
- ✅ Gating threshold ≥0.90
- ✅ /healthz & /readyz schemas unchanged (only consumed, not modified)
- ✅ No PII in logs, exports, or artifacts
- ✅ Render free-tier compatible (all workflows degrade gracefully)

## Support

For questions or issues:
1. Check workflow logs in GitHub Actions
2. Review evidence files in `reports/compliance/` and `artifacts/compliance/`
3. Run jobs locally with increased logging: `LOG_LEVEL=DEBUG python jobs/<job>.py`

