# 🔧 Fix: "Error loading access information"

## Problem

The frontend pages (transactions, export, upload) are showing **"Error loading access information"** because the frontend cannot reach the backend `/api/billing/entitlements` endpoint.

## Root Cause

The frontend deployed on Vercel is missing the `NEXT_PUBLIC_API_URL` environment variable, which tells it where to find the backend API.

**Frontend URL:** https://ai-bookkeeper-nine.vercel.app  
**Backend API URL:** https://ai-bookkeeper-api-ww4vg3u7eq-uc.a.run.app

Without this configuration, the frontend defaults to `http://localhost:8000` which doesn't exist in production.

## Solution

### Step 1: Configure Vercel Environment Variable

1. Go to **Vercel Dashboard**: https://vercel.com/dashboard
2. Select your project: `ai-bookkeeper`
3. Go to **Settings** → **Environment Variables**
4. Add the following variable:

```
Name: NEXT_PUBLIC_API_URL
Value: https://ai-bookkeeper-api-ww4vg3u7eq-uc.a.run.app
Environment: Production
```

5. Click **Save**

### Step 2: Redeploy Frontend

After adding the environment variable, you need to redeploy:

**Option A: Trigger via Git Push (Recommended)**
```bash
cd /Users/fabiancontreras/ai-bookkeeper
git commit --allow-empty -m "Trigger redeploy with API URL env var"
git push origin main
```

**Option B: Manual Redeploy in Vercel**
1. Go to **Deployments** tab
2. Click the three dots on the latest deployment
3. Select **Redeploy**

### Step 3: Verify the Fix

After redeployment completes (~2 minutes):

1. Open https://ai-bookkeeper-nine.vercel.app/transactions
2. Open browser DevTools (F12)
3. Go to **Network** tab
4. Refresh the page
5. Look for a request to `/api/billing/entitlements`
6. Verify it's calling: `https://ai-bookkeeper-api-ww4vg3u7eq-uc.a.run.app/api/billing/entitlements`

**Expected Result:** 
- If authenticated: Status 200 with entitlements data
- If not authenticated: Status 401 (which is expected - you need to login first)

## Additional Issue: CORS Configuration

The backend also needs to allow requests from the Vercel frontend. Check if this is configured:

### Verify Backend CORS Settings

The backend needs to have Vercel's URL in its `ALLOWED_ORIGINS` environment variable.

**In Google Cloud Run:**

1. Go to **Google Cloud Console**: https://console.cloud.google.com/run
2. Select service: `ai-bookkeeper-api`
3. Click **Edit & Deploy New Revision**
4. Go to **Variables & Secrets** tab
5. Find or add `ALLOWED_ORIGINS` variable:

```
Name: ALLOWED_ORIGINS
Value: https://ai-bookkeeper-nine.vercel.app,https://app.ai-bookkeeper.app
```

6. Click **Deploy**

## Testing Authentication Flow

Once both fixes are deployed, test the full flow:

### 1. Login
```bash
# Open the frontend
open https://ai-bookkeeper-nine.vercel.app/login

# Login with test credentials
# The backend should set an HTTP-only cookie with JWT token
```

### 2. Check Cookie
- Open DevTools → Application → Cookies
- Verify there's a cookie named `access_token` or `session`
- Domain should be `.run.app` or the backend domain

### 3. Test Protected Page
```bash
# Navigate to transactions page
open https://ai-bookkeeper-nine.vercel.app/transactions

# Should now load without "Error loading access information"
```

## Common Issues

### Issue 1: Cookie Not Being Set
**Symptom:** Login works but pages still show error  
**Cause:** Backend cookie is set for wrong domain  
**Fix:** Check backend's cookie settings include `SameSite=None` and `Secure=True` for cross-origin cookies

### Issue 2: CORS Errors
**Symptom:** Browser console shows CORS errors  
**Cause:** Backend doesn't allow Vercel origin  
**Fix:** Add Vercel URL to `ALLOWED_ORIGINS` (see above)

### Issue 3: 403 "No tenant access"
**Symptom:** Entitlements endpoint returns 403  
**Cause:** User account has no tenants assigned  
**Fix:** 
```bash
# SSH into backend or use Cloud Run terminal
# Run migration to create default tenant for user
```

## Quick Test Commands

```bash
# Test backend health
curl https://ai-bookkeeper-api-ww4vg3u7eq-uc.a.run.app/healthz

# Test entitlements endpoint (requires authentication)
curl https://ai-bookkeeper-api-ww4vg3u7eq-uc.a.run.app/api/billing/entitlements \
  -H "Cookie: access_token=YOUR_TOKEN" \
  --cookie-jar cookies.txt
```

## Summary

**Immediate Actions:**
1. ✅ Add `NEXT_PUBLIC_API_URL` to Vercel environment variables
2. ✅ Redeploy frontend
3. ✅ Verify `ALLOWED_ORIGINS` in backend includes Vercel URL
4. ✅ Test login and protected pages

**Expected Timeline:** 5-10 minutes

---

## Need Help?

If the issue persists after these steps, check:
1. Browser DevTools Network tab for failed requests
2. Backend logs in Google Cloud Run console
3. Verify user has tenant_ids in the database

Run this diagnostic:
```bash
# Check what URL the frontend is using
curl https://ai-bookkeeper-nine.vercel.app/_next/static/chunks/*.js | grep NEXT_PUBLIC_API_URL
```

