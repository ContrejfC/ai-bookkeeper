# Monorepo-Aware Production Deploy + Provenance Verification

## ✅ IMPLEMENTATION COMPLETE

A complete monorepo-aware deployment system using Vercel CLI with integrated provenance verification.

---

## 🚀 What Was Implemented

### 1. Monorepo-Aware Vercel CLI Workflow
**File:** `.github/workflows/deploy_prod.yml`

**Key Features:**
- ✅ Deploys from `/frontend` subdirectory (monorepo support)
- ✅ Uses Vercel CLI for controlled production deploys
- ✅ Forces alias to `ai-bookkeeper-nine.vercel.app`
- ✅ Runs comprehensive smoke tests after deployment
- ✅ Fails workflow if ANY assertion fails

**Triggers:**
- Push to `main` branch (automatic)
- Manual via `workflow_dispatch`

**Workflow Steps:**
1. Pull Vercel production environment
2. Build from `/frontend` directory
3. Deploy prebuilt artifacts to production
4. Force alias to production domain
5. Wait for propagation (10s)
6. Run all smoke tests
7. Post deployment summary

### 2. Production-Safe API Routes
**Verified All Routes Have:**
- ✅ `export const runtime = 'nodejs'`
- ✅ `export const dynamic = 'force-dynamic'`
- ✅ Method guards (405 for unsupported methods)

**Routes Verified:**
- `/api/free/categorizer/upload/route.ts` - POST only
- `/api/free/categorizer/lead/route.ts` - POST only
- `/api/free/categorizer/uploads/[id]/route.ts` - DELETE only
- `/api-version/route.ts` - GET only
- `/api-smoke/route.ts` - GET only

### 3. Provenance Endpoints
**Both endpoints exist and are production-ready:**

#### `/api-version`
Returns build metadata:
```json
{
  "name": "ai-bookkeeper",
  "host": "ai-bookkeeper-nine.vercel.app",
  "vercel": { "env": "production" },
  "git": {
    "commitSha": "...",
    "commitRef": "main",
    "commitMessage": "..."
  },
  "build": { "timeIso": "...", "soc2Status": "aligned" }
}
```

#### `/api-smoke`
Server-side runtime validation:
```json
{
  "assertions": {
    "privacyDate": true,
    "termsDate": true,
    "soc2Copy": true,
    "apiUpload405": true,
    "uiControls": true
  }
}
```

### 4. Smoke Test Coverage
**All smoke tests check:**
- ✅ Policy dates (November 3, 2025) in `/privacy` and `/terms`
- ✅ SOC2 compliance copy in `/security`
- ✅ API method guards (405 on GET for POST-only routes)
- ✅ UI controls on `/free/categorizer`
- ✅ `/api-version` returns valid JSON
- ✅ `/api-smoke` assertions all pass

---

## 📋 Prerequisites (GitHub Secrets)

Before running the workflow, add these secrets to your GitHub repository:

### Required Secrets
```
VERCEL_TOKEN        - Vercel API token
VERCEL_ORG_ID       - Your Vercel organization ID
VERCEL_PROJECT_ID   - Your Vercel project ID
```

### How to Get These Values

#### 1. VERCEL_TOKEN
```bash
# Install Vercel CLI if needed
npm i -g vercel@latest

# Login and get token
vercel login
vercel whoami

# Create token at: https://vercel.com/account/tokens
```

#### 2. VERCEL_ORG_ID and VERCEL_PROJECT_ID
```bash
# Run from the frontend directory
cd frontend
vercel link

# Then check .vercel/project.json
cat .vercel/project.json
```

**Or find in Vercel Dashboard:**
- Go to: https://vercel.com/contrejfcs-projects/ai-bookkeeper/settings
- Project Settings → General
- Copy "Project ID" and "Org ID"

### Adding Secrets to GitHub
1. Go to: https://github.com/ContrejfC/ai-bookkeeper/settings/secrets/actions
2. Click "New repository secret"
3. Add each secret:
   - Name: `VERCEL_TOKEN`
   - Value: `<your-token>`
4. Repeat for `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID`

---

## 🎯 How to Deploy

### Option A: Automatic (Push to Main)
```bash
git add .
git commit -m "feat: your changes"
git push origin main
```

**Workflow triggers automatically** and deploys to production.

### Option B: Manual Trigger
1. Go to: https://github.com/ContrejfC/ai-bookkeeper/actions
2. Click "Deploy Prod (Monorepo)"
3. Click "Run workflow"
4. Select branch: `main`
5. Click "Run workflow"

---

## 🧪 Verification After Deployment

### Check Workflow Status
Visit: https://github.com/ContrejfC/ai-bookkeeper/actions

**Expected:** All steps green ✅

**If red ❌:** Click into the failed step to see error details

### Test Endpoints Manually

```bash
# 1. Test version endpoint
curl -s https://ai-bookkeeper-nine.vercel.app/api-version | jq .

# Expected: JSON with commitSha, env, host

# 2. Test smoke endpoint
curl -s https://ai-bookkeeper-nine.vercel.app/api-smoke | jq .

# Expected: All assertions true

# 3. Test UI build tag
open "https://ai-bookkeeper-nine.vercel.app/free/categorizer?verify=1"

# Expected: Bottom-right ribbon with commit SHA

# 4. Run local smoke tests
cd /Users/fabiancontreras/ai-bookkeeper
npm run smoke:prod

# Expected: Exit code 0, all tests pass
```

