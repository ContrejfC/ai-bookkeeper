# ⚡ FIX & LAUNCH - Ultra-Quick Guide

**Current Status:** API service failing (no database)  
**Fix Time:** 5 minutes  
**Launch Time:** 2 hours after fix

---

## 🚨 FIX NOW (5 minutes)

### 1. Get Free Database (2 min)
```
1. Go to: https://neon.tech
2. Sign up → Create project
3. Copy connection string (starts with postgresql://)
4. Ensure it ends with: ?sslmode=require
```

### 2. Add to Render (2 min)
```
1. Render Dashboard → ai-bookkeeper-api → Environment
2. Add Environment Variable:
   Key: DATABASE_URL
   Value: postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require
3. Add Environment Variable:
   Key: PGSSLMODE
   Value: require
4. Click "Save Changes"
```

### 3. Wait & Verify (1 min)
```bash
# After ~3 min, test from your laptop:
curl https://YOUR-API.onrender.com/healthz

# Should return:
{"status":"healthy","database":"connected"}
```

---

## 🚀 LAUNCH AFTER FIX (2 hours)

### Phase 1: Deploy Web Service (10 min)
```
1. Render → New → Web Service
2. Name: ai-bookkeeper-web
3. Dockerfile: ./Dockerfile.web
4. Add variables (mark "Available during build"):
   NEXT_PUBLIC_API_URL = https://YOUR-API.onrender.com
   NEXT_PUBLIC_BASE_URL = https://ai-bookkeeper-web.onrender.com
5. Create
```

### Phase 2: Configure Stripe LIVE (30 min)
```
Follow: docs/GO_LIVE_NOW.md → Phase 2
- Run stripe_bootstrap.py locally
- Create webhook in Stripe
- Add env vars to Render API service
```

### Phase 3: Configure QBO Production (30 min)
```
Follow: docs/GO_LIVE_NOW.md → Phase 3
- Get production credentials from Intuit
- Add env vars to Render API service
```

### Phase 4: Generate API Key & Smoke Test (10 min)
```
SSH into Render API service:
./ops/launch_live.sh

Saves API key to: ops/.last_api_key.txt
```

### Phase 5: Publish GPT (40 min)
```
Follow: gpt_config/public_publish_checklist.md
- Import OpenAPI
- Add API key auth
- Toggle Public
- Test
```

---

## 📋 YOUR ACTION ITEMS RIGHT NOW

**Immediate (Fix Database):**
- [ ] Go to neon.tech
- [ ] Create project and copy PostgreSQL URL
- [ ] Add DATABASE_URL to Render API service
- [ ] Wait 3 min for redeploy
- [ ] Curl health check to verify

**After Fix (Deploy Web):**
- [ ] Create Web Service in Render
- [ ] Set NEXT_PUBLIC_* variables (mark "Available during build")
- [ ] Verify both services show "Live"

**Then (Full Launch):**
- [ ] Follow `docs/GO_LIVE_NOW.md` for complete launch
- [ ] Or just focus on getting services running first

---

## ✅ SUCCESS = GREEN HEALTH CHECKS

```bash
# API Health
curl https://YOUR-API.onrender.com/healthz
# Returns: {"status":"healthy","database":"connected"}

# Web Health (after web service deployed)
curl https://YOUR-WEB.onrender.com/healthz  
# Returns: {"status":"ok"}
```

**Once both return 200 OK, you're ready for the full launch!**

---

## 📂 All Your Guides

**Immediate Fix:**
- `RENDER_FIX_SIMPLE.md` (this guide, detailed)
- `RENDER_FIX_NOW.md` (original fix guide)

**After Fix:**
- `docs/GO_LIVE_NOW.md` (complete launch runbook)
- `docs/RENDER_SETTINGS.md` (all configuration)
- `gpt_config/public_publish_checklist.md` (GPT publishing)

**Launch Tools:**
- `ops/launch_live.sh` (one-command verification)
- `ops/smoke_live.sh` (smoke tests)

---

**Bottom Line:**
1. **NOW:** Get PostgreSQL URL from Neon → Add to Render → Verify health check
2. **THEN:** Follow the launch guides to go live

**First priority: Fix the database connection. Everything else waits on that.** ✅
