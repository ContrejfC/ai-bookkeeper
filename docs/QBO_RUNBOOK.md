# QuickBooks Online Integration - Operations Runbook
**Version:** 1.0  
**Date:** 2025-10-17  
**Status:** Production Ready

## Overview

This runbook covers QuickBooks Online (QBO) OAuth2 integration, token management, and idempotent journal entry posting.

## Quick Reference

### Endpoints
- `GET /api/auth/qbo/start` - Initialize OAuth flow (302 redirect)
- `GET /api/auth/qbo/callback` - OAuth callback handler
- `GET /api/qbo/status` - Connection status
- `POST /api/qbo/journalentry` - Post journal entry idempotently

### Environment Variables
```bash
QBO_CLIENT_ID=your_client_id
QBO_CLIENT_SECRET=your_client_secret
QBO_REDIRECT_URI=https://your-domain.com/api/auth/qbo/callback
QBO_SCOPES=com.intuit.quickbooks.accounting
QBO_BASE=https://sandbox-quickbooks.api.intuit.com  # or production URL
```

---

## Intuit App Setup (Sandbox)

### Step 1: Create Intuit Developer Account

1. Go to https://developer.intuit.com
2. Sign up for developer account
3. Navigate to "My Apps" dashboard

### Step 2: Create App

1. Click "Create an app"
2. Select "QuickBooks Online and Payments"
3. App name: "AI Bookkeeper" (or your choice)
4. Choose scopes: **Accounting**

### Step 3: Configure OAuth

1. In app settings, find "Keys & OAuth"
2. Add Redirect URI: `https://your-domain.com/api/auth/qbo/callback`
   - For local testing: `http://localhost:8000/api/auth/qbo/callback`
3. Copy "Client ID" and "Client Secret"
4. Save settings

### Step 4: Set Environment Variables

```bash
# Add to .env
QBO_CLIENT_ID=ABcd1234567890
QBO_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxx
QBO_REDIRECT_URI=http://localhost:8000/api/auth/qbo/callback
QBO_SCOPES=com.intuit.quickbooks.accounting
QBO_BASE=https://sandbox-quickbooks.api.intuit.com
```

---

## OAuth Flow

### Step 1: Initialize OAuth

```bash
# User clicks "Connect QuickBooks" in UI
# Or via cURL (will return redirect URL)
curl -X GET "http://localhost:8000/api/auth/qbo/start" \
  -H "Authorization: Bearer $TOKEN" \
  -v
  
# Response: 302 redirect to:
# https://appcenter.intuit.com/connect/oauth2?client_id=...&scope=...&state=...
```

### Step 2: User Authorizes App

1. User is redirected to Intuit authorization page
2. User selects QuickBooks company
3. User clicks "Authorize"
4. Intuit redirects back to callback URL

### Step 3: Callback Processes Tokens

```bash
# Intuit calls:
# GET /api/auth/qbo/callback?code=AB12345&realmId=123456789&state=...

# Backend:
# 1. Exchanges code for tokens
# 2. Stores tokens in database
# 3. Redirects user to /dashboard?qbo=connected
```

### Step 4: Verify Connection

```bash
curl -X GET "http://localhost:8000/api/qbo/status" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "connected": true,
  "realm_id": "123456789",
  "token_age_sec": 120,
  "expires_in_sec": 3480
}
```

---

## Posting Journal Entries

### Format

```bash
curl -X POST "http://localhost:8000/api/qbo/journalentry" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "txnDate": "2025-10-16",
    "refNumber": "AB-1001",
    "privateNote": "AI Bookkeeper",
    "lines": [
      {
        "amount": 150.00,
        "postingType": "Debit",
        "accountRef": {"value": "46"}
      },
      {
        "amount": 150.00,
        "postingType": "Credit",
        "accountRef": {"value": "7"}
      }
    ]
  }'
```

### Responses

**First Post (201 Created):**
```json
{
  "status": 201,
  "qbo_doc_id": "12345",
  "idempotent": false,
  "message": "Journal entry posted successfully"
}
```

**Duplicate Post (200 OK):**
```json
{
  "status": 200,
  "qbo_doc_id": "12345",
  "idempotent": true,
  "message": "Journal entry already posted (idempotent)"
}
```

### Idempotency Rules

- Payload hash computed from: txnDate, refNumber, privateNote, normalized lines
- Lines normalized: sorted by amount+account, rounded to 2 decimals
- Same hash → returns existing qbo_doc_id without posting again
- Prevents duplicate JE creation in QuickBooks

---

## Error Handling

### 400 - Unbalanced Entry
```json
{
  "code": "UNBALANCED_JE",
  "message": "Debits (150.00) must equal credits (100.00)"
}
```

