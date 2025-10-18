# ⚡ RENDER FIX - Simple 3-Step Solution

**Issue:** Database connection refused  
**Fix Time:** 5 minutes  
**No Render shell needed**

---

## 🎯 3 STEPS TO FIX

### Step 1: Get Free PostgreSQL URL (2 min)

**Option A: Neon (Recommended)**
1. Go to [neon.tech](https://neon.tech)
2. Sign up (free tier)
3. Create new project
4. Copy **psycopg2 connection string**
5. Ensure it ends with `?sslmode=require`

**Option B: Supabase**
1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Go to Settings → Database → Connection String
4. Copy **URI** format
5. Add `?sslmode=require` to the end if missing

**Option C: ElephantSQL**
1. Go to [elephantsql.com](https://elephantsql.com)
2. Create free "Tiny Turtle" instance
3. Copy URL
4. Add `?sslmode=require` to the end

**Final format:**
```
postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require
```

---

### Step 2: Add to Render Environment (2 min)

1. **Render Dashboard** → **ai-bookkeeper-api** → **Environment** tab
2. Click **Add Environment Variable**
3. Add these two variables:

```
DATABASE_URL = postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require
PGSSLMODE = require
```

4. Click **Save Changes**
5. Render will automatically redeploy (takes ~3-5 minutes)

---

### Step 3: Verify It Works (1 min)

**From your laptop, no shell needed:**

```bash
# Check health (should return JSON)
curl -sfS https://YOUR-API-SERVICE.onrender.com/healthz

# Check OpenAPI (should return JSON spec)
curl -s https://YOUR-API-SERVICE.onrender.com/openapi.json | head -n 5
```

**Expected responses:**
```json
// Health check:
{"status":"healthy","database":"connected"}

// OpenAPI:
{"openapi":"3.1.0","info":{"title":"AI Bookkeeper",...}}
```

---

## ✅ SUCCESS INDICATORS

**In Render Logs, you should see:**
```
✓ Single Alembic head confirmed
Running: alembic upgrade head
INFO  [alembic.runtime.migration] Running upgrade  -> 001
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002_tenant_settings
...
✅ Database migrations completed
INFO: Uvicorn running on http://0.0.0.0:10000
```

**NO MORE:**
```
❌ connection to server at "localhost" refused
```

---

## 🛡️ Optional: Add Safety Guard

If you want extra safety during first boot, add this variable:

```
ALREADY_DEPLOYED = true
```

This tells the migration script to be more lenient. Not strictly needed once DATABASE_URL is correct.

---

## 🚀 AFTER FIX WORKS

Once your API service is running:

### Next: Deploy Web Service

1. **Render Dashboard** → **New** → **Web Service**
2. **Repository:** `ContrejfC/ai-bookkeeper`
3. **Name:** `ai-bookkeeper-web`
4. **Runtime:** Docker
5. **Dockerfile Path:** `./Dockerfile.web`
6. **Environment Variables:**
   ```
   NEXT_PUBLIC_API_URL = https://YOUR-API-SERVICE.onrender.com
   NEXT_PUBLIC_BASE_URL = https://ai-bookkeeper-web.onrender.com
   ```
   **⚠️ CRITICAL:** Mark both as **"Available during build"**
   - Hover over each variable → three dots (⋮) → "Available during build"

7. Click **Create Web Service**

### Then: Continue with Launch Guide

Once both services are running:
- Follow: `docs/GO_LIVE_NOW.md`
- Configure Stripe LIVE
- Configure QBO Production
- Run launch script
- Publish GPT

---

## 📊 Why This Works

**Problem:** 
- Render services don't include PostgreSQL by default
- App was trying to connect to `localhost:5432` (doesn't exist)

**Solution:**
- External PostgreSQL database (Neon/Supabase/ElephantSQL)
- Connection string in `DATABASE_URL` environment variable
- App connects to external database instead of localhost

**Benefits:**
- ✅ Free tier available on all providers
- ✅ Better than Render's PostgreSQL (faster, more features)
- ✅ Easy to set up and manage
- ✅ SSL connection for security

---

## 🆘 Troubleshooting

### Issue: Health check still fails

**Check:**
1. DATABASE_URL format is correct (starts with `postgresql://`)
2. Ends with `?sslmode=require`
3. No extra spaces or line breaks in the URL
4. Database is actually created and accessible

**Test connection from your laptop:**
```bash
# Install psql if needed: brew install postgresql
psql "postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require"

# If this works, the URL is correct
```

### Issue: Service won't redeploy

**Try:**
1. Click **Manual Deploy** → **Deploy latest commit**
2. Or click **Clear build cache & deploy**

### Issue: Different error now

**Check logs for:**
- Alembic migration errors → Check DATABASE_URL format
- Port binding errors → Should be fine (uses $PORT)
- Import errors → Docker build issue (rare)

---

## 📞 Quick Reference

**What you need:**
- Free PostgreSQL URL from Neon/Supabase/ElephantSQL
- Render API service
- 5 minutes

**What you'll have:**
- Working API service with database
- Migrations applied
- Health checks passing
- Ready for web service deployment

**Time saved:**
- No need to create Render PostgreSQL ($7/month)
- No need to learn Render's database linking
- No need to SSH into service
- Just set env var and go!

---

**TL;DR:**
1. Get free PostgreSQL URL from Neon
2. Add `DATABASE_URL` to Render environment
3. Curl the health endpoint to verify

**That's it!** 🎉
