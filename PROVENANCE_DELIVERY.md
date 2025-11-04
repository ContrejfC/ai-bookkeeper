# 🚀 Deployment Provenance & Verification v1 - DELIVERY

## ✅ Implementation Complete

All code has been implemented, tested locally, and pushed to production (`main` branch).

**Git Commits:**
- `f4b0c3a` - feat: Add deployment provenance & verification system
- `097095a` - fix: Rename provenance routes to avoid Next.js private folder convention

**Status:** ⏳ Awaiting Vercel deployment (typically 2-5 minutes after push)

---

## 📦 Files Delivered

### New Files (7 total)
1. ✅ `frontend/app/api-version/route.ts` - Build provenance endpoint
2. ✅ `frontend/app/api-smoke/route.ts` - Runtime smoke test endpoint  
3. ✅ `frontend/components/BuildTag.tsx` - UI debug ribbon component
4. ✅ `scripts/smoke.js` - Standalone smoke test script
5. ✅ `.github/workflows/smoke.yml` - CI smoke test workflow
6. ✅ `DEPLOYMENT_PROVENANCE.md` - Complete documentation
7. ✅ `PROVENANCE_DELIVERY.md` - This delivery document

### Modified Files (3 total)
1. ✅ `frontend/app/layout.tsx` - Added BuildTag import and rendering
2. ✅ `frontend/package.json` - Added `smoke:prod` script
3. ✅ `.github/workflows/smoke.yml` - Scheduled smoke tests every 6 hours

---

## 🎯 Feature Summary

### 1. `/api-version` Endpoint
**Purpose:** Public JSON endpoint exposing build metadata

**What it returns:**
- Host, protocol, Vercel environment
- Git commit SHA, branch, repo, commit message
- Build timestamp
- SOC2 status, max rows config
- List of key pages and APIs

**Example:**
```json
{
  "name": "ai-bookkeeper",
  "host": "ai-bookkeeper-nine.vercel.app",
  "vercel": { "env": "production" },
  "git": {
    "commitSha": "097095a...",
    "commitRef": "main"
  }
}
```

### 2. `/api-smoke` Endpoint
**Purpose:** Server-side runtime validation

**What it checks:**
- ✅ Policy dates (Nov 3, 2025) in /privacy and /terms
- ✅ SOC2 compliance copy in /security
- ✅ API method guards (405 for wrong HTTP methods)
- ✅ UI controls on /free/categorizer

**Returns:**
- `200` if all assertions pass
- `500` if any assertion fails
- Detailed JSON with pass/fail per check

### 3. UI Build Tag (`?verify=1`)
**Purpose:** Visual confirmation of deployment

**Trigger:** Add `?verify=1` to any page URL

**Display:**
- Fixed bottom-right ribbon
- Shows: `sha: abc1234 • env: production`
- Styled with white background, drop shadow
- Only visible when `?verify=1` is set (or in dev mode)

### 4. Smoke Test Script
**Usage:**
```bash
# Test production
npm run smoke:prod

# Test custom host
HOST=https://preview.vercel.app node scripts/smoke.js
```

**Output:**
- Structured JSON
- ✅/❌ emoji summary
- Exit code 0 (pass) or 1 (fail)

### 5. GitHub Actions Workflow
**Triggers:**
- Manual (`workflow_dispatch`)
- Scheduled (every 6 hours)

**Actions:**
- Curls `/api-smoke` endpoint
- Parses JSON assertions
- Fails workflow if any check fails
- Posts results to GitHub Actions summary

---

## 🧪 Verification Instructions

### Step 1: Wait for Vercel Deployment
Check deployment status:
- Visit: https://vercel.com/contrejfcs-projects/ai-bookkeeper
- Look for "Ready" status (usually 2-5 min after push)
- Latest commit should be: `097095a`

### Step 2: Test `/api-version` Endpoint
```bash
curl -s https://ai-bookkeeper-nine.vercel.app/api-version | jq .
```

**Expected:**
- Status: `200 OK`
- Content-Type: `application/json`
- Body contains: `commitSha`, `host`, `vercel.env`

### Step 3: Test `/api-smoke` Endpoint
```bash
curl -s https://ai-bookkeeper-nine.vercel.app/api-smoke | jq .
```

**Expected:**
- Status: `200 OK` (or `500` if any check fails)
- Body contains: `assertions` object with 5 boolean values
- All assertions should be `true`