---

## 🔍 Smoke Test Details

### What Gets Checked

| Check | Endpoint | Expected |
|-------|----------|----------|
| Privacy Date | `/privacy` | Contains "November 3, 2025" |
| Terms Date | `/terms` | Contains "November 3, 2025" |
| SOC2 Copy | `/security` | Contains "aligned controls" or "Type II" |
| API Guard | `GET /api/free/categorizer/upload` | Returns 405, Allow: POST |
| UI Controls | `/free/categorizer` | Contains expected UI text |
| Version | `/api-version` | Returns valid JSON |
| Assertions | `/api-smoke` | All assertions = true |

### Failure Handling

**If ANY check fails, the entire workflow fails.**

This ensures:
- No broken deployments marked as "success"
- Immediate notification of issues
- Rollback capability (deploy previous commit)

---

## 📊 Workflow Output

### GitHub Actions Summary
After each deployment, the workflow posts:
- Deployment URL
- Production alias
- Full `/api-smoke` JSON results

**View at:** Actions → Deploy Prod (Monorepo) → Summary tab

### Example Success Output
```
🧪 Checking /privacy for November 3, 2025...
✅ Pass

🧪 Checking /terms for November 3, 2025...
✅ Pass

🧪 Checking /security for SOC2 copy...
✅ Pass

🧪 Checking /api/free/categorizer/upload for 405 on GET...
Status:  405 
Allow: allow: POST
✅ Pass

🧪 Checking /free/categorizer for UI controls...
✅ Pass

🧪 Checking /api-version...
{
  "name": "ai-bookkeeper",
  "host": "ai-bookkeeper-nine.vercel.app",
  ...
}
✅ /api-version returned valid JSON

🧪 Checking /api-smoke assertions...
{
  "assertions": {
    "privacyDate": true,
    "termsDate": true,
    "soc2Copy": true,
    "apiUpload405": true,
    "uiControls": true
  }
}
✅ All smoke test assertions passed
```

---

## 🛠️ Troubleshooting

### Workflow Fails: "VERCEL_TOKEN not found"
**Problem:** GitHub secrets not configured

**Fix:**
1. Add secrets as described in Prerequisites section
2. Re-run workflow

### Workflow Fails: "vercel pull" error
**Problem:** Invalid org/project IDs

**Fix:**
1. Run `cd frontend && vercel link` locally
2. Copy correct IDs from `.vercel/project.json`
3. Update GitHub secrets
4. Re-run workflow

### Smoke Test Fails: Policy dates
**Problem:** Date in `/privacy` or `/terms` doesn't match

**Fix:**
1. Check actual date in files
2. Update workflow regex if date changed intentionally
3. Or update files to use "November 3, 2025"

### Smoke Test Fails: API endpoint 404
**Problem:** Route doesn't exist or isn't deployed

**Fix:**
1. Verify route files exist in `/frontend/app/api/`
2. Check build logs for errors
3. Verify `runtime = 'nodejs'` is set
4. Re-deploy

### Deployment URL different from alias
**Problem:** Alias command failed

**Fix:**
1. Check Vercel dashboard for domain settings
2. Verify domain is configured in project
3. Check workflow logs for alias command output
4. May need to manually set alias in Vercel dashboard

---

## 📁 Files Modified/Created

### New Files (2)
1. `.github/workflows/deploy_prod.yml` - Main deployment workflow
2. `MONOREPO_DEPLOY.md` - This documentation

### Existing Files (Verified)
- `frontend/app/api-version/route.ts` ✅
- `frontend/app/api-smoke/route.ts` ✅
- `frontend/app/api/free/categorizer/upload/route.ts` ✅
- `frontend/app/api/free/categorizer/lead/route.ts` ✅
- `frontend/app/api/free/categorizer/uploads/[id]/route.ts` ✅
- `scripts/smoke.js` ✅
- `frontend/package.json` ✅ (has `smoke:prod` script)

---

## 🎉 Success Criteria

**Deployment is successful when:**

✅ GitHub Actions workflow completes (all steps green)  
✅ Production alias set to `ai-bookkeeper-nine.vercel.app`  
✅ All 7 smoke tests pass  
✅ `/api-version` returns JSON with current commit SHA  
✅ `/api-smoke` returns all assertions = true  
✅ UI build tag shows on `?verify=1`  

---

## 🔄 Continuous Deployment

**Current Setup:**
- ✅ Every push to `main` triggers automatic deployment
- ✅ All smoke tests run automatically
- ✅ Deployment fails if ANY test fails
- ✅ Manual trigger available for re-deploys

**Recommendation:**
- Keep automatic deployments enabled
- Monitor GitHub Actions for failures
- Set up Slack/email notifications for failed workflows

---

## 📞 Next Steps

1. **Add GitHub Secrets** (if not already done)
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`

2. **Trigger First Deployment**
   - Option A: Push this commit to `main`
   - Option B: Manually trigger workflow

3. **Verify Production**
   - Check all smoke tests pass
   - Visit production URL
   - Test `/api-version` and `/api-smoke`

4. **Set Up Monitoring** (optional)
   - GitHub Actions notifications
   - Vercel deployment webhooks
   - Slack integration

---

**Status:** 🟢 Ready to Deploy

**Production URL:** https://ai-bookkeeper-nine.vercel.app

**Workflow:** `.github/workflows/deploy_prod.yml`

**Last Updated:** 2025-11-04

