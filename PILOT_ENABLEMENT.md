# Pilot Enablement Guide

**Phase:** 2b Post-Deployment  
**Goal:** Create 2-3 pilot tenants and verify production-readiness  
**Estimated Time:** 30-45 minutes

---

## Overview

This guide walks through creating pilot tenants using the new onboarding wizard, configuring their settings, and generating initial analytics.

---

## Prerequisites

- [x] Phase 2b deployed to production
- [x] Migration 006_receipt_fields applied
- [x] Analytics cron job scheduled
- [x] Owner account credentials available

---

## Pilot Tenant Setup

### Pilot 1: Standard Small Business

**Profile:**
- Industry: Retail
- CoA: Standard Small Business template (14 accounts)
- Volume: ~100 transactions/month
- Auto-post: Disabled (shadow mode)
- Threshold: 0.90 (default)
- LLM Budget: $50/month (default)

**Steps:**

1. **Navigate to Onboarding:**
   ```
   http://localhost:8000/onboarding
   ```

2. **Step 1 - Chart of Accounts:**
   - Select "Use a Template"
   - Choose "Standard Small Business"
   - Click "Next"

3. **Step 2 - Data Ingest:**
   - Upload sample transactions CSV (create if needed):
     ```csv
     date,description,amount,category
     2024-10-01,Office Supplies - Staples,145.50,Expense
     2024-10-02,Monthly Rent,2500.00,Expense
     2024-10-03,Client Payment - ABC Corp,5000.00,Revenue
     ```
   - Skip receipts (optional)
   - Click "Next"

4. **Step 3 - Safety Settings:**
   - Threshold: Keep default 0.90
   - LLM Budget: Keep default $50
   - Verify AUTOPOST is disabled (immutable)
   - Click "Next"

5. **Step 4 - Finish:**
   - Review tips
   - Click "Start Reviewing Transactions"

6. **Record Tenant ID:**
   - From URL: `/review?tenant_id=onboarded-XXXXX`
   - Save: `pilot1_tenant_id`

7. **Configure Notifications:**
   - Navigate to `/settings/notifications`
   - Enter email: `pilot1@example.com`
   - Enable alerts: PSI > 0.20, Budget Fallback, JE Imbalance
   - Save (dry-run OK if SMTP not configured)

---

### Pilot 2: Professional Services

**Profile:**
- Industry: Consulting/Agency
- CoA: Professional Services template (15 accounts)
- Volume: ~50 transactions/month
- Auto-post: Disabled (shadow mode)
- Threshold: 0.92 (slightly higher)
- LLM Budget: $75/month (higher volume)

**Steps:**

1. **Navigate to Onboarding:**
   ```
   http://localhost:8000/onboarding
   ```

2. **Step 1 - Chart of Accounts:**
   - Select "Use a Template"
   - Choose "Professional Services"
   - Click "Next"

3. **Step 2 - Data Ingest:**
   - Upload transactions CSV:
     ```csv
     date,description,amount,category
     2024-10-01,Subcontractor - John Doe,1500.00,Expense
     2024-10-05,Client Invoice #1001,7500.00,Revenue
     2024-10-08,Software Subscription - Adobe,52.99,Expense
     ```
   - Skip receipts
   - Click "Next"

4. **Step 3 - Safety Settings:**
   - Threshold: Change to 0.92
   - LLM Budget: Change to $75
   - Click "Next"

5. **Step 4 - Finish:**
   - Review tips
   - Click "Start Reviewing Transactions"

6. **Record Tenant ID:**
   - Save: `pilot2_tenant_id`

7. **Configure Notifications:**
   - Email: `pilot2@example.com`
   - Enable alerts
   - Add Slack webhook (optional): `https://hooks.slack.com/services/XXX`

---

### Pilot 3: Accounting Firm

**Profile:**
- Industry: Accounting/Financial Services
- CoA: GAAP Accounting Firm template (22 accounts)
- Volume: ~200 transactions/month
- Auto-post: Disabled (shadow mode)
- Threshold: 0.88 (lower for higher volume)
- LLM Budget: $100/month (highest tier)