### Step 4: Verify UI Build Tag
Visit:
```
https://ai-bookkeeper-nine.vercel.app/free/categorizer?verify=1
```

**Expected:**
- Fixed ribbon bottom-right corner
- Text: `sha: 097095a • env: production`
- White background, gray border

### Step 5: Run Local Smoke Test
```bash
cd /Users/fabiancontreras/ai-bookkeeper
npm run smoke:prod
```

**Expected:**
```
🧪 Running smoke tests against: https://ai-bookkeeper-nine.vercel.app

{
  "base": "https://ai-bookkeeper-nine.vercel.app",
  "ok": true,
  "assertions": {
    "privacyDate": true,
    "termsDate": true,
    "soc2Copy": true,
    "apiUpload405": true,
    "uiControls": true
  }
}

==================================================
SMOKE TEST SUMMARY
==================================================
✅ PASS - privacyDate
✅ PASS - termsDate
✅ PASS - soc2Copy
✅ PASS - apiUpload405
✅ PASS - uiControls
==================================================
Overall: ✅ ALL TESTS PASSED
==================================================

Exit code: 0
```

---

## 📋 Acceptance Criteria Status

| AC | Description | Status |
|----|-------------|--------|
| AC-1 | `/api-version` returns JSON with build metadata | ✅ Implemented |
| AC-2 | `/api-smoke` returns 200/500 based on checks | ✅ Implemented |
| AC-3 | UI build tag shows when `?verify=1` | ✅ Implemented |
| AC-4 | `npm run smoke:prod` script works | ✅ Implemented |
| AC-5 | GitHub Actions workflow configured | ✅ Implemented |

---

## 🔍 Troubleshooting

### If endpoints return 404:
1. Check Vercel deployment status
2. Verify latest commit deployed: `097095a`
3. Clear browser cache / try incognito
4. Wait 2-3 more minutes for DNS propagation

### If smoke tests fail:
1. Check individual assertions in `/api-smoke` response
2. Verify policy dates haven't changed
3. Ensure SOC2 copy is on /security page
4. Confirm API routes exist

### If build tag doesn't show:
1. Ensure `?verify=1` is in URL
2. Check browser dev console for errors
3. Verify `BuildTag` component in layout.tsx

---

## 📊 Production URLs

**Primary Domain:**
```
https://ai-bookkeeper-nine.vercel.app
```

**Provenance Endpoints:**
- Version: `/api-version`
- Smoke: `/api-smoke`
- UI Verify: `/free/categorizer?verify=1`

**Full URLs:**
```
https://ai-bookkeeper-nine.vercel.app/api-version
https://ai-bookkeeper-nine.vercel.app/api-smoke
https://ai-bookkeeper-nine.vercel.app/free/categorizer?verify=1
```

---

## 🎉 Next Steps

Once Vercel deployment shows "Ready":

1. ✅ Run all verification steps above
2. ✅ Confirm `/api-version` JSON looks correct
3. ✅ Confirm `/api-smoke` returns all `true` assertions
4. ✅ Confirm UI build tag appears with `?verify=1`
5. ✅ Run `npm run smoke:prod` and verify exit code 0
6. ✅ Trigger GitHub Actions workflow manually to test CI

---

## 📝 Implementation Notes

### Why `api-version` and `api-smoke` (not `__version` and `__smoke`)?
Next.js treats folders starting with `_` or `__` as private and excludes them from routing. We use `api-` prefix to avoid this convention and ensure routes are publicly accessible.

### Environment Variables
All Vercel-provided env vars are automatically available:
- `VERCEL_GIT_COMMIT_SHA`
- `VERCEL_ENV`
- `VERCEL_URL`
- etc.

No additional configuration needed!

### Runtime Configuration
- Both endpoints use `runtime = 'nodejs'` for Node.js environment
- Both use `dynamic = 'force-dynamic'` to prevent caching
- BuildTag is a client component using `'use client'`

---

## ✅ Delivery Complete

**All code delivered and pushed to `main` branch.**

**Waiting for:** Vercel deployment (ETA: 2-5 minutes)

**To verify:** Run the verification steps above once deployment shows "Ready"

---

**Last Updated:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")
**Commit:** `097095a`
**Branch:** `main`
**Status:** 🟢 Code Complete, ⏳ Deployment In Progress