**Fix:** Ensure sum of debits equals sum of credits

### 401 - Not Connected
```json
{
  "code": "QBO_UNAUTHORIZED",
  "message": "QuickBooks not connected. Please connect your QuickBooks account."
}
```

**Fix:** Complete OAuth flow via `/api/auth/qbo/start`

### 422 - Validation Error
```json
{
  "code": "QBO_VALIDATION",
  "message": "Account 999 not found in chart of accounts"
}
```

**Fix:** Use valid account codes from your QuickBooks chart of accounts

### 429 - Rate Limited
```json
{
  "code": "QBO_RATE_LIMITED",
  "message": "QuickBooks API rate limit reached. Retry after 60 seconds.",
  "retry_after": 60
}
```

**Fix:** Wait and retry after specified seconds

### 502 - Upstream Error
```json
{
  "code": "QBO_UPSTREAM",
  "message": "QuickBooks API unavailable. Please try again shortly."
}
```

**Fix:** QuickBooks API is down, retry later

---

## Token Management

### Automatic Token Refresh

- Tokens expire after 1 hour
- System automatically refreshes when expired or expiring within 5 minutes
- Refresh updates database and logs audit event
- Failed refresh returns 401 QBO_UNAUTHORIZED

### Manual Token Check

```sql
-- Check token expiration
SELECT 
  tenant_id,
  realm_id,
  expires_at,
  CAST((julianday(expires_at) - julianday('now')) * 24 * 60 * 60 AS INTEGER) as expires_in_sec
FROM qbo_tokens;
```

### Manual Token Refresh

```python
# scripts/refresh_qbo_tokens.py
from app.db.session import get_db_context
from app.services.qbo import QBOService
import asyncio

async def refresh_tenant_tokens(tenant_id: str):
    with get_db_context() as db:
        service = QBOService(db)
        try:
            access_token, realm_id = await service.get_fresh_token(tenant_id)
            print(f"✓ Tokens refreshed for tenant {tenant_id}")
        except Exception as e:
            print(f"✗ Refresh failed: {e}")

if __name__ == "__main__":
    import sys
    asyncio.run(refresh_tenant_tokens(sys.argv[1]))
```

---

## Testing

### Test with Sandbox Company

1. **Create Sandbox Company**
   - Go to https://developer.intuit.com/app/developer/qbo/docs/get-started/start-developing-your-app
   - Click "Create a sandbox company"
   - Note the Company ID (realmId)

2. **Connect via OAuth**
   ```bash
   # Start OAuth flow
   curl -L "http://localhost:8000/api/auth/qbo/start" \
     -H "Authorization: Bearer $TOKEN"
   ```

3. **Post Test Journal Entry**
   ```bash
   curl -X POST "http://localhost:8000/api/qbo/journalentry" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "txnDate": "2025-10-17",
       "refNumber": "TEST-001",
       "lines": [
         {"amount": 100.00, "postingType": "Debit", "accountRef": {"value": "1"}},
         {"amount": 100.00, "postingType": "Credit", "accountRef": {"value": "30"}}
       ]
     }'
   ```

4. **Verify Idempotency**
   ```bash
   # Post same entry again - should return 200 with idempotent=true
   curl -X POST "http://localhost:8000/api/qbo/journalentry" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "txnDate": "2025-10-17",
       "refNumber": "TEST-001",
       "lines": [
         {"amount": 100.00, "postingType": "Debit", "accountRef": {"value": "1"}},
         {"amount": 100.00, "postingType": "Credit", "accountRef": {"value": "30"}}
       ]
     }'
   ```

5. **Verify in QuickBooks**
   - Log in to sandbox company
   - Navigate to "Transactions" > "Journal Entries"
   - Verify entry appears only once

---

## Production Migration

### Step 1: Switch to Production

1. Create production Intuit app
2. Update redirect URI to production domain
3. Copy production Client ID and Secret

```bash
# Update .env with production values
QBO_CLIENT_ID=production_client_id
QBO_CLIENT_SECRET=production_client_secret  
QBO_REDIRECT_URI=https://ai-bookkeeper-web.onrender.com/api/auth/qbo/callback
QBO_BASE=https://quickbooks.api.intuit.com  # Production URL
```

### Step 2: Deploy

```bash
# Set environment variables in Render dashboard
# Deploy to production
git push origin main
```

### Step 3: Test with Production Company

- Complete OAuth flow with real QuickBooks company
- Post test journal entry
- Verify in QuickBooks Online

---

## Monitoring

### Token Expiration Monitoring

