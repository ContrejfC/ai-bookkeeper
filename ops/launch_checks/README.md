# Launch Checks - Pre-Production Verification Harness

## Overview

Automated end-to-end verification suite that validates AI-Bookkeeper deployment readiness before accepting paid traffic. Runs health checks, integration tests, security validations, and generates comprehensive reports.

## Quick Start

```bash
# 1. Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -U requests pytest pydantic pyyaml stripe jsonschema

# 2. Configure environment
cp ops/launch_checks/env.example ops/launch_checks/.env
# Edit .env with your values

# 3. Run checks
./ops/launch_checks/verify.sh
```

## Configuration

### Environment Variables

Required variables in `.env`:

- `API_BASE` - Base URL of deployed API (e.g., `https://api.example.com`)
- `TEST_TENANT_ID` - Test tenant UUID for validation

Optional integration variables (checks skip if missing):

- `STRIPE_SECRET_KEY` - Stripe test key for idempotency checks
- `STRIPE_WEBHOOK_SECRET` - For webhook signature verification
- `WEBHOOK_URL` - App webhook endpoint (e.g., `https://<api-base>/api/webhooks/stripe`)
- `QBO_REALM_ID`, `QBO_CLIENT_ID`, `QBO_CLIENT_SECRET`, `QBO_REFRESH_TOKEN`
- `XERO_TENANT_ID`, `XERO_CLIENT_ID`, `XERO_CLIENT_SECRET`, `XERO_REFRESH_TOKEN`
- `TEST_USERNAME`, `TEST_PASSWORD` - For auth flow testing

### config.yaml

Override defaults:

```yaml
api_base: "${API_BASE}"
tenant_id: "${TEST_TENANT_ID}"
demo_mode: true
date_from: "2024-01-01"
date_to: "2024-12-31"
timeout_seconds: 30
endpoints:
  health: "/healthz"
  ready: "/readyz"
  audit_export: "/api/audit/export"
  upload: "/api/upload"
  propose: "/api/post/propose"
  webhook: "/api/billing/stripe_webhook"
  qbo_export: "/api/export/qbo/demo"
  xero_export: "/api/export/xero/demo"
```

## Checks Implemented

### 1. Health & Readiness
- `GET /healthz` returns 200 with ok status
- `GET /readyz` returns 200 with database connectivity

### 2. CORS & Auth Security
- Response headers include proper security settings
- Cookies have `HttpOnly`, `Secure`, `SameSite=Lax`

### 3. Stripe Idempotency
- Duplicate checkout sessions return identical IDs
- Webhook events process once despite duplicate POSTs

### 4. QBO/Xero Demo Posting
- Journal entries post successfully in demo mode
- Duplicate posts are idempotent (same external ID)

### 5. AI Threshold Gate
- Low-confidence categorizations flagged for review
- Unbalanced journal entries rejected

### 6. PII Redaction
- Logs and exports redact emails, SSNs, phone numbers
- No raw PII in API responses

### 7. Audit Export
- CSV export generates with proper headers
- Date range filtering works

### 8. Ingestion Robustness
- Malformed CSV returns 4xx with clear error
- Oversized files handled gracefully (no 500s)

## Output

Each run creates timestamped directory:

```
ops/reports/2025-10-30T12-34-56Z/
├── report.json     # Machine-readable results
├── report.md       # Human-readable summary
├── audit.csv       # Sample audit export
└── artifacts/      # Additional evidence
```

### Report Structure

```json
{
  "timestamp_utc": "2025-10-30T12:34:56Z",
  "api_base": "https://api.example.com",
  "summary": {
    "pass": 8,
    "fail": 0,
    "skip": 2,
    "total": 10
  },
  "checks": [
    {
      "name": "healthz",
      "status": "PASS",
      "duration_ms": 45,
      "details": {"status_code": 200, "response": {...}},
      "evidence": "Health endpoint responded with ok=true"
    }
  ],
  "artifacts": [
    {"path": "audit.csv", "description": "Sample audit export"}
  ]
}
```

## Exit Codes

- `0` - All REQUIRED checks passed
- `1` - One or more REQUIRED checks failed
- `2` - Configuration error
- `3` - Runtime error

## CI/CD Integration

GitHub Actions workflow runs:
- On manual trigger (`workflow_dispatch`)
- Nightly at 2 AM UTC
- On `release/*` tags

```bash
# Trigger manually
gh workflow run launch-checks.yml

# View results
gh run list --workflow=launch-checks.yml
```

Artifacts uploaded:
- `report.json`
- `report.md`
- `audit.csv`

## Common Failure Modes

### 1. Health Check Fails
**Symptom:** `healthz` returns 5xx or times out  
**Fix:** Verify deployment is running, check logs

### 2. Stripe Idempotency Fails
**Symptom:** Duplicate requests return different IDs  
**Fix:** Check Stripe key, verify idempotency implementation

### 3. PII Redaction Fails
**Symptom:** Raw emails/SSNs in responses  
**Fix:** Verify redaction middleware is active

### 4. Webhook Signature Fails
**Symptom:** 401/403 on webhook POST  
**Fix:** Check `STRIPE_WEBHOOK_SECRET` matches deployment

### 5. Audit Export Empty
**Symptom:** CSV has headers but no data  
**Fix:** Verify test tenant has audit logs in date range

## Local Development

Run individual checks:

```python
from ops.launch_checks.checks import run_health_check, load_config

config = load_config('ops/launch_checks/config.yaml')
result = run_health_check(config)
print(result)
```

Run with pytest:

```bash
# All tests
pytest tests/ops/test_launch_checks.py -v

# Only unit tests (skip e2e)
pytest tests/ops/test_launch_checks.py -v -m "not e2e"

# Only e2e tests
pytest tests/ops/test_launch_checks.py -v -m e2e
```

## Validation

Validate report structure:

```bash
python - <<'PY'
import json, sys, jsonschema
jsonschema.validate(
    json.load(open('ops/reports/<timestamp>/report.json')),
    json.load(open('ops/launch_checks/report_schema.json'))
)
print("✓ Valid")
PY
```

## Extending Checks

Add new check in `checks.py`:

```python
def run_my_check(config: Config) -> CheckResult:
    """Check description."""
    start = time.time()
    try:
        # Perform check
        response = http_get(f"{config.api_base}/my/endpoint")
        
        return CheckResult(
            name="my_check",
            status="PASS",
            duration_ms=int((time.time() - start) * 1000),
            details={"response": response.json()},
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

Register in `run_all_checks()`:

```python
checks.append(run_my_check(config))
```

## Troubleshooting

### Debug Mode

```bash
export DEBUG=1
./ops/launch_checks/verify.sh
```

### Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Skip External Checks

Don't set optional env vars - checks will SKIP gracefully:

```bash
# Only run health/internal checks
unset STRIPE_SECRET_KEY
unset QBO_CLIENT_ID
./ops/launch_checks/verify.sh
```

## Support

For issues:
1. Check `ops/reports/<timestamp>/report.md` for details
2. Review `report.json` for full context
3. Enable debug mode and re-run
4. Check API logs for server-side errors

## Operational Guarantees

- **Required checks must PASS**: Optional checks may SKIP when secrets are absent
- **HTTP timeouts**: 10s connect, 10s read with 3 automatic retries and jitter backoff
- **Report retention**: Last 20 runs kept automatically, older reports pruned
- **Error capture**: Failed requests include 4KiB body samples for debugging
- **Exit codes**: 0=success, 1=required failures, 2=config error, 3=runtime error
- **Idempotency**: All checks are safe to re-run without side effects

## License

Part of AI-Bookkeeper internal tooling.

