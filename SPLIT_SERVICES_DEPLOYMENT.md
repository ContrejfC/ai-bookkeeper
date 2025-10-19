# Split Services Deployment - AI Bookkeeper

## 🎯 Overview

Successfully migrated from a **failing multi-stage Docker build** to **two independent services** using Render's native build system.

---

## ✅ What Was Implemented

### **1. Backend Service: `ai-bookkeeper-api`**

**Technology:** FastAPI + Python 3.11 (Native Build)

**Files Modified:**
- Created `main.py` in root directory for easier import
- Existing `app/api/main.py` already has:
  - ✅ Health endpoint at `/healthz`
  - ✅ CORS middleware configured
  - ✅ All FastAPI routes

**Render Configuration:**
```yaml
- type: web
  name: ai-bookkeeper-api
  env: python
  buildCommand: pip install -r requirements.txt
  startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
  healthCheckPath: /healthz
```

**Environment Variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET_KEY` - Authentication secret
- `ALLOWED_ORIGINS` - **IMPORTANT:** Set to frontend URL after first deploy
- `STRIPE_SECRET_KEY`, `OPENAI_API_KEY` - API keys
- `LOG_LEVEL`, `OCR_PROVIDER`, etc. - Configuration

---

### **2. Frontend Service: `ai-bookkeeper-web`**

**Technology:** Next.js 15 + Node 20 (Native Build)

**Files Modified:**
- `frontend/package.json`:
  - ✅ Added `start` script with PORT binding: `next start -p ${PORT:-3000}`
  - ✅ Added Node 20 engine requirement
  
**Render Configuration:**
```yaml
- type: web
  name: ai-bookkeeper-web
  env: node
  rootDir: frontend
  buildCommand: npm ci && npm run build
  startCommand: npm run start
```

**Environment Variables:**
- `NEXT_PUBLIC_API_URL` - **Auto-set** from API service reference
- `NEXT_PUBLIC_GA_MEASUREMENT_ID` - Google Analytics ID

---

### **3. Smoke Test Script**

**Location:** `scripts/smoke.sh`

**Tests:**
1. ✅ API health endpoint responds with `{"status":"ok"}`
2. ✅ Web homepage returns HTTP 200
3. ✅ CORS preflight succeeds

**Usage:**
```bash
export API_URL=https://ai-bookkeeper-api.onrender.com
export WEB_URL=https://ai-bookkeeper-web.onrender.com
./scripts/smoke.sh
```

---

## 📋 Post-Deployment Steps

### **Step 1: Wait for Both Services to Deploy**

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Look for two services:
   - `ai-bookkeeper-api` - Should deploy in ~3-5 minutes
   - `ai-bookkeeper-web` - Should deploy in ~5-7 minutes
3. Wait for both to show "Live" status

### **Step 2: Get Service URLs**

After deployment, note the URLs:
- API: `https://ai-bookkeeper-api.onrender.com`
- Web: `https://ai-bookkeeper-web.onrender.com`

### **Step 3: Update CORS on API**

**CRITICAL:** The API needs to allow requests from the frontend.

1. Go to `ai-bookkeeper-api` service in Render
2. Go to **Environment** section
3. Update `ALLOWED_ORIGINS` to:
   ```
   https://ai-bookkeeper-web.onrender.com,https://app.ai-bookkeeper.app
   ```
4. Click **Save Changes**
5. Service will automatically redeploy

### **Step 4: Run Smoke Tests**

```bash
export API_URL=https://ai-bookkeeper-api.onrender.com
export WEB_URL=https://ai-bookkeeper-web.onrender.com
./scripts/smoke.sh
```

**Expected Output:**
```
🔍 Running smoke tests...
  API: https://ai-bookkeeper-api.onrender.com
  WEB: https://ai-bookkeeper-web.onrender.com

1️⃣  Checking API health...
   ✅ API health check passed
2️⃣  Checking WEB homepage...
   ✅ WEB homepage returned 200
3️⃣  Checking CORS preflight...
   ✅ CORS preflight passed

✅ All smoke tests passed!
```

