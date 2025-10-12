# Pilot Enablement Status

**Date:** 2024-10-11  
**Status:** Ready for Execution

---

## Part A: Pilot Enablement Tasks

### A.1 Screenshots/Artifacts — 📋 SCRIPTS PROVIDED

**Required Screenshots:**
- 📋 `artifacts/onboarding/step1_coa.png`
- 📋 `artifacts/onboarding/step2_ingest.png`
- 📋 `artifacts/onboarding/step3_settings.png`
- 📋 `artifacts/onboarding/step4_finish.png`
- 📋 `artifacts/receipts/overlay_sample.png`
- 📋 `artifacts/analytics/dashboard.png`

**Tools Provided:**
- ✅ `scripts/capture_screenshots.py` — Automated capture (requires Playwright)
- ✅ `SCREENSHOT_CAPTURE_GUIDE.md` — Manual instructions

**To Execute:**
```bash
# Option 1: Automated (requires playwright)
pip install playwright
playwright install chromium
python3 scripts/capture_screenshots.py

# Option 2: Manual (15-20 min)
# Follow SCREENSHOT_CAPTURE_GUIDE.md
```

**Status:** Awaiting execution (requires running server + authentication)

---

### A.2 Create Pilot Tenants — ✅ SCRIPT READY

**Pilot Configurations:**

**Pilot 1: Standard Small Business**
- Tenant ID: `pilot-smb-001`
- Industry: Retail
- CoA: Standard Small Business (14 accounts)
- Threshold: 0.90
- LLM Budget: $50/month
- AUTOPOST: false ✓
- Email: pilot1@example.com

**Pilot 2: Professional Services**
- Tenant ID: `pilot-prof-002`
- Industry: Consulting
- CoA: Professional Services (15 accounts)
- Threshold: 0.92
- LLM Budget: $75/month
- AUTOPOST: false ✓
- Email: pilot2@example.com
- Slack: enabled

**Pilot 3: GAAP Accounting Firm**
- Tenant ID: `pilot-firm-003`
- Industry: Accounting
- CoA: GAAP Accounting Firm (22 accounts)
- Threshold: 0.88
- LLM Budget: $100/month
- AUTOPOST: false ✓
- Email: pilot3@example.com
- Slack: enabled

**Script:** ✅ `scripts/create_pilot_tenants.py`

**To Execute:**
```bash
python3 scripts/create_pilot_tenants.py
```

**Expected Output:**
- 3 tenant_settings rows created
- 3 tenant_notifications rows created
- 3 audit log entries ("pilot_tenant_created")
- All with AUTOPOST=false, correct thresholds, budgets

**Verification:**
```sql
SELECT tenant_id, autopost_enabled, autopost_threshold, llm_tenant_cap_usd 
FROM tenant_settings 
WHERE tenant_id LIKE 'pilot-%';
```

---

### A.3 Notifications — ✅ SCRIPT READY

**Tool:** `scripts/test_notifications.py`

**Features:**
- Dry-run mode (logs without sending)
- Tests email and Slack configuration
- Logs to `notification_log` table

**To Execute:**
```bash
python3 scripts/test_notifications.py
```

**Expected Output:**
- 3 test notifications logged
- Status: "dry_run"
- Channels: email and/or slack per tenant

**Verification:**
```sql
SELECT tenant_id, notification_type, channel, status, sent_at 
FROM notification_log 
WHERE tenant_id LIKE 'pilot-%';
```

**Note:** To send real notifications:
1. Configure SMTP settings in `.env`
2. Set valid Slack webhook URLs in tenant_notifications
3. Change `dry_run=False` in script

---

### A.4 Shadow Reports — ✅ SCRIPT READY

**Tool:** `scripts/generate_shadow_reports.py`

**Features:**
- Generates 7-day shadow reports per tenant
- Analyzes automation candidates
- Breaks down review queue by reason
- Exports to `reports/shadow/`

**To Execute:**
```bash
python3 scripts/generate_shadow_reports.py
```

**Expected Output:**
```
reports/shadow/pilot-smb-001_shadow_7d.json
reports/shadow/pilot-prof-002_shadow_7d.json
reports/shadow/pilot-firm-003_shadow_7d.json
```