```sql
-- Find tokens expiring soon
SELECT 
  tenant_id,
  realm_id,
  expires_at,
  CAST((julianday(expires_at) - julianday('now')) * 24 * 60 * 60 AS INTEGER) as expires_in_sec
FROM qbo_tokens
WHERE expires_at < datetime('now', '+1 hour');
```

### Idempotency Stats

```sql
-- Count idempotent vs new posts
SELECT 
  DATE(created_at) as date,
  COUNT(*) as total_posts,
  COUNT(DISTINCT tenant_id) as unique_tenants
FROM je_idempotency
WHERE created_at >= DATE('now', '-7 days')
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Audit Trail

```sql
-- QBO-related audit events
SELECT 
  timestamp,
  tenant_id,
  action
FROM decision_audit_log
WHERE action LIKE 'QBO_%'
ORDER BY timestamp DESC
LIMIT 50;
```

---

## Troubleshooting

### Issue: OAuth Redirect Not Working

**Symptoms:** Callback never receives code parameter

**Check:**
1. Verify redirect URI in Intuit app matches QBO_REDIRECT_URI exactly
2. Check app is in correct mode (Sandbox vs Production)
3. Verify SSL certificate if using HTTPS

**Fix:**
```bash
# Update redirect URI in Intuit app dashboard
# Restart application after env change
```

### Issue: Token Expired Error

**Symptoms:** 401 QBO_UNAUTHORIZED on API calls

**Diagnosis:**
```sql
SELECT tenant_id, expires_at 
FROM qbo_tokens 
WHERE expires_at < datetime('now');
```

**Fix:** Tokens should auto-refresh. If not:
```python
# Manual refresh
python scripts/refresh_qbo_tokens.py tenant_123
```

### Issue: Duplicate Journal Entries in QuickBooks

**Symptoms:** Same entry appears multiple times

**Diagnosis:**
```sql
-- Check idempotency records
SELECT * FROM je_idempotency 
WHERE tenant_id = 'tenant_123'
ORDER BY created_at DESC;
```

**Cause:** Idempotency check may have failed

**Prevention:** System uses hash-based idempotency to prevent duplicates

---

## Security

### Token Storage
- Access tokens stored in database (consider encryption for production)
- Refresh tokens stored securely
- Tokens never logged or exposed in API responses
- Auto-refresh on expiration

### Audit Logging
- All OAuth connections logged: `QBO_CONNECTED`
- All token refreshes logged: `QBO_TOKEN_REFRESHED`
- All JE posts logged: `QBO_JE_POSTED` (with idempotent flag)
- Tokens masked in all logs

### Rate Limiting
- Respects QBO rate limits with backoff
- Returns 429 with retry_after on rate limit
- Implements exponential backoff for retries

---

## cURL Examples

### Complete OAuth Flow

```bash
# 1. Get authorization URL
curl -X GET "http://localhost:8000/api/auth/qbo/start" \
  -H "Authorization: Bearer $TOKEN" \
  -L  # Follow redirect

# 2. User completes authorization in browser
# 3. Check connection status
curl -X GET "http://localhost:8000/api/qbo/status" \
  -H "Authorization: Bearer $TOKEN"
```

### Post Journal Entry

```bash
# Simple journal entry
curl -X POST "http://localhost:8000/api/qbo/journalentry" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "txnDate": "2025-10-17",
    "refNumber": "JE-001",
    "privateNote": "Office supplies purchase",
    "lines": [
      {"amount": 250.00, "postingType": "Debit", "accountRef": {"value": "46"}},
      {"amount": 250.00, "postingType": "Credit", "accountRef": {"value": "33"}}
    ]
  }'
```

### Complex Multi-Line Entry

```bash
curl -X POST "http://localhost:8000/api/qbo/journalentry" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "txnDate": "2025-10-17",
    "refNumber": "JE-002",
    "lines": [
      {"amount": 500.00, "postingType": "Debit", "accountRef": {"value": "1"}},
      {"amount": 300.00, "postingType": "Debit", "accountRef": {"value": "46"}},
      {"amount": 800.00, "postingType": "Credit", "accountRef": {"value": "30"}}
    ]
  }'
```

---

## Account Codes Reference

Common QuickBooks account codes (varies by company):

| Code | Account Name | Type |
|------|--------------|------|
| 1 | Checking | Bank |
| 7 | Accounts Receivable | Accounts Receivable |
| 30 | Accounts Payable | Accounts Payable |
| 33 | Cash | Bank |
| 46 | Office Supplies | Expense |
| 50 | Advertising | Expense |
| 60 | Utilities | Expense |

**Get actual codes:**
```bash
# API call to fetch chart of accounts (requires implementation)
curl -X GET "http://localhost:8000/api/qbo/chart-of-accounts" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Troubleshooting Commands

