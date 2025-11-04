# Cloud Run Deployment Issue Analysis

## Current Status: All Deployments Failing

### Symptoms
- ✅ Docker image builds successfully
- ✅ Image pushes to Artifact Registry
- ❌ Container fails to start in Cloud Run within timeout
- Latest ready revision: `00029-ghm` (old, before all fixes)
- All new revisions (00030-00035): Failed to start

### What We've Fixed So Far
1. ✅ npm dependencies (`npm install --legacy-peer-deps`)
2. ✅ Smart quote syntax error in frontend
3. ✅ Dockerfile inline comments
4. ✅ Missing `config/` directory
5. ✅ Missing imports (`get_current_user`, `Response`)

### Current Problem
**Backend is taking too long to start** - Times out before binding to port.

From logs we've seen:
- Backend starts loading
- Loads middleware
- Tries to import the FastAPI app
- **Takes more than 30 seconds** before health check times out

### Root Cause Hypothesis
The `app/api/main.py` file is doing **too much at module import time**:
- Loading all routes
- Initializing database connections
- Loading ML models/embeddings
- Setting up middleware
- Importing many heavy dependencies

**Cloud Run's startup probe times out before the app is ready.**

### Recommended Solutions

#### Option 1: Lazy Loading (Quickest Fix)
Move heavy initialization to **after** the FastAPI app starts:
- Defer ML model loading until first request
- Use startup events instead of module-level initialization
- Make database connections lazy

#### Option 2: Separate Services
Split into two services:
- **Simple API service** (just auth + basic endpoints)
- **Worker service** (handles ML/AI processing)

#### Option 3: Increase Startup Timeout
```bash
gcloud run services update ai-bookkeeper-api \
  --region=us-central1 \
  --timeout=600 \
  --startup-cpu-boost
```

#### Option 4: Remove Optional Features
Comment out non-essential features temporarily:
- Wave-2 routes
- Entitlement middleware (already showing warnings)
- ML/embeddings (use fallbacks only)

## Immediate Action Plan

### Step 1: Check What's Actually Failing
We need actual logs from revision 00035-z8n to see the current error.

**Try accessing logs from browser:**
1. Go to Cloud Run console
2. Select `ai-bookkeeper-api` service
3. Click on "LOGS" tab
4. Filter by revision `00035-z8n`

### Step 2: If Logs Show Timeout
Implement lazy loading in `app/api/main.py`:
- Move imports inside endpoints
- Use `@app.on_event("startup")` for async initialization
- Defer ML model loading

### Step 3: If Still Failing
Create a **minimal FastAPI app** that just:
- Returns health check
- Has one simple endpoint
- Proves the infrastructure works

Then gradually add features back.

## Questions to Answer
1. What is the EXACT error in revision 00035-z8n logs?
2. How long does the backend actually take to start locally?
3. Are there any blocking database queries on startup?
4. Which imports are taking the longest?

---

**Status:** Blocked on accessing logs for latest revision  
**Next Step:** Get logs for revision ai-bookkeeper-api-00035-z8n








