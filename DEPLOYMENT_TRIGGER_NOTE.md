# Deployment Trigger Note

**Time:** November 5, 2025  
**Issue:** V2 not deploying despite all fixes  
**Root Cause:** Path filter working TOO well  

---

## What Happened

1. ✅ Added SSR marker to page.tsx (commit `b4ea7a5`)
2. ✅ Updated smoke tests (commits `3cd753d`, `b4ea7a5`)
3. ✅ Added path filters to workflows (commit `0149262`)
4. ✅ Documented fixes (commit `824f8e2`)
5. ❌ **But commit `824f8e2` only changed `CI_FIXES_SUMMARY.md`**
6. ❌ **Path filter requires `frontend/**` changes to trigger deploy**
7. ❌ **Workflow didn't run → no deployment**

---

## The Fix

**Path filter in `deploy_prod.yml`:**
```yaml
paths:
  - 'frontend/**'
  - '.github/workflows/deploy_prod.yml'
```

**Last commit only changed:**
- `CI_FIXES_SUMMARY.md` (docs, not frontend)

**Solution:**
Added empty `frontend/.deploy-trigger` file to match path filter.

---

## Lesson Learned

**Path filters are great** for preventing unnecessary runs, but you need to ensure at least one file in the filtered paths changes to trigger the workflow.

**Best practice for trigger commits:**
```bash
# Option 1: Touch a frontend file
touch frontend/.deploy-trigger
git add frontend/.deploy-trigger
git commit -m "chore: trigger deployment"

# Option 2: Use workflow_dispatch
# Manually trigger via GitHub UI or gh CLI

# Option 3: Include workflow file in commit
git add .github/workflows/deploy_prod.yml
# Any change triggers because workflow file is in path filter
```

---

## Current Status

**Commit:** `f7e6797` (trigger commit)  
**Queued Changes:** 27 commits (15b4e81 → f7e6797)  
**Includes:**
- V2 activation (page.tsx swap)
- SSR marker (data-app, data-version)
- Updated smoke tests
- Path filters for all workflows
- All bug fixes

**Expected:** Production will deploy in 2-3 minutes

---

## Monitoring

**GitHub Actions:**
https://github.com/ContrejfC/ai-bookkeeper/actions

**Verify when live:**
```bash
HOST=https://ai-bookkeeper.app

# Should show f7e6797 (or newer)
curl -s $HOST/api-version | jq -r '.git.commitSha'

# Should show v2 marker
curl -s $HOST/free/categorizer | grep 'data-version="v2"'
```

---

**Status:** Workflow triggered, awaiting deployment. ⏳