### Check Connection Status
```bash
sqlite3 ai_bookkeeper_demo.db "SELECT tenant_id, realm_id, datetime(expires_at) as expires FROM qbo_tokens;"
```

### Check Idempotency Records
```bash
sqlite3 ai_bookkeeper_demo.db "SELECT tenant_id, substr(payload_hash,1,16) as hash, qbo_doc_id, datetime(created_at) FROM je_idempotency ORDER BY created_at DESC LIMIT 10;"
```

### Check QBO Audit Logs
```bash
sqlite3 ai_bookkeeper_demo.db "SELECT datetime(timestamp), tenant_id, action FROM decision_audit_log WHERE action LIKE 'QBO%' ORDER BY timestamp DESC LIMIT 20;"
```

---

## GPT Actions Integration

### Workflow

1. **Check Billing Status**
   ```
   GET /api/billing/status
   → If not active, show paywall
   ```

2. **Check QBO Connection**
   ```
   GET /api/qbo/status
   → If not connected, prompt "Connect QuickBooks"
   ```

3. **Connect QuickBooks** (if needed)
   ```
   GET /api/auth/qbo/start
   → User completes OAuth in browser
   ```

4. **Post Journal Entry**
   ```
   POST /api/qbo/journalentry
   → Returns qbo_doc_id
   ```

### GPT Prompt Examples

**When not connected:**
> "To post to QuickBooks, you need to connect your QuickBooks account. Click **Connect QuickBooks** to authorize access."

**After connection:**
> "QuickBooks connected! I can now post journal entries to your company (ID: 123456789). What would you like to post?"

**After posting:**
> "Posted journal entry to QuickBooks (Doc ID: 12345). This entry has been safely recorded and won't be duplicated if you retry."

---

## Commit Flow Integration

The `/post/commit` endpoint aggregates approved journal entries and posts them to QuickBooks with idempotency.

### Endpoint: POST /api/post/commit

**Request:**
```json
{
  "approvals": [
    {
      "txn_id": "t1",
      "je": {
        "txnDate": "2025-10-17",
        "refNumber": "AB-1001",
        "privateNote": "AI Bookkeeper",
        "lines": [
          {"amount": 150.00, "postingType": "Debit", "accountRef": {"value": "46"}},
          {"amount": 150.00, "postingType": "Credit", "accountRef": {"value": "7"}}
        ]
      }
    }
  ]
}
```

**Response (Success):**
```json
{
  "results": [
    {
      "txn_id": "t1",
      "qbo_doc_id": "12345",
      "idempotent": false,
      "status": "posted"
    }
  ],
  "summary": {
    "total": 1,
    "posted": 1,
    "errors": 0
  }
}
```

**Response (Mixed):**
```json
{
  "results": [
    {
      "txn_id": "t1",
      "qbo_doc_id": "12345",
      "idempotent": false,
      "status": "posted"
    },
    {
      "txn_id": "t2",
      "status": "error",
      "error": {
        "code": "UNBALANCED_JE",
        "message": "Debits (150.00) must equal credits (100.00)"
      }
    }
  ],
  "summary": {
    "total": 2,
    "posted": 1,
    "errors": 1
  }
}
```

### Behavior

1. **Per-Item Processing:** Each approval is processed independently
2. **No Short-Circuit:** Errors in one item don't block others
3. **Idempotency:** Duplicate payloads return existing qbo_doc_id
4. **Usage Tracking:** Only non-idempotent posts increment monthly counter
5. **Global Gates:** Middleware blocks entire request if subscription inactive or over cap (402)

### Example cURL

```bash
curl -X POST "http://localhost:8000/api/post/commit" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approvals": [
      {
        "txn_id": "office_supplies_001",
        "je": {
          "txnDate": "2025-10-17",
          "refNumber": "OS-001",
          "lines": [
            {"amount": 250.00, "postingType": "Debit", "accountRef": {"value": "46"}},
            {"amount": 250.00, "postingType": "Credit", "accountRef": {"value": "33"}}
          ]
        }
      }
    ]
  }'
```

---

## Appendix: Testing Checklist

- [ ] OAuth flow completes successfully
- [ ] Tokens stored in database
- [ ] Connection status shows connected
- [ ] First JE post returns 201
- [ ] Duplicate JE post returns 200 with idempotent=true
- [ ] Unbalanced JE returns 400
- [ ] Token auto-refreshes on expiration
- [ ] Audit logs capture all QBO events
- [ ] No tokens leaked in logs or error responses

---

**END OF RUNBOOK**
