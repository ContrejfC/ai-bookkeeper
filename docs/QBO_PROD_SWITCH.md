# QuickBooks Online Production Switch Guide

**Purpose:** Transition from QuickBooks Sandbox to Production environment for real customer data access.

---

## Prerequisites

- [ ] QuickBooks Online Developer account
- [ ] Sandbox OAuth flow working correctly
- [ ] Test transactions posted successfully to sandbox
- [ ] Ready to access real customer QuickBooks data

---

## Step 1: Create Production App

### 1.1 Via Intuit Developer Portal

1. Go to [Intuit Developer Portal](https://developer.intuit.com/)
2. Sign in with your Intuit account
3. Navigate to **My Apps**
4. Click **Create an app** (or use existing app)

### 1.2 App Configuration

**App Name:** AI Bookkeeper for QuickBooks  
**Description:** Automate journal entry proposals and posting to QuickBooks Online  
**App Type:** Web app (OAuth 2.0)

**Scopes Required:**
- `com.intuit.quickbooks.accounting` - Full accounting access (read/write journal entries)

**⚠️ Important:** Do NOT select "QuickBooks App Store" unless you plan marketplace distribution. For direct customer integration, use standard OAuth app.

### 1.3 Set Redirect URIs

**Production Redirect URI:**
```
https://YOUR_PRODUCTION_DOMAIN/api/auth/qbo/callback
```

**Development/Staging (optional):**
```
https://staging.yourdomain.com/api/auth/qbo/callback
http://localhost:8000/api/auth/qbo/callback
```

### 1.4 Get Production Credentials

After saving:
1. Click **Keys & OAuth**
2. Toggle to **Production** (top right)
3. Copy **Client ID** and **Client Secret**
4. **⚠️ Save these securely** - you'll need them for environment variables

---

## Step 2: Verify Production Settings

### 2.1 Check App Settings

- [ ] Production redirect URI matches your deployed domain
- [ ] Scopes include `com.intuit.quickbooks.accounting`
- [ ] App is **not** in "Development" mode (should be "Production")

### 2.2 Environment Base URLs

**Sandbox:**
- Auth: `https://appcenter.intuit.com/connect/oauth2`
- API: `https://sandbox-quickbooks.api.intuit.com/v3/company/{realmId}/...`

**Production:**
- Auth: `https://appcenter.intuit.com/connect/oauth2` (same)
- API: `https://quickbooks.api.intuit.com/v3/company/{realmId}/...`

**Key Difference:** Remove `sandbox-` from API base URL.

---

## Step 3: Update Environment Variables

### In Render (or your hosting platform)

```bash
# QuickBooks OAuth Credentials (PRODUCTION)
QBO_CLIENT_ID=ABxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
QBO_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# QuickBooks Settings
QBO_REDIRECT_URI=https://YOUR_PRODUCTION_DOMAIN/api/auth/qbo/callback
QBO_SCOPES=com.intuit.quickbooks.accounting
QBO_ENVIRONMENT=production  # or set QBO_BASE directly

# API Base URL (Production)
QBO_BASE=https://quickbooks.api.intuit.com
QBO_AUTH_BASE=https://appcenter.intuit.com/connect/oauth2
```

**⚠️ After updating, redeploy your application!**

---

## Step 4: Verify QBO Environment

### 4.1 Run Environment Check Script

```bash
python scripts/check_qbo_env.py
```

**Expected output:**
```
======================================================================
  QuickBooks Environment Verification
======================================================================

✅ QBO_CLIENT_ID present
✅ QBO_CLIENT_SECRET present
✅ QBO_REDIRECT_URI present (https://...)
✅ QBO_SCOPES present
✅ QBO_BASE present (https://quickbooks.api.intuit.com)
✅ Environment: PRODUCTION

======================================================================
  All checks passed
======================================================================
```

### 4.2 Sanity Check API Base

The script will attempt to verify the QBO base URL is reachable (no auth required, just connectivity check).

---

## Step 5: Test Production OAuth Flow

### 5.1 Initiate Connection

```bash
# Get OAuth start URL
curl https://YOUR_PRODUCTION_DOMAIN/api/auth/qbo/start \
     -H "Authorization: Bearer YOUR_API_KEY"

# Response should include authorization_url
{
  "authorization_url": "https://appcenter.intuit.com/connect/oauth2?..."
}
```

### 5.2 Complete OAuth Flow

1. Open the `authorization_url` in a browser
2. Sign in with a **real QuickBooks account** (not sandbox)
3. Select a company to authorize
4. Click **Connect**
5. You'll be redirected to your callback URL
6. Token will be stored automatically

### 5.3 Verify Connection

```bash
curl https://YOUR_PRODUCTION_DOMAIN/api/qbo/status \
     -H "Authorization: Bearer YOUR_API_KEY"

# Expected response:
{
  "connected": true,
  "realm_id": "xxxxxxxxxx",
  "environment": "production"
}
```

---

## Step 6: Test Production Posting

### 6.1 Test Journal Entry (Small Amount)

```bash
curl -X POST https://YOUR_PRODUCTION_DOMAIN/api/post/commit \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "approvals": [
         {
           "txn_id": "prod_test_1",
           "je": {
             "txnDate": "2025-10-17",
             "refNumber": "PROD-TEST-001",
             "privateNote": "AI Bookkeeper - Production Test",
             "lines": [
               {
                 "amount": 0.01,
                 "postingType": "Debit",
                 "accountRef": {"value": "46"}
               },
               {
                 "amount": 0.01,
                 "postingType": "Credit",
                 "accountRef": {"value": "7"}
               }
             ]
           }
         }
       ]
     }'

# Expected: HTTP 200 with qbo_doc_id
```

**⚠️ Use a test amount ($0.01) for first production post!**

### 6.2 Verify in QuickBooks

1. Log into QuickBooks Online
2. Go to **Transactions** → **Journal Entries**
3. Find entry with ref number `PROD-TEST-001`
4. Verify:
   - Amount: $0.01
   - Note: "AI Bookkeeper - Production Test"
   - Status: Posted

### 6.3 Test Idempotency

```bash
# Repeat the same request
curl -X POST ... (same payload as above)

# Expected: HTTP 200 with idempotent:true
{
  "results": [
    {
      "txn_id": "prod_test_1",
      "qbo_doc_id": "123",
      "idempotent": true,
      "status": "posted"
    }
  ]
}
```

---

## Step 7: Monitor & Verify

### 7.1 Check Application Logs

```bash
# In Render or your logs
grep "QBO" logs/app.log

# Should see:
# "QBO OAuth completed: realm_id=xxxxx"
# "Posted JE to QBO: doc_id=123"
# "QBO token refreshed successfully"
```

### 7.2 Check QBO Token Storage

```bash
# Verify token stored (via API or DB)
curl https://YOUR_PRODUCTION_DOMAIN/api/qbo/status \
     -H "Authorization: Bearer YOUR_API_KEY"

# Should show connected:true with realm_id
```

### 7.3 Test Token Refresh

Tokens expire after 1 hour (access) and 100 days (refresh). The system should auto-refresh.

**Manual test:** Wait 1 hour, then try posting another JE. Should work without re-auth.

---

## Rollback Plan

If issues occur after switching to production:

### Option 1: Revert to Sandbox

1. In Render, update environment variables back to sandbox credentials
2. Update `QBO_BASE=https://sandbox-quickbooks.api.intuit.com`
3. Update `QBO_CLIENT_ID` and `QBO_CLIENT_SECRET` to sandbox values
4. Redeploy
5. Test sandbox OAuth flow

### Option 2: Revoke Production Connection

1. In QuickBooks, go to **Settings** → **Apps**
2. Find "AI Bookkeeper" (or your app name)
3. Click **Disconnect**
4. This revokes all tokens
5. Customer can re-authorize after fixes

---

## Common Issues

### Issue: OAuth Error "Invalid Redirect URI"

**Cause:** Production redirect URI doesn't match Intuit app settings

**Fix:**
1. Go to Intuit Developer Portal → Your App → Keys & OAuth
2. Verify redirect URI exactly matches (including https://, no trailing slash)
3. Wait 5-10 minutes for changes to propagate
4. Retry OAuth flow

### Issue: "Unauthorized" When Posting

**Cause:** Sandbox token used with production base URL (or vice versa)

**Fix:**
1. Disconnect QBO in app
2. Verify `QBO_BASE` environment variable
3. Re-authorize with production account
4. Token storage should now have production realm_id

### Issue: Token Refresh Failed

**Cause:** Refresh token expired (100 days) or revoked

**Fix:**
1. Customer must re-authorize
2. Provide link: `GET /api/auth/qbo/start`
3. Complete OAuth flow again

---

## Security Checklist

- [ ] Production client secret never committed to git
- [ ] Production client secret stored securely (Render env vars)
- [ ] Tokens encrypted at rest in database
- [ ] Token refresh logs mask sensitive data
- [ ] HTTPS enforced for redirect URI
- [ ] Production app not in "Development" mode

---

## Scope Differences (Sandbox vs Production)

| Feature | Sandbox | Production |
|---------|---------|------------|
| Real customer data | ❌ No | ✅ Yes |
| Test company | ✅ Yes | ❌ No |
| API rate limits | Relaxed | Enforced (500 req/min) |
| Token expiry | Same (1h/100d) | Same |
| Data persistence | Test data | Real accounting data |

---

## Production Best Practices

1. **Start Small:** Test with $0.01 amounts first
2. **Monitor Closely:** Check logs for first week
3. **Customer Communication:** Inform users about QuickBooks connection
4. **Rate Limiting:** Respect QBO API limits (500 req/min)
5. **Error Handling:** Log all QBO errors, retry 429s
6. **Token Management:** Refresh proactively before expiry
7. **Audit Trail:** Maintain je_idempotency table for compliance

---

## Final Verification Checklist

- [ ] Production app created in Intuit portal
- [ ] Redirect URI configured correctly
- [ ] Environment variables updated in Render
- [ ] Application redeployed
- [ ] `scripts/check_qbo_env.py` passes
- [ ] OAuth flow completes with real QBO account
- [ ] Test journal entry posts successfully ($0.01)
- [ ] Entry visible in QuickBooks dashboard
- [ ] Idempotency works (repeat post)
- [ ] Token refresh tested (after 1 hour)
- [ ] Logs show no errors

---

## Support & Resources

- **Intuit Developer Docs:** https://developer.intuit.com/app/developer/qbo/docs
- **OAuth 2.0 Guide:** https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/oauth-2.0
- **API Reference:** https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/journalentry
- **Rate Limits:** https://developer.intuit.com/app/developer/qbo/docs/develop/rest-api-rate-limiting

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-17  
**Applicable to:** AI Bookkeeper v0.9.1+

