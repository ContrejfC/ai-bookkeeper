# Onboarding Wizard — Quick Start Guide

**Version:** 1.0  
**Phase:** 2b.1  
**Status:** Production-Ready

---

## Overview

The Onboarding Wizard is a 4-step guided process for setting up new tenants in AI Bookkeeper. It creates a fully-configured tenant in shadow mode, ready for transaction review.

---

## Access

**URL:** `/onboarding`

**Requirements:**
- Must be logged in
- Must have Owner role
- Staff users will receive 403 Forbidden

---

## Wizard Steps

### Step 1: Chart of Accounts

Choose how to set up your accounts:

**Option A: Use a Template**
- Standard Small Business (14 accounts)
- Professional Services (15 accounts)
- GAAP Accounting Firm (22 accounts)

**Option B: Upload CSV**
- Format: `account_code,account_name,account_type`
- Example:
  ```csv
  1000,Cash,Asset
  2000,Accounts Payable,Liability
  4000,Sales Revenue,Revenue
  ```

### Step 2: Data Ingest

Upload your historical data:

**Transactions** (required):
- Formats: CSV, OFX, QFX
- Recommended: Last 6-12 months
- Columns: date, description, amount, category (optional)

**Receipts** (optional):
- Formats: PDF, TXT
- Multiple files supported
- System will extract date, amount, vendor

### Step 3: Safety Settings

Configure guardrails:

**Auto-Post Threshold:**
- Range: 0.80 to 0.98
- Default: 0.90 (recommended)
- Only transactions with calibrated confidence ≥ threshold are eligible for auto-posting

**LLM Budget:**
- Monthly cap per tenant (USD)
- Default: $50/month
- System falls back to Rules/ML when exceeded

**Auto-Post Status:**
- ⚠️ Always DISABLED after onboarding
- Tenant starts in shadow mode for safety
- Enable manually after reviewing system performance

### Step 4: Tips & Finish

Quick tips to get started:

**Keyboard Shortcuts:**
- `A` — Approve transaction
- `R` — Reject transaction
- `E` — View explanation

**Shadow Mode:**
- All suggestions require manual review
- System learns from your corrections
- Auto-rules promoted from high-precision patterns

**Monitoring:**
- Visit `/metrics` to track automation rate
- Check `/firm` console for health indicators

**Action:** Click "Start Reviewing Transactions" to proceed to `/review`

---

## Result

After completing onboarding:

✅ **Tenant Created:**
- Unique tenant ID: `onboarded-{random}`
- Chart of Accounts loaded
- Settings persisted to database

✅ **Safety First:**
- AUTOPOST disabled (shadow mode)
- Threshold configured but not active
- LLM budget cap in place

✅ **Data Loaded:**
- Transactions ingested
- Receipts uploaded (if provided)
- Ready for categorization

✅ **Audit Trail:**
- Event: `onboarding_complete`
- Actor: {user_id}
- Timestamp: {ISO8601}

---

## Technical Details

### API Endpoint

**`POST /api/onboarding/complete`**

**Authentication:** Bearer token (Owner role required)

**Request:** `multipart/form-data`
```
coa_method: "template" | "upload"
coa_template: string (if method=template)
autopost_threshold: float (0.80-0.98)
llm_budget: float
coa_file: file (if method=upload)
transactions_file: file (optional)
receipts: file[] (optional)
```

**Response:**
```json
{
  "success": true,
  "tenant_id": "onboarded-abc123",
  "summary": {
    "coa_method": "template",
    "coa_accounts": 14,
    "transactions": 120,
    "receipts": 35,
    "autopost_enabled": false,
    "autopost_threshold": 0.90,
    "llm_budget": 50.0
  }
}
```

### Database Tables Updated

- `tenant_settings` — New row created
- `decision_audit_log` — Event logged

### RBAC

- ✅ Owner: Full access
- ❌ Staff: 403 Forbidden

---

## Resume Later

The wizard supports saving progress:

1. Click "Resume Later" at any step
2. Progress saved to browser localStorage
3. Return to `/onboarding` to continue
4. Progress restored automatically

**Saved Fields:**
- Current step
- CoA method + template selection
- Threshold + budget values

**Not Saved:**
- File uploads (must re-select)

---

## Testing

Run onboarding tests:

```bash
pytest tests/test_onboarding.py -v
```

**Expected:** 5/5 tests passing

**Tests:**
1. Settings + CoA persisted
2. AUTOPOST disabled by default
3. Redirects to review on finish
4. Staff blocked (RBAC)
5. File uploads handled

---

## Screenshots

See `artifacts/onboarding/`:
- `step1_coa.png` — Chart of Accounts selection
- `step2_ingest.png` — Data upload
- `step3_settings.png` — Safety configuration
- `step4_finish.png` — Tips and finish

---

## Troubleshooting

**Issue:** "403 Forbidden"  
**Solution:** Ensure you're logged in as Owner, not Staff

**Issue:** "Invalid CoA template"  
**Solution:** Template name must be exact match (see Step 1)

**Issue:** File upload fails  
**Solution:** Check file format (CSV/OFX for transactions, PDF/TXT for receipts)

**Issue:** Wizard stuck on step  
**Solution:** Check browser console for errors; ensure all required fields filled

---

## Next Steps

After onboarding:

1. **Review Transactions:** `/review?tenant_id={id}`
2. **Monitor Performance:** `/metrics?tenant_id={id}`
3. **Configure Rules:** `/rules` (as system learns)
4. **Enable Auto-Post:** When ready, via `/firm` console

---

## Support

**Documentation:**
- `PHASE2B_COMPLETE.md` — Full technical details
- `tests/test_onboarding.py` — Usage examples

**Contact:**
- For issues, check `decision_audit_log` for error details

---

**Version:** 1.0  
**Last Updated:** 2024-10-11  
**Phase:** 2b.1 Onboarding Wizard