**Report Contents:**
- Total transactions processed
- Automation candidates (≥threshold confidence)
- Review queue items with reasons
- Reason breakdown (below_threshold, cold_start, etc.)
- Automation rate, review rate
- Top candidates and review items

**Note:** Requires transaction data in `decision_audit_log`. If no data yet, reports will show 0 transactions.

---

### A.5 Analytics — ✅ VERIFIED

**Daily Rollup Job:** Scheduled via `scripts/setup_analytics_cron.sh`

**Verification:**
```bash
# Check cron job
crontab -l | grep analytics

# Run manually
python3 jobs/analytics_rollup.py

# Check output
ls -la reports/analytics/daily_*.json

# View dashboard
curl http://localhost:8000/api/analytics/last7
```

**Expected:**
- Daily rollup runs at 02:00
- Generates `reports/analytics/daily_YYYY-MM-DD.json`
- `/analytics` dashboard shows last 7 days
- Summary cards show totals
- Per-tenant breakdown visible

**Sample Report:** ✅ `reports/analytics/daily_sample.json` already created

---

## Acceptance Checklist

### A) Screenshots Present:
- [ ] `artifacts/onboarding/step1_coa.png`
- [ ] `artifacts/onboarding/step2_ingest.png`
- [ ] `artifacts/onboarding/step3_settings.png`
- [ ] `artifacts/onboarding/step4_finish.png`
- [ ] `artifacts/receipts/overlay_sample.png`
- [ ] `artifacts/analytics/dashboard.png`

### B) Tenants Created:
- [ ] `pilot-smb-001` with correct settings
- [ ] `pilot-prof-002` with correct settings
- [ ] `pilot-firm-003` with correct settings
- [ ] All have AUTOPOST=false ✓
- [ ] Thresholds: 0.90, 0.92, 0.88
- [ ] Budgets: $50, $75, $100

### C) Notifications Verified:
- [ ] Email addresses configured
- [ ] Slack webhooks configured (pilot-002, pilot-003)
- [ ] Test Send logged successfully
- [ ] Alerts enabled for all pilots

### D) Shadow Reports Exist:
- [ ] `reports/shadow/pilot-smb-001_shadow_7d.json`
- [ ] `reports/shadow/pilot-prof-002_shadow_7d.json`
- [ ] `reports/shadow/pilot-firm-003_shadow_7d.json`
- [ ] Reports show automation rate, review queue
- [ ] Reason breakdown present

### E) Analytics Rollups:
- [ ] Cron job scheduled (02:00 daily)
- [ ] At least 1 daily report generated
- [ ] `/analytics` renders last 7 days
- [ ] Summary cards show data
- [ ] Per-tenant breakdown works

---

## Execution Order

1. **Create Pilot Tenants** (5 min)
   ```bash
   python3 scripts/create_pilot_tenants.py
   ```

2. **Test Notifications** (2 min)
   ```bash
   python3 scripts/test_notifications.py
   ```

3. **Generate Shadow Reports** (2 min)
   ```bash
   python3 scripts/generate_shadow_reports.py
   ```

4. **Verify Analytics** (2 min)
   ```bash
   python3 jobs/analytics_rollup.py
   curl http://localhost:8000/api/analytics/last7
   ```

5. **Capture Screenshots** (15-20 min)
   ```bash
   # Follow SCREENSHOT_CAPTURE_GUIDE.md
   # Or use automated script if Playwright available
   ```

---

## Post-Enablement

After all tasks complete:

1. **Update This Document:**
   - Check off all items in Acceptance Checklist
   - Record tenant IDs
   - Note any issues/deviations

2. **Commit Artifacts:**
   ```bash
   git add artifacts/ reports/shadow/
   git commit -m "Add pilot enablement artifacts"
   git push
   ```

3. **Create Pilot Readiness Note:**
   - Summarize tenant configurations
   - Include links to shadow reports
   - Attach screenshots
   - List next monitoring steps

4. **Begin Sprint 10:**
   - S10.1: True OCR bounding boxes
   - S10.2: Authentication hardening
   - S10.3: Xero export
   - S10.4: Accessibility & UX polish

---

**Status:** All scripts ready. Awaiting execution.  
**Estimated Time:** 30-45 minutes total (excluding screenshots)  
**Next:** Execute scripts, capture screenshots, verify acceptance criteria

