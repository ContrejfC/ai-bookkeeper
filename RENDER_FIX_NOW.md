# 🚨 RENDER DEPLOYMENT FIX - DATABASE CONNECTION

**Issue:** Service failing to connect to database  
**Error:** `connection to server at "localhost" refused`  
**Root Cause:** `DATABASE_URL` environment variable not set

---

## ✅ IMMEDIATE FIX (5 minutes)

### Step 1: Create PostgreSQL Database

1. Go to **Render Dashboard** → **New** → **PostgreSQL**
2. **Name:** `ai-bookkeeper-db`
3. **Database Name:** `ai_bookkeeper`
4. **Region:** Oregon
5. **Plan:** Starter (or Free for testing)
6. Click **Create Database**
7. **Wait for database to become "Available"** (2-3 minutes)

### Step 2: Link Database to API Service

**Option A: Via Environment Variable**
1. Go to **API Service** → **Environment** tab
2. Click **Add Environment Variable**
3. **Key:** `DATABASE_URL`
4. **Value:** Click **"Link to Database"** → Select `ai-bookkeeper-db`
5. Click **Save Changes**

**Option B: Manual Connection String** (if Link doesn't work)
1. Go to **Database** → **Info** tab
2. Copy **Internal Database URL** (starts with `postgresql://`)
3. Go to **API Service** → **Environment** tab
4. Add variable:
   - **Key:** `DATABASE_URL`
   - **Value:** (paste the Internal Database URL)
5. Click **Save Changes**

### Step 3: Verify Deployment

After saving, Render will automatically redeploy the API service.

**Watch the logs for:**
```
✓ Single Alembic head confirmed
Running: alembic upgrade head
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial schema baseline
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002_tenant_settings, Add tenant_settings table
...
✅ Database migrations completed
INFO:     Uvicorn running on http://0.0.0.0:10000
```

---

## 🔍 VERIFY IT WORKED

### Check Service Logs
```
Render Dashboard → API Service → Logs

Look for:
✅ "Database migrations completed"
✅ "Uvicorn running on..."
✅ No "Connection refused" errors
```

### Test Health Endpoint
```bash
curl https://YOUR-API-SERVICE.onrender.com/healthz

# Expected response:
{"status":"healthy","database":"connected"}
```

---

## 📋 OTHER REQUIRED ENVIRONMENT VARIABLES

While you're in the Environment tab, also set these:

### Core (Required for startup)
```
ENV=production
JWT_SECRET=[generate: openssl rand -hex 32]
CSRF_SECRET=[generate: openssl rand -hex 32]
LOG_LEVEL=INFO
```

### Optional (Can add later)
```
STRIPE_SECRET_KEY=sk_test_... (or sk_live_...)
QBO_CLIENT_ID=...
QBO_CLIENT_SECRET=...
```

---

## 🚨 IF STILL FAILING

### Issue: Script parsing error
```
scripts/db_migrate.sh: line 23: [: 0
0: integer expression expected
```

**This is a warning, not the cause.** The real issue is DATABASE_URL.

### Issue: Alembic migration fails
**Check:**
1. Database is "Available" in Render Dashboard
2. DATABASE_URL is set and starts with `postgresql://`
3. No typos in the connection string

### Issue: Service won't start at all
**Try:**
1. Click **Manual Deploy** → **Clear build cache & deploy**
2. Check **Events** tab for specific error messages
3. Verify Dockerfile.api path is correct

---

## ✅ SUCCESS CRITERIA

**Service is working when:**
- [ ] Logs show "Database migrations completed"
- [ ] Logs show "Uvicorn running on..."
- [ ] Health check returns 200 OK
- [ ] No "Connection refused" errors

---

## 📞 NEXT STEPS AFTER FIX

Once the API service is running:

1. **Deploy Web Service:**
   - Create new Web Service
   - Use `Dockerfile.web`
   - Set `NEXT_PUBLIC_API_URL` (mark "Available during build")

2. **Follow Launch Guide:**
   - See: `docs/GO_LIVE_NOW.md`
   - Configure Stripe LIVE
   - Configure QBO Production
   - Run launch script

---

**Quick Summary:**
1. Create PostgreSQL database in Render
2. Link database to API service (set DATABASE_URL)
3. Wait for redeploy
4. Verify health check passes

**That's it!** The database connection issue will be resolved.
