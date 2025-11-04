# 🚀 Step-by-Step Deployment Guide

## Prerequisites Checklist

Before you start, make sure you have:
- [x] GitHub account with access to `ContrejfC/ai-bookkeeper`
- [x] Vercel account (same one used for the project)
- [x] Terminal/command line access
- [x] Node.js installed (for local verification)

---

## STEP 1: Get Your Vercel Token

### 1.1. Open Vercel Dashboard
1. Go to: https://vercel.com/login
2. Log in to your Vercel account

### 1.2. Navigate to Tokens Page
1. Click on your profile icon (top right)
2. Click **"Settings"**
3. In the left sidebar, click **"Tokens"**
4. Or go directly to: https://vercel.com/account/tokens

### 1.3. Create a New Token
1. Click **"Create Token"** button
2. Give it a name: `GitHub Actions Deployment`
3. Set expiration: **"No Expiration"** (or choose a date)
4. Click **"Create Token"**
5. **⚠️ IMPORTANT:** Copy the token immediately (you won't see it again!)
6. Store it somewhere safe (you'll need it in Step 3)

**✅ Token format:** `vercel_xxxxx...` (starts with `vercel_`)

---

## STEP 2: Get Your Vercel Org ID and Project ID

### 2.1. Open Terminal
```bash
# Navigate to your project
cd /Users/fabiancontreras/ai-bookkeeper/frontend
```

### 2.2. Link Vercel Project
```bash
# Install Vercel CLI if you haven't already
npm install -g vercel@latest

# Link the project (if not already linked)
vercel link
```

**What happens:**
- If you're not logged in, it will ask you to login: press Enter, open the browser, log in
- It will ask: **"Set up and deploy? [y/N]"** → Type `N` and press Enter
- It will ask: **"Which scope?"** → Select your organization/account
- It will ask: **"Link to existing project? [y/N]"** → Type `Y` and press Enter
- It will list projects → Select **"ai-bookkeeper"** (or your project name)
- It will ask about directories → Accept defaults

### 2.3. Get the IDs
```bash
# Read the project configuration
cat .vercel/project.json
```

**You'll see something like:**
```json
{
  "orgId": "team_abc123xyz",
  "projectId": "prj_abc123xyz"
}
```

**✅ Copy these two values:**
- `orgId`: This is your **VERCEL_ORG_ID**
- `projectId`: This is your **VERCEL_PROJECT_ID**

---

## STEP 3: Add GitHub Secrets

### 3.1. Navigate to GitHub Secrets Page
1. Go to: https://github.com/ContrejfC/ai-bookkeeper
2. Click **"Settings"** tab (at the top of the repo)
3. In the left sidebar, click **"Secrets and variables"**
4. Click **"Actions"**

**Or go directly to:**
https://github.com/ContrejfC/ai-bookkeeper/settings/secrets/actions

### 3.2. Add VERCEL_TOKEN Secret
1. Click **"New repository secret"** button (top right)
2. **Name:** Type `VERCEL_TOKEN`
3. **Secret:** Paste your Vercel token (from Step 1.3)
4. Click **"Add secret"**

### 3.3. Add VERCEL_ORG_ID Secret
1. Click **"New repository secret"** button again
2. **Name:** Type `VERCEL_ORG_ID`
3. **Secret:** Paste your orgId (from Step 2.3)
4. Click **"Add secret"**

### 3.4. Add VERCEL_PROJECT_ID Secret
1. Click **"New repository secret"** button again
2. **Name:** Type `VERCEL_PROJECT_ID`
3. **Secret:** Paste your projectId (from Step 2.3)
4. Click **"Add secret"**

**✅ You should now see 3 secrets:**
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

---

## STEP 4: Verify Workflow File Exists

### 4.1. Check Workflow File
```bash
# From project root
cd /Users/fabiancontreras/ai-bookkeeper

# Verify the workflow exists
ls -la .github/workflows/deploy_prod.yml

# View the workflow (optional)
cat .github/workflows/deploy_prod.yml | head -20
```

**✅ You should see:** `.github/workflows/deploy_prod.yml` exists

---

## STEP 5: Trigger the Deployment Workflow

### Option A: Automatic Trigger (Push to Main)

The workflow runs automatically when you push to `main`. Since we already pushed, let's manually trigger it:

### Option B: Manual Trigger (Recommended First Time)

#### 5.1. Navigate to GitHub Actions
1. Go to: https://github.com/ContrejfC/ai-bookkeeper
2. Click **"Actions"** tab (at the top)

#### 5.2. Find the Workflow
1. In the left sidebar, look for **"Deploy Prod (Monorepo)"**
2. Click on it

#### 5.3. Run the Workflow
1. Click **"Run workflow"** button (top right)
2. Branch: Make sure `main` is selected
3. Click the green **"Run workflow"** button

#### 5.4. Monitor the Run
1. You'll see a new workflow run appear
2. Click on it to see the progress
3. Watch each step as it executes

**Expected steps (in order):**
1. ✅ Checkout repository
2. ✅ Setup Node.js
3. ✅ Install Vercel CLI
4. ✅ Pull Vercel environment information
5. ✅ Build project artifacts
6. ✅ Deploy prebuilt to production
7. ✅ Force alias to production domain
8. ✅ Wait for deployment propagation
9. ✅ Smoke: Policy dates (privacy)
10. ✅ Smoke: Policy dates (terms)
11. ✅ Smoke: SOC2 compliance copy
12. ✅ Smoke: API route method guard
13. ✅ Smoke: UI controls present
14. ✅ Smoke: /api-version endpoint
15. ✅ Smoke: /api-smoke assertions

**⏰ This takes about 3-5 minutes**

---

## STEP 6: Check Workflow Status

### 6.1. Successful Deployment
**If all steps are green ✅:**

1. Scroll down to see the deployment summary
2. You'll see:
   - Deployment URL (something like `ai-bookkeeper-xyz123.vercel.app`)
   - Production alias: `ai-bookkeeper-nine.vercel.app`
   - Smoke test results (all assertions should be `true`)

**✅ Success! Your deployment is live.**

### 6.2. Failed Deployment

**If any step is red ❌:**

1. Click on the failed step
2. Read the error message

**Common errors:**

**Error: "VERCEL_TOKEN not found"**
- **Fix:** Go back to Step 3, make sure you added all 3 secrets correctly

**Error: "vercel pull" failed**
- **Fix:** Check that VERCEL_ORG_ID and VERCEL_PROJECT_ID are correct
- Run `vercel link` again in `frontend/` directory to verify

**Error: "Smoke test failed"**
- **Fix:** Check which specific assertion failed
- Visit the failed page manually to see what's wrong
- May need to fix content or configuration

**Error: "404" on endpoints**
- **Fix:** Routes may not be deployed. Check build logs for errors.

---

## STEP 7: Verify Production Deployment

### 7.1. Test Version Endpoint
```bash
# In terminal
curl -s https://ai-bookkeeper-nine.vercel.app/api-version | jq .
```

**Expected output:**
```json
{
  "name": "ai-bookkeeper",
  "host": "ai-bookkeeper-nine.vercel.app",
  "protocol": "https",
  "vercel": {
    "env": "production",
    "url": "ai-bookkeeper-nine.vercel.app"
  },
  "git": {
    "commitSha": "0cb826f...",
    "commitRef": "main"
  },
  "build": {
    "timeIso": "2025-11-04T...",
    "soc2Status": "aligned",
    "freeMaxRows": 500
  }
}
```

**✅ If you see JSON with commit SHA → Success!**

### 7.2. Test Smoke Endpoint
```bash
curl -s https://ai-bookkeeper-nine.vercel.app/api-smoke | jq .
```

**Expected output:**
```json
{
  "base": "https://ai-bookkeeper-nine.vercel.app",
  "timestamp": "2025-11-04T...",
  "assertions": {
    "privacyDate": true,
    "termsDate": true,
    "soc2Copy": true,
    "apiUpload405": true,
    "uiControls": true
  }
}
```

**✅ If all assertions are `true` → Success!**

### 7.3. Test UI Build Tag
1. Open browser
2. Go to: https://ai-bookkeeper-nine.vercel.app/free/categorizer?verify=1
3. Look at the **bottom-right corner**

**✅ You should see:** A small white box with text like:
```
sha: 0cb826f • env: production
```

### 7.4. Run Local Smoke Tests
```bash
# From project root
cd /Users/fabiancontreras/ai-bookkeeper

# Run smoke tests
npm run smoke:prod
```

**Expected output:**
```
🧪 Running smoke tests against: https://ai-bookkeeper-nine.vercel.app

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
```

**Exit code should be:** `0` (success)

---

## STEP 8: Verify Automatic Deployments Work

### 8.1. Make a Test Change
```bash
# Make a small change to verify auto-deploy
cd /Users/fabiancontreras/ai-bookkeeper

# Create a test file
echo "# Test" >> TEST.md

# Commit and push
git add TEST.md
git commit -m "test: Verify automatic deployment"
git push origin main
```

### 8.2. Check GitHub Actions
1. Go to: https://github.com/ContrejfC/ai-bookkeeper/actions
2. You should see a new workflow run starting automatically
3. Wait 3-5 minutes
4. Verify it completes successfully

**✅ If workflow runs automatically → Success!**

### 8.3. Clean Up Test File
```bash
git rm TEST.md
git commit -m "chore: Remove test file"
git push origin main
```

---

## STEP 9: Understanding the Workflow

### What Happens on Each Deployment

1. **Checkout:** Gets the latest code from `main` branch
2. **Setup:** Installs Node.js 20
3. **Install CLI:** Installs latest Vercel CLI
4. **Pull Config:** Downloads Vercel production environment variables
5. **Build:** Builds the Next.js app from `/frontend` directory
6. **Deploy:** Deploys the built artifacts to Vercel
7. **Alias:** Forces the alias to `ai-bookkeeper-nine.vercel.app`
8. **Wait:** Waits 10 seconds for DNS propagation
9. **Test:** Runs 7 smoke tests to verify everything works
10. **Summary:** Posts results to GitHub Actions summary

### When Does It Run?

- **Automatic:** Every push to `main` branch
- **Manual:** You can trigger it manually from GitHub Actions

### What If Tests Fail?

- **Workflow fails** → Deployment marked as failed
- **Previous deployment stays live** (no broken deploy)
- **You get notified** via GitHub Actions
- **Fix the issue** → Push again → New deployment

---

## STEP 10: Troubleshooting Common Issues

### Issue: "jq: command not found" in smoke tests
**Fix:**
- The workflow automatically installs `jq` if missing
- If it still fails, check the workflow logs

### Issue: Endpoints return 404
**Possible causes:**
1. Routes not deployed yet (wait 2-3 more minutes)
2. Vercel caching (try with `?t=$(date +%s)` query param)
3. Wrong domain alias (check workflow logs for alias step)

**Fix:**
```bash
# Try with cache-busting
curl "https://ai-bookkeeper-nine.vercel.app/api-version?t=$(date +%s)"

# Check Vercel dashboard
# Visit: https://vercel.com/contrejfcs-projects/ai-bookkeeper
```

### Issue: Smoke test fails on policy dates
**Possible cause:** Content changed or typo

**Fix:**
1. Visit https://ai-bookkeeper-nine.vercel.app/privacy
2. Check if "November 3, 2025" is present
3. Update content or workflow regex if needed

### Issue: Can't get Vercel token
**Fix:**
- Make sure you're logged into the correct Vercel account
- Check that you have access to the project
- Try creating token in incognito mode

### Issue: `vercel link` fails
**Fix:**
```bash
# Make sure you're in the frontend directory
cd /Users/fabiancontreras/ai-bookkeeper/frontend

# Logout and login again
vercel logout
vercel login

# Try linking again
vercel link
```

---

## ✅ Success Checklist

After completing all steps, you should have:

- [ ] ✅ Vercel token created and stored
- [ ] ✅ VERCEL_ORG_ID and VERCEL_PROJECT_ID copied
- [ ] ✅ All 3 GitHub secrets added
- [ ] ✅ Workflow ran successfully (all green checks)
- [ ] ✅ `/api-version` returns JSON with commit SHA
- [ ] ✅ `/api-smoke` returns all assertions `true`
- [ ] ✅ UI build tag appears on `?verify=1`
- [ ] ✅ `npm run smoke:prod` passes locally
- [ ] ✅ Automatic deployments working on push to `main`

---

## 📞 Quick Reference

**GitHub Secrets:** https://github.com/ContrejfC/ai-bookkeeper/settings/secrets/actions  
**GitHub Actions:** https://github.com/ContrejfC/ai-bookkeeper/actions  
**Vercel Tokens:** https://vercel.com/account/tokens  
**Production URL:** https://ai-bookkeeper-nine.vercel.app  
**Workflow File:** `.github/workflows/deploy_prod.yml`

---

## 🎉 You're Done!

Once all steps are complete, you have:
- ✅ Automated deployments on every push to `main`
- ✅ Manual deployment trigger option
- ✅ Comprehensive smoke tests
- ✅ Provenance verification
- ✅ Production-safe API routes

**Every time you push to `main`, your code automatically:**
1. Gets deployed to production
2. Gets smoke tested
3. Gets verified to work correctly

**If anything breaks, the workflow fails and you're notified immediately!**

---

**Need Help?** Check the detailed documentation:
- `MONOREPO_DEPLOY.md` - Full technical documentation
- `DEPLOYMENT_FINAL.md` - Deployment summary
- GitHub Actions logs - Detailed execution logs
