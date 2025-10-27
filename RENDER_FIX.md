# RENDER SPLIT SERVICES FIX RUNBOOK

**Objective:** Enforce split services architecture (ai-bookkeeper-api + ai-bookkeeper-web) via Blueprint deployment

---

## 🎯 OVERVIEW

This runbook provides step-by-step instructions to:
1. **Detect drift** between desired and live Render services
2. **Clean up stray services** that don't match render.yaml
3. **Deploy split services** using Render Blueprint
4. **Verify deployment** with health checks and CORS tests

---

## 📋 PREREQUISITES

- ✅ Render account with API access
- ✅ GitHub repository connected to Render
- ✅ `RENDER_API_KEY` environment variable set
- ✅ Python 3.11+ and bash available locally

---

## 🔧 STEP-BY-STEP EXECUTION

### Step 1: Export API Key
```bash
export RENDER_API_KEY=your_render_api_key_here
```

### Step 2: Run Drift Analysis
```bash
python3 scripts/render_fix.py
```

**Expected Output:**
- List of desired services: `ai-bookkeeper-api, ai-bookkeeper-web`
- List of live services (may include stray services)
- Stray services with deletion commands
- Drift report saved to `tmp/render_drift.json`

### Step 3: Clean Up Stray Services

**Option A: Manual Deletion (Recommended)**
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Navigate to each stray service
3. Click "Settings" → "Delete Service"
4. Confirm deletion

**Option B: API Deletion**
```bash
# Use the curl commands printed by render_fix.py
curl -H 'Authorization: Bearer $RENDER_API_KEY' -X DELETE https://api.render.com/v1/services/{service_id}
```

### Step 4: Apply Blueprint Deployment

1. **Go to Render Dashboard**
   - Click "New" → "Blueprint"

2. **Connect Repository**
   - Select your GitHub repository
   - Choose the main branch
   - Render will detect `render.yaml`

3. **Review Configuration**
   - Verify 2 services: `ai-bookkeeper-api` and `ai-bookkeeper-web`
   - Check environment variables are configured
   - Confirm build commands match your repo structure

4. **Deploy Services**
   - Click "Apply" to create services
   - Monitor build logs for both services
   - Wait for deployments to complete (~5-10 minutes)

### Step 5: Configure Environment Variables

**For ai-bookkeeper-api service:**
```bash
DATABASE_URL=<your_postgres_url>
REDIS_URL=<your_redis_url>
JWT_SECRET_KEY=<generated_secret>
PASSWORD_RESET_SECRET=<generated_secret>
ALLOWED_ORIGINS=https://ai-bookkeeper-web.onrender.com
STRIPE_SECRET_KEY=<your_stripe_key>
STRIPE_WEBHOOK_SECRET=<your_webhook_secret>
OPENAI_API_KEY=<your_openai_key>
```

**For ai-bookkeeper-web service:**
```bash
NEXT_PUBLIC_API_URL=https://ai-bookkeeper-api.onrender.com
NEXT_PUBLIC_GA_MEASUREMENT_ID=<your_ga_id>
```

### Step 6: Update CORS Configuration

**After web service is live:**
1. Get the web service URL from Render dashboard
2. Update `ALLOWED_ORIGINS` in api service to include web URL
3. Redeploy api service to apply CORS changes

### Step 7: Run Health Checks

```bash
# Set service URLs
export API_URL="https://ai-bookkeeper-api.onrender.com"
export WEB_URL="https://ai-bookkeeper-web.onrender.com"

# Run comprehensive probe
bash scripts/render_probe.sh
```

**Expected Output:**
```
[probe] API /healthz
[probe] WEB HEAD
[probe] CORS preflight
OK
```

### Step 8: Verify End-to-End Functionality

1. **Test API Health:**
   ```bash
   curl https://ai-bookkeeper-api.onrender.com/healthz
   # Expected: {"status":"ok"}
   ```

2. **Test Web Service:**
   ```bash
   curl -I https://ai-bookkeeper-web.onrender.com/
   # Expected: HTTP 200
   ```

3. **Test CORS:**
   ```bash
   curl -X OPTIONS https://ai-bookkeeper-api.onrender.com/healthz \
     -H "Origin: https://ai-bookkeeper-web.onrender.com" \
     -H "Access-Control-Request-Method: GET"
   # Expected: No errors
   ```

---

## 🚨 TROUBLESHOOTING

### Build Failures

**API Service Build Fails:**
- Check `requirements.txt` exists in repo root
- Verify Python 3.11.9 is available
- Check build logs for missing dependencies

**Web Service Build Fails:**
- Check `frontend/package.json` has correct scripts
- Verify Node 20 is available
- Check build logs for npm errors

### Runtime Issues

**API Returns 502:**
- Check `uvicorn app.api.main:app` command
- Verify `app/api/main.py` exists
- Check environment variables are set

**Web Returns 404:**
- Check `npm run start` command
- Verify `frontend/package.json` has start script
- Check PORT environment variable

**CORS Errors:**
- Verify `ALLOWED_ORIGINS` includes web service URL
- Check API service has CORS middleware enabled
- Ensure preflight requests are handled

### Service Discovery Issues

**Services Not Found:**
- Verify `render.yaml` is in repo root
- Check service names match exactly
- Ensure Blueprint was applied successfully

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Only 2 services exist: `ai-bookkeeper-api` and `ai-bookkeeper-web`
- [ ] Both services build and start successfully
- [ ] API `/healthz` returns `{"status":"ok"}`
- [ ] Web service returns HTTP 200
- [ ] CORS preflight requests succeed
- [ ] `scripts/render_probe.sh` passes all tests
- [ ] No stray services remain in Render dashboard

---

## 🎯 EXPECTED OUTCOME

**Final State:**
- ✅ `ai-bookkeeper-api`: Python service running FastAPI
- ✅ `ai-bookkeeper-web`: Node service running Next.js
- ✅ Both services communicating without CORS errors
- ✅ Ready for custom domain configuration
- ✅ Ready for Google Ads deployment

**Performance Targets:**
- API response time: < 2 seconds
- Web response time: < 5 seconds
- CORS preflight: < 1 second

---

## 📞 SUPPORT

If issues persist:
1. Check Render build logs for specific errors
2. Verify environment variables are correctly set
3. Test services individually before integration
4. Review `tmp/render_drift.json` for configuration issues

**Success Metrics:**
- All health checks pass
- No CORS errors in browser console
- Services respond within performance targets
- Blueprint deployment completes without errors

