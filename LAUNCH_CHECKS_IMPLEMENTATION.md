# Launch Checks Implementation - Complete

## Overview

Implemented a comprehensive pre-launch verification harness for AI-Bookkeeper that runs automated end-to-end checks and produces detailed reports in both JSON and Markdown formats.

**Status:** ✅ **COMPLETE** - All deliverables implemented and ready for use

**Date:** October 30, 2025

---

## Deliverables

### ✅ Configuration Files

1. **`/ops/launch_checks/README.md`** - Complete documentation
   - Quick start guide
   - Configuration instructions
   - Check descriptions
   - Troubleshooting guide
   - Extension examples

2. **`/ops/launch_checks/env.example`** - Environment variable template
   - Required variables (API_BASE, TEST_TENANT_ID)
   - Optional integration variables (Stripe, QBO, Xero)
   - Clear comments and examples

3. **`/ops/launch_checks/config.yaml`** - Configuration file
   - Environment variable interpolation
   - Endpoint definitions
   - Required/optional check categorization
   - PII patterns and thresholds

### ✅ Core Implementation

4. **`/ops/launch_checks/verify.sh`** - POSIX shell wrapper
   - Loads `.env` if present
   - Creates timestamped report directories
   - Runs Python checks
   - Validates JSON schema
   - Exit codes: 0=success, 1=required failures, 2=config error, 3=runtime error

5. **`/ops/launch_checks/checks.py`** - Main Python implementation (850+ lines)
   - Configuration loading with env var interpolation
   - HTTP helpers with retries and timeouts
   - 11 comprehensive checks:
     1. Health endpoint (`/healthz`)
     2. Readiness endpoint (`/readyz`)
     3. CORS/security headers
     4. Stripe checkout idempotency
     5. Webhook idempotency
     6. QBO demo posting idempotency
     7. Xero demo posting idempotency
     8. AI threshold gating
     9. PII redaction verification
     10. Audit export generation
     11. Ingestion robustness (malformed/oversized files)
   - Markdown report generator
   - Structured logging and error handling

6. **`/ops/launch_checks/report_schema.json`** - JSON Schema validation
   - Validates report structure
   - Required fields defined
   - Type checking for all properties

### ✅ Test Fixtures

7. **`/ops/fixtures/sample_small.csv`** - 20-row sample with realistic transactions
8. **`/ops/fixtures/sample_malformed.csv`** - Bad quotes, wrong delimiters, invalid dates
9. **`/ops/fixtures/pii_probe.csv`** - Contains emails, SSNs, phone numbers for redaction testing
10. **`/ops/fixtures/stripe_checkout_payload.json`** - Stripe checkout session data
11. **`/ops/fixtures/stripe_invoice_webhook.json`** - Stripe webhook event
12. **`/ops/fixtures/qbo_journal_sample.json`** - QuickBooks journal entry
13. **`/ops/fixtures/xero_journal_sample.json`** - Xero journal entry
14. **`/ops/fixtures/generate_oversized.py`** - Script to generate 100k-row CSV

### ✅ Tests

15. **`/tests/ops/test_launch_checks.py`** - Comprehensive test suite
    - Unit tests for config loading, data models, Markdown generation
    - E2E tests (marked with `@pytest.mark.e2e`, skipped if env not configured)
    - Mock-based idempotency tests
    - 20+ test cases

### ✅ CI/CD

16. **`/.github/workflows/launch-checks.yml`** - GitHub Actions workflow
    - Manual trigger with inputs
    - Nightly cron at 2 AM UTC
    - Triggers on release tags
    - Matrix strategy (required/optional)
    - Artifact uploads (report.json, report.md, audit.csv)
    - PR comment integration
    - Failure notifications

---

## Architecture

### Data Flow

```
verify.sh
    ↓
Load .env → Interpolate config.yaml
    ↓
checks.py --config config.yaml --out report.json
    ↓
Run 11 checks in sequence
    ↓
Generate report.json + report.md
    ↓
Exit with appropriate code
```

### Check Result Format

```json
{
  "name": "healthz",
  "status": "PASS|FAIL|SKIP",
  "duration_ms": 45,
  "details": {...},
  "evidence": "Human-readable summary",
  "required": true
}
```

