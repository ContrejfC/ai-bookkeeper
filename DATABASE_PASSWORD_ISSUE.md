# Database Authentication Issue

## 🔴 CRITICAL: Database Password Incorrect

### Problem
The Neon database password is failing authentication:
```
ERROR: password authentication failed for user 'neondb_owner'
```

### Current Database Connection String (INVALID)
```
postgresql://neondb_owner:npg_f1nD7XhKekjp@ep-summer-fog-aftcltuf-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require
```

## Root Cause

The password `npg_f1nD7XhKekjp` is no longer valid for the Neon database. This could be because:
1. Password was rotated
2. Connection string was incorrect from the start
3. Database was recreated with new credentials

## Impact

### What Works:
- ✅ Frontend deployed and accessible
- ✅ API container builds successfully
- ✅ Auth routes load correctly
- ✅ All code is functional

### What's Broken:
- ❌ Database connection fails
- ❌ Cannot create users
- ❌ Cannot log in
- ❌ All database operations fail

## Resolution Required

### Step 1: Get Correct Neon Database Credentials

Go to your Neon dashboard:
1. Open https://console.neon.tech/
2. Find your project: `ep-summer-fog-aftcltuf`
3. Click "Connection Details" or "Connection String"
4. Copy the **correct** PostgreSQL connection string

It should look like:
```
postgresql://neondb_owner:CORRECT_PASSWORD@ep-summer-fog-aftcltuf-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require
```

### Step 2: Update Cloud Run Environment

Once you have the correct DATABASE_URL:

```bash
# Create env file with correct credentials
cat > tmp/env_database.yaml << EOF
DATABASE_URL: "postgresql://neondb_owner:CORRECT_PASSWORD@ep-summer-fog-aftcltuf-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require"
ALLOWED_ORIGINS: "https://frontend-ma4iv9gxo-contrejfcs-projects.vercel.app,https://app.ai-bookkeeper.app"
EOF

# Deploy with correct credentials
gcloud run deploy ai-bookkeeper-api \
  --image us-central1-docker.pkg.dev/bright-fastness-475700-j2/app/api:latest \
  --region us-central1 \
  --project bright-fastness-475700-j2 \
  --env-vars-file tmp/env_database.yaml \
  --min-instances 1 \
  --max-instances 10 \
  --cpu 2 \
  --memory 2Gi \
  --timeout 600s \
  --cpu-boost
```

### Step 3: Test Locally First (Recommended)

Before deploying, test with the correct credentials:

```bash
export DATABASE_URL="postgresql://neondb_owner:CORRECT_PASSWORD@ep-summer-fog-aftcltuf-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require"
export PYTHONPATH=/Users/fabiancontreras/ai-bookkeeper
export ALLOWED_ORIGINS="https://frontend-ma4iv9gxo-contrejfcs-projects.vercel.app"

# Test
python3 -m uvicorn app.api.main_minimal:app --port 8080 &
sleep 5
curl -X POST http://localhost:8080/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test1234","full_name":"Test"}'
```

If this returns `{"success": true, ...}` then we're good to deploy!

## Alternative Solution: Use SQLite Temporarily

If you can't get the Neon credentials right now, we could temporarily use SQLite:

```bash
# Deploy without DATABASE_URL (will use default SQLite)
gcloud run deploy ai-bookkeeper-api \
  --image us-central1-docker.pkg.dev/bright-fastness-475700-j2/app/api:latest \
  --region us-central1 \
  --update-env-vars "ALLOWED_ORIGINS=https://frontend-ma4iv9gxo-contrejfcs-projects.vercel.app,https://app.ai-bookkeeper.app" \
  --remove-env-vars DATABASE_URL
```

**Note:** SQLite won't persist across container restarts on Cloud Run, so this is only for testing.

## What I Need From You

**Please provide the correct Neon database connection string** from your Neon dashboard:
https://console.neon.tech/

Once I have that, I can:
1. Test locally to verify it works
2. Deploy to Cloud Run with correct credentials
3. Verify signup works end-to-end
4. Complete the Google Ads launch prep

---

**Status:** Blocked on correct database credentials  
**Impact:** Production signup not working  
**ETA to Fix:** 10 minutes after credentials provided
