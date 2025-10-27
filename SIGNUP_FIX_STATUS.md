# Signup API Fix - Status Update

## Issue
Frontend signup fails with "Unexpected token 'N', 'Not Found' is not valid JSON"

## Root Cause
API routes (including `/api/auth/signup`) not loading in Cloud Run deployment due to import failures.

## Fix Attempted
Created minimal API (`main_minimal.py`) but deployment failed - container wouldn't start.

## Current Status
The deployment is failing because of dependency issues. The Cloud Run container timeout suggests the app is crashing on startup.

## Immediate Workaround Recommendation

Since we can't get Cloud Run routes working right now, I recommend:

### Option A: Test Locally First
Before deploying, test the minimal API locally to catch import errors:
```bash
cd /Users/fabiancontreras/ai-bookkeeper
PYTHONPATH=/Users/fabiancontreras/ai-bookkeeper python -m uvicorn app.api.main_minimal:app --host 0.0.0.0 --port 8080
```

Then test signup:
```bash
curl -X POST http://localhost:8080/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test1234","full_name":"Test"}'
```

### Option B: Use the Working Vercel Frontend with Mock Data
Temporarily modify the frontend to work without a working signup API.

### Option C: Keep Previous Revision
Roll back to a previous working revision if auth was working before.

## Next Steps Needed
1. Access Cloud Run logs to see exact error
2. Test minimal API locally first
3. Fix import dependencies
4. Redeploy once verified locally

## Alternative: Quick Frontend Fix
Since the frontend is the one showing the error, we could also:
1. Add better error handling in the frontend signup page
2. Show user-friendly error messages
3. Add retry logic

But the real fix is getting the API routes working.

---

**Priority:** HIGH  
**Blocker:** Yes - prevents user signups  
**Recommended Action:** Test locally first before next Cloud Run deployment