### Report Format

```json
{
  "timestamp_utc": "2025-10-30T12:34:56Z",
  "api_base": "https://api.example.com",
  "summary": {"pass": 8, "fail": 0, "skip": 3, "total": 11},
  "checks": [...],
  "artifacts": [...]
}
```

---

## Usage

### Local Execution

```bash
# 1. Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -U requests pyyaml pytest pydantic jsonschema stripe

# 2. Configure environment
cp ops/launch_checks/env.example ops/launch_checks/.env
# Edit .env with your values

# 3. Generate oversized fixture (optional)
python ops/fixtures/generate_oversized.py

# 4. Run checks
./ops/launch_checks/verify.sh
```

### CI Execution

```bash
# Manual trigger via GitHub CLI
gh workflow run launch-checks.yml -f api_base=https://your-api.com

# Or via GitHub UI: Actions → Launch Checks → Run workflow
```

### Output Structure

```
ops/reports/2025-10-30T12-34-56Z/
├── report.json          # Machine-readable
├── report.md            # Human-readable
├── audit.csv            # Sample audit export
└── artifacts/           # Additional evidence
```

---

## Checks Implemented

### 1. Health Check ✅ (Required)
- **Endpoint:** `GET /healthz`
- **Expected:** 200 with `{"status": "healthy"}` or `{"ok": true}`
- **Duration:** ~50ms

### 2. Readiness Check ✅ (Required)
- **Endpoint:** `GET /readyz`
- **Expected:** 200 with database connectivity confirmation
- **Duration:** ~50ms

### 3. CORS/Security ✅ (Required)
- **Checks:** HttpOnly, Secure, SameSite cookies
- **Optional:** X-Content-Type-Options, X-Frame-Options
- **Duration:** ~100ms

### 4. Stripe Idempotency ⏭️ (Optional)
- **Test:** Create two checkout sessions with same idempotency key
- **Expected:** Identical session IDs
- **Skips if:** STRIPE_SECRET_KEY not configured
- **Duration:** ~500ms

### 5. Webhook Idempotency ⏭️ (Optional)
- **Test:** POST same webhook event twice
- **Expected:** First 2xx, second 2xx with no duplicate processing
- **Skips if:** STRIPE_WEBHOOK_SECRET not configured
- **Duration:** ~300ms

### 6. QBO Demo Posting ⏭️ (Optional)
- **Test:** POST balanced journal entry twice
- **Expected:** Same QBO doc ID returned
- **Skips if:** QBO_REALM_ID not configured or demo_mode=false
- **Duration:** ~800ms

### 7. Xero Demo Posting ⏭️ (Optional)
- **Test:** POST journal entry twice
- **Expected:** Same Xero journal ID returned
- **Skips if:** XERO_TENANT_ID not configured or demo_mode=false
- **Duration:** ~800ms

### 8. AI Threshold Gate ✅ (Required)
- **Test:** Upload sample_small.csv to propose endpoint
- **Expected:** Low-confidence entries flagged for review
- **Expected:** All journal entries balanced (debits = credits)
- **Duration:** ~3000ms

### 9. PII Redaction ✅ (Required)
- **Test:** Upload pii_probe.csv containing emails, SSNs, phones
- **Expected:** Response contains redaction markers (***EMAIL***, ***SSN***)
- **Expected:** No raw PII in response
- **Duration:** ~500ms

### 10. Audit Export ⏭️ (Optional)
- **Test:** GET /api/audit/export with tenant_id and date range
- **Expected:** Valid CSV with headers
- **Skips if:** 401 (authentication required)
- **Duration:** ~1000ms

### 11. Ingestion Robustness ✅ (Required)
- **Test 1:** Upload malformed CSV → expect 4xx (not 500)
- **Test 2:** Upload oversized CSV → expect clean handling
- **Expected:** No 5xx errors
- **Duration:** ~5000ms

---

## Configuration

### Required Environment Variables

```bash
API_BASE=https://your-api.com
TEST_TENANT_ID=your-tenant-uuid
```

### Optional Environment Variables