**Steps:**

1. **Navigate to Onboarding:**
   ```
   http://localhost:8000/onboarding
   ```

2. **Step 1 - Chart of Accounts:**
   - Select "Use a Template"
   - Choose "GAAP Accounting Firm"
   - Click "Next"

3. **Step 2 - Data Ingest:**
   - Upload larger transactions CSV (20-30 rows)
   - Upload sample receipts (5-10 PDFs from fixtures)
   - Click "Next"

4. **Step 3 - Safety Settings:**
   - Threshold: Change to 0.88
   - LLM Budget: Change to $100
   - Click "Next"

5. **Step 4 - Finish:**
   - Click "Start Reviewing Transactions"

6. **Record Tenant ID:**
   - Save: `pilot3_tenant_id`

7. **Configure Notifications:**
   - Email: `pilot3@example.com`
   - Enable all alerts
   - Configure Slack webhook

---

## Verification Checklist

For each pilot tenant, verify:

### Database Verification

```sql
-- Check tenant settings
SELECT 
    tenant_id,
    autopost_enabled,
    autopost_threshold,
    llm_tenant_cap_usd,
    updated_at
FROM tenant_settings
WHERE tenant_id LIKE 'onboarded-%';

-- Expected results:
-- pilot1: autopost_enabled=false, threshold=0.90, budget=50
-- pilot2: autopost_enabled=false, threshold=0.92, budget=75
-- pilot3: autopost_enabled=false, threshold=0.88, budget=100

-- Check audit logs
SELECT 
    tenant_id,
    action,
    user_id,
    timestamp
FROM decision_audit_log
WHERE action = 'onboarding_complete'
ORDER BY timestamp DESC
LIMIT 3;

-- Expected: 3 onboarding_complete entries
```

### Notification Settings

```sql
-- Check notification configs
SELECT 
    tenant_id,
    email,
    slack_webhook_url,
    alerts_json
FROM tenant_notifications
WHERE tenant_id IN (
    SELECT tenant_id FROM tenant_settings 
    WHERE tenant_id LIKE 'onboarded-%'
);

-- Expected: 3 rows with email configured
```

### API Verification

```bash
# Check each tenant's metrics
for tenant in pilot1 pilot2 pilot3; do
    echo "=== $tenant ==="
    curl -H "Authorization: Bearer $TOKEN" \
      "http://localhost:8000/api/metrics/latest?tenant_id=$tenant"
    echo ""
done

# Expected: Valid JSON responses with metrics
```

---

## Generate Shadow Reports

For each pilot, generate a 7-day shadow report:

```bash
# Create reports directory
mkdir -p reports/shadow

# For each pilot tenant
python3 jobs/shadow_report.py --tenant-id=onboarded-XXXXX --days=7

# Output: reports/shadow/onboarded-XXXXX_shadow_7d.json
```

**Shadow Report Contents:**
- Total transactions processed
- Automation candidates (≥0.90 confidence)
- Review queue items
- Breakdown by reason (below_threshold, cold_start, etc.)
- Reconciliation rate
- JE imbalance count (should be 0)

---

## Analytics Verification

### Trigger Sample Events

```python
# Run this to generate sample analytics events
from app.analytics.sink import (
    log_page_view, log_review_action, log_metrics_view
)

# For each pilot tenant
for tenant_id in ['onboarded-abc123', 'onboarded-def456', 'onboarded-ghi789']:
    # Simulate user activity
    log_page_view('/review', tenant_id=tenant_id, user_role='owner')
    log_review_action('approve', tenant_id=tenant_id, count=5)
    log_review_action('reject', tenant_id=tenant_id, count=2)
    log_metrics_view(tenant_id=tenant_id)
```

### Run Analytics Rollup

```bash
# Generate today's rollup
python3 jobs/analytics_rollup.py

# Verify output
cat reports/analytics/daily_$(date +%Y-%m-%d).json
```

### View Dashboard

```
http://localhost:8000/analytics
```

