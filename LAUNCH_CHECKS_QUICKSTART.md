# Launch Checks - Quick Start Guide

## Overview

Pre-launch verification harness that runs 11 automated checks against your deployed API and generates detailed reports.

## Setup (5 minutes)

### 1. Install Dependencies

```bash
cd /Users/fabiancontreras/ai-bookkeeper

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install packages
pip install -U requests pyyaml pytest pydantic jsonschema stripe
```

### 2. Configure Environment

```bash
# Copy template
cp ops/launch_checks/env.example ops/launch_checks/.env

# Edit with your values
nano ops/launch_checks/.env
```

**Minimum required:**
```bash
API_BASE=https://your-api-url.com
TEST_TENANT_ID=your-tenant-uuid
```

### 3. Generate Test Fixtures (Optional)

```bash
# Generate 100k-row CSV for robustness testing
python ops/fixtures/generate_oversized.py
```

## Run Checks

### Local Execution

```bash
./ops/launch_checks/verify.sh
```

Output appears in: `ops/reports/<timestamp>/`

### View Results

```bash
# Find latest report
LATEST=$(ls -t ops/reports | head -1)

# View Markdown summary
cat ops/reports/$LATEST/report.md

# View JSON (pretty-printed)
python3 -m json.tool ops/reports/$LATEST/report.json

# Quick summary view (just the key info)
last="$(ls -1 ops/reports | tail -1)"
echo "Last report: ops/reports/$last/report.md"
awk '/^## Summary/{flag=1;next}/^## /{if(flag)exit}flag' ops/reports/$last/report.md || head -80 "ops/reports/$last/report.md"
```

### Using Make Targets

```bash
# Run checks (easier than full path)
make launch-checks

# View summary of last run
make launch-checks-summary
```

## Interpreting Results

### Exit Codes

- **0** = All required checks passed ✅
- **1** = Required check(s) failed ❌
- **2** = Configuration error ⚙️
- **3** = Runtime error 💥

### Check Statuses

- **PASS** ✅ = Check succeeded
- **FAIL** ❌ = Check failed (investigate)
- **SKIP** ⏭️ = Check skipped (credentials not configured)

### Sample Output

```
=== AI-Bookkeeper Launch Checks ===

Loading environment from ops/launch_checks/.env
Creating report directory: ops/reports/2025-10-30T12-34-56Z
Running checks against: https://api.example.com

✓ All required checks passed!

Reports generated:
  JSON: ops/reports/2025-10-30T12-34-56Z/report.json
  Markdown: ops/reports/2025-10-30T12-34-56Z/report.md
```

## What Gets Checked

### Required Checks (Must Pass)

1. ✅ **Health** - `/healthz` returns 200
2. ✅ **Readiness** - `/readyz` confirms DB connection
3. ✅ **CORS/Security** - Proper cookie attributes
4. ✅ **AI Thresholds** - Low-confidence flagged, entries balanced
5. ✅ **PII Redaction** - Emails/SSNs/phones redacted
6. ✅ **Ingestion** - Malformed/oversized files handled gracefully

### Optional Checks (Skip if Not Configured)

7. ⏭️ **Stripe Idempotency** - Duplicate requests return same ID
8. ⏭️ **Webhook Idempotency** - Duplicate events processed once
9. ⏭️ **QBO Demo** - Journal posts are idempotent
10. ⏭️ **Xero Demo** - Journal posts are idempotent
11. ⏭️ **Audit Export** - CSV generates correctly

## Common Issues

### "API_BASE not configured"

**Fix:**
```bash
export API_BASE=https://your-api.com
# Or add to .env file
```

### All Optional Checks Skipped

**Normal!** Optional checks skip when integration credentials aren't configured.

**To enable:**
1. Add credentials to `.env` (see `env.example`)
2. Re-run checks

### Check Fails with 401/403

**Cause:** Endpoint requires authentication

**Options:**
1. Add `TEST_USERNAME` and `TEST_PASSWORD` to `.env`
2. Or expect that check to skip (if optional)

### PII Redaction Fails

**Action:** Verify `app/logging/redaction.py` middleware is active

**Check:** Response should contain `***EMAIL***`, not raw emails

## CI/CD Integration

### GitHub Actions

Already configured! Workflow runs:
- **Manually** - via Actions UI
- **Nightly** - at 2 AM UTC
- **On Release** - when pushing release tags

### Trigger Manually

```bash
gh workflow run launch-checks.yml \
  -f api_base=https://your-staging-api.com \
  -f required_mode=true
```

### View Results

1. Go to: Actions → Launch Checks
2. Click latest run
3. Download artifacts: `launch-checks-report-...`
4. Extract and view `report.md`

## Testing the Harness Itself

### Run Unit Tests

```bash
pytest tests/ops/test_launch_checks.py -v
```

### Run E2E Tests (Requires Live API)

```bash
export API_BASE=https://your-api.com
export TEST_TENANT_ID=your-tenant-uuid

pytest tests/ops/test_launch_checks.py -v -m e2e
```

### Skip E2E Tests

```bash
pytest tests/ops/test_launch_checks.py -v -m "not e2e"
```

## Advanced Usage

### Custom Configuration

Edit `ops/launch_checks/config.yaml`:

```yaml
# Change timeouts
timeout_seconds: 60

# Modify endpoints
endpoints:
  health: "/custom-health"
  ready: "/custom-ready"

# Adjust thresholds
ai_thresholds:
  min_confidence: 0.7
```

### Run Specific Checks Only

Modify `checks.py` to comment out checks you don't need:

```python
def run_all_checks(config: Config, output_dir: Path) -> Report:
    checks = []
    
    checks.append(run_health_check(config))
    checks.append(run_readiness_check(config))
    # checks.append(run_stripe_idempotency_check(config))  # Skip this
    # ... etc
```

### Validate Report Schema

```bash
python - ops/reports/<timestamp>/report.json <<'PY'
import sys, json, jsonschema
jsonschema.validate(
    json.load(open(sys.argv[1])),
    json.load(open('ops/launch_checks/report_schema.json'))
)
print("✓ Report structure valid")
PY
```

## Files Reference

```
ops/
├── launch_checks/
│   ├── README.md              # Full documentation
│   ├── env.example            # Environment template
│   ├── config.yaml            # Configuration
│   ├── verify.sh              # Run this!
│   ├── checks.py              # Main implementation
│   └── report_schema.json     # JSON schema
└── fixtures/
    ├── sample_small.csv       # 20-row sample
    ├── sample_malformed.csv   # Bad formatting
    ├── pii_probe.csv          # PII patterns
    └── *.json                 # Stripe/QBO/Xero samples

tests/ops/test_launch_checks.py  # Test suite
.github/workflows/launch-checks.yml  # CI workflow
```

## Next Steps

1. ✅ Run checks locally: `./ops/launch_checks/verify.sh`
2. ✅ Review report: `cat ops/reports/<timestamp>/report.md`
3. ✅ Fix any failures
4. ✅ Configure CI secrets (if using GitHub Actions)
5. ✅ Run nightly checks automatically

## Support

- **Full docs:** `ops/launch_checks/README.md`
- **Implementation details:** `LAUNCH_CHECKS_IMPLEMENTATION.md`
- **Config reference:** `ops/launch_checks/config.yaml`

---

**Ready to verify your deployment?**

```bash
./ops/launch_checks/verify.sh
```