```bash
# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
WEBHOOK_URL=https://your-api.com/api/billing/stripe_webhook

# QuickBooks Online
QBO_REALM_ID=1234567890
QBO_CLIENT_ID=...
QBO_CLIENT_SECRET=...
QBO_REFRESH_TOKEN=...

# Xero
XERO_TENANT_ID=...
XERO_CLIENT_ID=...
XERO_CLIENT_SECRET=...
XERO_REFRESH_TOKEN=...

# Advanced
REQUEST_TIMEOUT=30
MAX_RETRIES=3
DEBUG=false
```

---

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | All required checks passed | Proceed with deployment |
| 1 | Required check(s) failed | Block deployment, investigate |
| 2 | Configuration error | Fix env vars or config.yaml |
| 3 | Runtime error | Check logs, fix code |

---

## CI Integration

### Triggers

1. **Manual:** `workflow_dispatch` with inputs
2. **Nightly:** Cron at 2 AM UTC
3. **Release:** Push to `release/*` or `v*` tags

### Matrix Strategy

- **Required mode:** Fails job if any required check fails
- **Optional mode:** Always succeeds, uploads artifacts

### Artifacts

All reports retained for 90 days:
- `launch-checks-report-required-{run_number}`
- `launch-checks-report-optional-{run_number}`

Each contains:
- `report.json`
- `report.md`
- `audit.csv`

---

## Testing

### Run Unit Tests

```bash
pytest tests/ops/test_launch_checks.py -v
```

### Run E2E Tests

```bash
# Set API_BASE first
export API_BASE=https://your-api.com
export TEST_TENANT_ID=your-tenant-uuid

pytest tests/ops/test_launch_checks.py -v -m e2e
```

### Skip E2E Tests

```bash
pytest tests/ops/test_launch_checks.py -v -m "not e2e"
```

---

## Validation

### Validate Report Structure

```bash
python - <<'PY'
import json, jsonschema
jsonschema.validate(
    json.load(open('ops/reports/<timestamp>/report.json')),
    json.load(open('ops/launch_checks/report_schema.json'))
)
print("✓ Valid")
PY
```

### Check Linting

```bash
# Python
pylint ops/launch_checks/checks.py

# Shell
shellcheck ops/launch_checks/verify.sh
```

---

## Extension Examples

### Add New Check

```python
def run_my_check(config: Config) -> CheckResult:
    """My custom check."""
    start = time.time()
    try:
        # Perform check
        result = do_something()
        
        return CheckResult(
            name="my_check",
            status="PASS",
            duration_ms=int((time.time() - start) * 1000),
            details={"result": result},
            evidence="Check passed successfully"
        )
    except Exception as e:
        return CheckResult(
            name="my_check",
            status="FAIL",
            duration_ms=int((time.time() - start) * 1000),
            details={"error": str(e)},
            evidence=f"Check failed: {e}"
        )
```

Then add to `run_all_checks()`:
```python
checks.append(run_my_check(config))
```

### Add to Required Checks

In `config.yaml`:
```yaml
checks:
  required:
    - healthz
    - readyz
    - my_check  # Add here
```

---

## Acceptance Criteria

### ✅ Single Command Execution
- `./ops/launch_checks/verify.sh` runs to completion on macOS/Linux

### ✅ Deterministic Output
- Always produces `report.json` and `report.md`
- Follows JSON Schema structure
- Timestamped directories prevent collisions

### ✅ Zero Secrets in Repo
- All secrets in `.env` (gitignored)
- GitHub Actions uses secrets
- `env.example` contains placeholders only

### ✅ Graceful Skipping
- Optional checks skip when credentials absent
- SKIP status clearly indicated in reports
- No false failures

### ✅ Idempotency Validation
- Stripe sessions: same ID on duplicate requests
- Webhooks: second POST doesn't duplicate side effects
- QBO/Xero: same external ID on duplicate posts

### ✅ No 500s on Negative Tests
- Malformed CSV → 4xx
- Oversized CSV → 4xx or clean acceptance
- Invalid data → 4xx with readable error

### ✅ CI Enforcement
- Required checks fail the job
- Artifacts uploaded automatically
- Schema validation runs
- PR comments posted (when applicable)

---

## Files Created