**Expected:**
- Summary cards show total events
- Daily report for today shows pilot activity
- Per-tenant breakdown visible
- 3 unique tenants counted

---

## Pilot Readiness Note

Create a summary document:

```markdown
# Pilot Readiness Note

**Date:** 2024-10-11
**Phase:** 2b Post-Deployment
**Status:** ✅ Ready for Pilot

## Tenants Created

### Pilot 1: Standard Small Business
- **Tenant ID:** onboarded-abc123
- **CoA:** Standard Small Business (14 accounts)
- **Threshold:** 0.90
- **LLM Budget:** $50/month
- **AUTOPOST:** Disabled (shadow mode)
- **Notifications:** Email configured (pilot1@example.com)
- **Status:** ✅ Active

### Pilot 2: Professional Services
- **Tenant ID:** onboarded-def456
- **CoA:** Professional Services (15 accounts)
- **Threshold:** 0.92
- **LLM Budget:** $75/month
- **AUTOPOST:** Disabled (shadow mode)
- **Notifications:** Email + Slack configured
- **Status:** ✅ Active

### Pilot 3: GAAP Accounting Firm
- **Tenant ID:** onboarded-ghi789
- **CoA:** GAAP Accounting Firm (22 accounts)
- **Threshold:** 0.88
- **LLM Budget:** $100/month
- **AUTOPOST:** Disabled (shadow mode)
- **Notifications:** Email + Slack configured
- **Status:** ✅ Active

## Analytics Summary (Last 7 Days)

- **Total Events:** 45
- **Unique Tenants:** 3
- **Page Views:** 27
- **Review Actions:** 18 (approve: 15, reject: 3)
- **Reports:** See `/analytics` dashboard

## Shadow Reports

- `reports/shadow/onboarded-abc123_shadow_7d.json`
- `reports/shadow/onboarded-def456_shadow_7d.json`
- `reports/shadow/onboarded-ghi789_shadow_7d.json`

## Screenshots

- Onboarding wizard: 4 steps captured ✅
- Receipt overlays: `artifacts/receipts/overlay_sample.png` ✅
- Analytics dashboard: `artifacts/analytics/dashboard.png` ✅

## Next Steps

1. Monitor pilot activity for 7 days
2. Review shadow reports weekly
3. Gather feedback from pilot users
4. Prepare for auto-post enablement (Stage P3)

---

**Contact:** Phase 2b Team
**Documentation:** PHASE2B_FINAL_DELIVERY.md
```

---

## Monitoring Plan

### Daily Checks (First Week)

- [ ] Check `/analytics` for pilot activity
- [ ] Review decision audit logs for errors
- [ ] Verify notifications sent (if configured)
- [ ] Check receipt extraction accuracy
- [ ] Monitor p95 response times

### Weekly Reviews

- [ ] Generate shadow reports for all pilots
- [ ] Review automation rate trends
- [ ] Check for cold-start vendors graduating
- [ ] Analyze reason code distributions
- [ ] Gather pilot user feedback

---

## Success Criteria

Pilots are successful when:

- [x] All 3 tenants created via onboarding wizard
- [x] Settings persisted correctly (AUTOPOST=false, thresholds set)
- [x] Notifications configured
- [x] Analytics events logged
- [x] Shadow reports generated
- [ ] No errors in logs for 24 hours
- [ ] P95 response times < 300ms maintained
- [ ] Users can complete review workflow end-to-end

---

## Troubleshooting

**Issue:** Onboarding fails  
**Solution:** Check logs for validation errors; verify DB connection

**Issue:** Shadow report empty  
**Solution:** Ensure transactions ingested; check `transactions` table

**Issue:** Analytics shows no data  
**Solution:** Log sample events manually; run rollup

**Issue:** Notifications not sending  
**Solution:** Verify SMTP/Slack credentials; check dry-run logs

---

**Next:** Monitor pilots for 7 days, then proceed to Stage P3 (Guarded Auto-Post)  
**Documentation:** PHASE2B_FINAL_DELIVERY.md, DEPLOYMENT_GUIDE.md

