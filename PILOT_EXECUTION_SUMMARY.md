# Pilot Enablement — Execution Summary

**Date:** 2024-10-11  
**Status:** Ready to Execute

---

## Part A: Pilot Enablement Scripts

All scripts are ready and executable. Follow these steps:

### Step 1: Create Pilot Tenants (5 min)

```bash
cd /path/to/ai-bookkeeper
python3 scripts/create_pilot_tenants.py
```

**Expected Output:**
```
✅ Created 3 pilot tenants
- pilot-smb-001 (SMB, threshold 0.90, budget $50)
- pilot-prof-002 (Professional, threshold 0.92, budget $75)  
- pilot-firm-003 (Accounting Firm, threshold 0.88, budget $100)
```

**Verify:**
```sql
SELECT tenant_id, autopost_enabled, autopost_threshold, llm_tenant_cap_usd 
FROM tenant_settings 
WHERE tenant_id LIKE 'pilot-%';
```

---

### Step 2: Test Notifications (2 min)

```bash
python3 scripts/test_notifications.py
```

**Expected Output:**
```
✅ Tested 3/3 tenants
- Notifications logged in dry-run mode
- Check notification_log table
```

**Verify:**
```sql
SELECT tenant_id, notification_type, channel, status 
FROM notification_log 
WHERE tenant_id LIKE 'pilot-%';
```

---

### Step 3: Generate Shadow Reports (2 min)

```bash
python3 scripts/generate_shadow_reports.py
```

**Expected Output:**
```
✅ Generated 3 shadow reports
- reports/shadow/pilot-smb-001_shadow_7d.json
- reports/shadow/pilot-prof-002_shadow_7d.json
- reports/shadow/pilot-firm-003_shadow_7d.json
```

**Note:** If no transaction data yet, reports will show 0 transactions. This is expected for new tenants.

---

### Step 4: Verify Analytics (2 min)

```bash
# Run manual rollup
python3 jobs/analytics_rollup.py

# Check output
ls -la reports/analytics/daily_*.json

# Test API
curl http://localhost:8000/api/analytics/last7

# View dashboard
open http://localhost:8000/analytics
```

**Expected:**
- Daily rollup file created
- API returns JSON array
- Dashboard renders with summary cards

---

### Step 5: Capture Screenshots (15-20 min)

Follow `SCREENSHOT_CAPTURE_GUIDE.md`:

1. **Start Server:**
   ```bash
   uvicorn app.api.main:app --port 8000
   ```

2. **Login as Owner** (use dev auth or configured credentials)

3. **Capture Onboarding (4 screenshots):**
   - Navigate to http://localhost:8000/onboarding
   - Screenshot Step 1 (CoA selection) → `artifacts/onboarding/step1_coa.png`
   - Click "Next", screenshot Step 2 (Data ingest) → `step2_ingest.png`
   - Click "Next", screenshot Step 3 (Settings) → `step3_settings.png`
   - Click "Next", screenshot Step 4 (Finish) → `step4_finish.png`

4. **Capture Receipts (1 screenshot):**
   - Navigate to http://localhost:8000/receipts
   - Click on a receipt to load overlays
   - Screenshot → `artifacts/receipts/overlay_sample.png`

5. **Capture Analytics (1 screenshot):**
   - Navigate to http://localhost:8000/analytics
   - Wait for data to load
   - Screenshot → `artifacts/analytics/dashboard.png`

---

### Step 6: Commit Artifacts

```bash
git add artifacts/ reports/shadow/
git commit -m "Add pilot enablement artifacts and shadow reports"
git push
```

---

## Acceptance Checklist

- [ ] 3 pilot tenants created with correct settings
- [ ] All have AUTOPOST=false
- [ ] Thresholds: 0.90, 0.92, 0.88
- [ ] Budgets: $50, $75, $100
- [ ] Notification settings configured
- [ ] Test notifications logged
- [ ] 3 shadow reports generated in `reports/shadow/`
- [ ] Analytics rollup job runs successfully
- [ ] `/analytics` shows last 7 days
- [ ] 6 screenshots captured and committed
- [ ] All artifacts committed to repo

---

## Summary

**Total Time:** 30-45 minutes (excluding screenshots)

**Scripts:**
1. ✅ `scripts/create_pilot_tenants.py`
2. ✅ `scripts/test_notifications.py`
3. ✅ `scripts/generate_shadow_reports.py`
4. ✅ `jobs/analytics_rollup.py` (existing)
5. ✅ `SCREENSHOT_CAPTURE_GUIDE.md` (manual process)

**Outputs:**
- `tenant_settings` table: 3 new rows
- `tenant_notifications` table: 3 new rows
- `notification_log` table: 3+ test entries
- `reports/shadow/`: 3 JSON files
- `reports/analytics/`: Daily rollup
- `artifacts/onboarding/`: 4 PNG files
- `artifacts/receipts/`: 1 PNG file
- `artifacts/analytics/`: 1 PNG file

**Next:** Proceed to Sprint 10 implementation (S10.2 + S10.4)