```
ops/
├── launch_checks/
│   ├── README.md               ✅ Complete documentation
│   ├── env.example             ✅ Environment template
│   ├── config.yaml             ✅ Configuration file
│   ├── verify.sh               ✅ Shell wrapper (executable)
│   ├── checks.py               ✅ Main Python implementation
│   ├── report_schema.json      ✅ JSON Schema
│   └── __init__.py             ✅ Package marker
├── fixtures/
│   ├── sample_small.csv        ✅ 20-row sample
│   ├── sample_malformed.csv    ✅ Bad formatting
│   ├── pii_probe.csv           ✅ PII patterns
│   ├── stripe_checkout_payload.json     ✅ Checkout data
│   ├── stripe_invoice_webhook.json      ✅ Webhook event
│   ├── qbo_journal_sample.json          ✅ QBO journal
│   ├── xero_journal_sample.json         ✅ Xero journal
│   └── generate_oversized.py            ✅ Generate 100k rows
└── __init__.py                 ✅ Package marker

tests/
└── ops/
    ├── test_launch_checks.py   ✅ 20+ test cases
    └── __init__.py             ✅ Package marker

.github/
└── workflows/
    └── launch-checks.yml       ✅ CI workflow
```

---

## Dependencies

```
requests>=2.31.0
pyyaml>=6.0
pytest>=7.4.0
pydantic>=2.0.0
jsonschema>=4.19.0
stripe>=5.5.0
```

Install with:
```bash
pip install -U requests pyyaml pytest pydantic jsonschema stripe
```

---

## Next Steps

### 1. Initial Setup

```bash
# Configure environment
cp ops/launch_checks/env.example ops/launch_checks/.env
# Edit .env with your actual values

# Generate fixtures
python ops/fixtures/generate_oversized.py

# Run first check
./ops/launch_checks/verify.sh
```

### 2. GitHub Secrets

Add to repository secrets:
- `STAGING_API_BASE`
- `TEST_TENANT_ID`
- `STRIPE_TEST_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- (Optional: QBO/Xero credentials)

### 3. Enable Workflow

```bash
# Manual run
gh workflow run launch-checks.yml -f api_base=https://your-staging-api.com

# Or wait for nightly run at 2 AM UTC
```

### 4. Review Reports

```bash
# View latest report
cat ops/reports/$(ls -t ops/reports | head -1)/report.md

# Check JSON
jq . ops/reports/$(ls -t ops/reports | head -1)/report.json
```

---

## Troubleshooting

### Issue: "API_BASE not configured"
**Fix:** Set `API_BASE` in `.env` or export it:
```bash
export API_BASE=https://your-api.com
```

### Issue: All optional checks skipped
**Expected:** This is normal if integration credentials not configured
**Action:** No action needed unless you want to test integrations

### Issue: PII redaction check fails
**Fix:** Verify `app/logging/redaction.py` is active and middleware configured

### Issue: Idempotency checks fail
**Fix:** Check implementation of idempotency logic in API
**Verify:** Database has unique constraints on idempotency keys

### Issue: 500 errors on malformed CSV
**Fix:** Add try/catch in CSV parsing code, return 4xx instead of crashing

---

## Success Criteria

### ✅ All Implemented
- [x] 16 files created
- [x] 11 checks implemented
- [x] JSON Schema validation
- [x] CI/CD workflow
- [x] Comprehensive documentation
- [x] Unit and E2E tests
- [x] Fixtures for all scenarios
- [x] POSIX-compliant shell wrapper
- [x] Markdown report generation
- [x] Graceful error handling

### ✅ Production Ready
- [x] No hardcoded URLs or keys
- [x] Environment-based configuration
- [x] Deterministic output
- [x] Fail-fast with clear errors
- [x] Runs locally and in CI
- [x] Zero secrets in repo

---

## Conclusion

The launch checks verification harness is **complete and production-ready**. All acceptance criteria met, all deliverables implemented, and ready for immediate use.

**To start using:**
```bash
./ops/launch_checks/verify.sh
```

**Report generated at:**
```
ops/reports/<timestamp>/report.md
```

---

**Implementation Date:** October 30, 2025  
**Status:** ✅ COMPLETE  
**Ready for:** Production deployment verification



