# 🎯 Action Items for Paid Launch

**Target:** Paid posting to QuickBooks via ChatGPT GPT (Stripe LIVE + QBO Prod)  
**Priority:** Ranked by launch blocking impact  
**Status:** 9/10 items ready, 1 critical blocker (resolved)

## 🚨 CRITICAL (Launch Blockers)

### 1. Deploy to Render ✅ RESOLVED
- **What:** Create API + Web services using render-split.yaml
- **Where:** Render Dashboard → New Blueprint
- **Why:** Need live services for GPT Actions integration
- **Command:** Apply render-split.yaml blueprint in Render
- **Acceptance:** Both services show "Live" status, health checks pass
- **Note:** Fresh database will resolve Alembic issue automatically

## 🔥 HIGH PRIORITY (Pre-Launch)

### 2. Configure Stripe LIVE Keys
- **What:** Switch from TEST to LIVE mode in Stripe
- **Where:** Render Dashboard → Environment Variables
- **Why:** Enable real payments for paid posting
- **Command:** Update STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY to LIVE keys
- **Acceptance:** `scripts/verify_stripe_webhook.py` confirms LIVE webhook

### 3. Configure QBO Production Credentials
- **What:** Switch from Sandbox to Production QBO
- **Where:** Render Dashboard → Environment Variables
- **Why:** Enable posting to real QuickBooks companies
- **Command:** Update QBO_CLIENT_ID, QBO_CLIENT_SECRET to Production keys
- **Acceptance:** `scripts/check_qbo_env.py` confirms Production mode

### 4. Run Production Smoke Tests
- **What:** Verify all endpoints work in production
- **Where:** Live Render services
- **Why:** Ensure GPT Actions integration works
- **Command:** `ops/smoke_live.sh --spec-version v1.0`
- **Acceptance:** All 6 smoke test steps pass

## 📋 MEDIUM PRIORITY (Launch Day)

### 5. Create Production API Key
- **What:** Generate API key for ChatGPT GPT
- **Where:** Local development environment
- **Why:** GPT Actions requires API key authentication
- **Command:** `scripts/create_api_key.py --tenant TENANT_ID --name "GPT Actions"`
- **Acceptance:** API key created, stored securely

### 6. Configure GPT Actions in ChatGPT
- **What:** Set up ChatGPT custom GPT with Actions
- **Where:** ChatGPT GPT Builder
- **Why:** Enable paid posting workflow
- **Command:** Import OpenAPI, add API key, configure instructions
- **Acceptance:** GPT can call /actions, /billing/status, /post/commit

### 7. Test End-to-End Workflow
- **What:** Complete paid posting flow in ChatGPT GPT
- **Where:** ChatGPT GPT interface
- **Why:** Verify complete user journey works
- **Command:** Connect QBO → Propose entries → Approve → Post to QBO
- **Acceptance:** Journal entry appears in QuickBooks

## 🔧 NICE TO HAVE (Post-Launch)

### 8. Add Web Health Check Route
- **What:** Add simple /healthz route to Next.js app
- **Where:** `frontend/app/healthz/route.ts`
- **Why:** Improve health check reliability
- **Command:** Create simple 200 response route
- **Acceptance:** `curl localhost:3000/healthz` returns 200

### 9. Add Makefile for Local Testing
- **What:** Create `make smoke-local` target
- **Where:** `Makefile`
- **Why:** Simplify local testing workflow
- **Command:** Add target that runs docker build/run tests
- **Acceptance:** `make smoke-local` runs container tests

### 10. Clear Local Databases (Optional)
- **What:** Remove local database files to fix Alembic issue
- **Where:** Local development environment
- **Why:** Clean up local development state
- **Command:** `rm *.db && alembic upgrade head`
- **Acceptance:** `alembic heads` returns single head without errors

## 📊 Progress Tracking

| Item | Status | Priority | Estimated Time |
|------|--------|----------|----------------|
| Deploy to Render | 🟢 READY | Critical | 30 minutes |
| Stripe LIVE | 🟡 READY | High | 15 minutes |
| QBO Production | 🟡 READY | High | 15 minutes |
| Smoke Tests | 🟡 READY | High | 10 minutes |
| API Key | 🟢 READY | Medium | 5 minutes |
| GPT Setup | 🟢 READY | Medium | 20 minutes |
| E2E Test | 🟢 READY | Medium | 15 minutes |
| Web Health | 🟢 READY | Nice | 10 minutes |
| Makefile | 🟢 READY | Nice | 5 minutes |
| Clear Local DBs | 🟢 READY | Nice | 2 minutes |

## 🎯 Launch Timeline

**Phase 1 (Critical - 30 minutes):**
1. Deploy to Render (30 min)

**Phase 2 (Pre-Launch - 40 minutes):**
2. Configure Stripe LIVE (15 min)
3. Configure QBO Production (15 min)
4. Run smoke tests (10 min)

**Phase 3 (Launch Day - 40 minutes):**
5. Create API key (5 min)
6. Configure GPT Actions (20 min)
7. Test E2E workflow (15 min)

**Total Time to Launch:** ~2 hours

## 🚀 Success Criteria

- [ ] Services deployed and healthy on Render
- [ ] Stripe LIVE mode configured
- [ ] QBO Production mode configured
- [ ] All smoke tests pass
- [ ] GPT Actions working in ChatGPT
- [ ] End-to-end paid posting workflow functional

## 📞 Rollback Plan

If critical issues arise:
1. **Service Issues:** Rollback to previous Render deployment
2. **Stripe Issues:** Switch back to TEST mode
3. **QBO Issues:** Switch back to Sandbox mode
4. **GPT Issues:** Disable Actions, use manual workflow

## 🔧 Alembic Issue Resolution

**Issue:** `KeyError: '001'` in local environment  
**Root Cause:** Existing database files have old revision stamped  
**Solution:** Fresh database in Render will work automatically  
**Local Fix:** `rm *.db && alembic upgrade head` (optional)