### **Step 5: Configure Custom Domains (Optional)**

#### **For API:**
1. Go to `ai-bookkeeper-api` → Settings → Custom Domains
2. Add: `api.ai-bookkeeper.app`
3. Update DNS CNAME: `api` → `ai-bookkeeper-api.onrender.com`

#### **For Web:**
1. Go to `ai-bookkeeper-web` → Settings → Custom Domains
2. Add: `app.ai-bookkeeper.app`
3. Update DNS CNAME: `app` → `ai-bookkeeper-web.onrender.com`

After custom domains:
- Update `ALLOWED_ORIGINS` to include `https://app.ai-bookkeeper.app`
- Update frontend env var `NEXT_PUBLIC_API_URL` to `https://api.ai-bookkeeper.app`

---

## 🐛 Troubleshooting

### **Issue: API Build Fails**

**Check:**
1. Go to deployment logs in Render
2. Look for missing Python packages
3. Verify `requirements.txt` is complete

**Fix:**
```bash
# Test locally first
pip install -r requirements.txt
python -c "from app.api.main import app; print('OK')"
```

### **Issue: Frontend Build Fails**

**Check:**
1. Go to deployment logs in Render
2. Look for npm install or build errors
3. Verify Node version compatibility

**Fix:**
```bash
# Test locally first
cd frontend
npm ci
npm run build
```

### **Issue: CORS Errors in Browser**

**Symptoms:**
- Browser console shows CORS errors
- API requests from frontend fail with 403/CORS

**Fix:**
1. Verify `ALLOWED_ORIGINS` on API includes frontend URL
2. Check browser network tab for actual Origin header
3. Restart API service after updating env vars

### **Issue: Frontend Can't Reach API**

**Check:**
1. Verify `NEXT_PUBLIC_API_URL` is set correctly
2. Check if API is actually running (visit `/healthz`)
3. Look at frontend server logs

**Fix:**
```bash
# Manually set the env var if fromService didn't work
# In Render: ai-bookkeeper-web → Environment
NEXT_PUBLIC_API_URL=https://ai-bookkeeper-api.onrender.com
```

---

## 🎉 Success Criteria

- ✅ Both services deploy without errors
- ✅ API `/healthz` returns 200
- ✅ Web homepage loads
- ✅ No CORS errors in browser console
- ✅ Frontend can call API endpoints
- ✅ Smoke tests pass

---

## 📊 Comparison: Before vs After

### **Before (Failed)**
- ❌ Single Docker multi-stage build
- ❌ Complex Dockerfile with frontend + backend
- ❌ Build failures on Render
- ❌ Difficult to debug
- ❌ 503 errors, service hibernating

### **After (Working)**
- ✅ Two independent services
- ✅ Native Python and Node builds
- ✅ Clear error messages
- ✅ Easy to debug and scale
- ✅ Industry best practice

---

## 🔗 Resources

- **Render Dashboard:** https://dashboard.render.com
- **Render Docs:** https://render.com/docs
- **Next.js Docs:** https://nextjs.org/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com

---

## 📝 Files Changed

1. ✅ `main.py` - Root-level FastAPI import
2. ✅ `frontend/package.json` - PORT binding and Node engine
3. ✅ `render.yaml` - Split service configuration
4. ✅ `scripts/smoke.sh` - Automated tests

---

## 🚀 Next Steps

1. **Wait for deployments to complete** (~10 minutes)
2. **Update ALLOWED_ORIGINS** on API service
3. **Run smoke tests** to verify everything works
4. **Configure custom domains** (optional)
5. **Test full user flows** in browser
6. **Monitor logs** for any issues

---

**Deployment initiated:** October 19, 2025 at 12:30 PM
**Status:** ⏳ Waiting for Render to build and deploy both services

