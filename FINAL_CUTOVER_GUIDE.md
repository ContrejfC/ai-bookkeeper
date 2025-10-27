# Google Cloud Run Frontend + DNS Cutover - Final Guide

## 🎯 CURRENT STATUS

### ✅ COMPLETED
- **API Deployed:** Cloud Run API live at `https://ai-bookkeeper-api-644842661403.us-central1.run.app`
- **Database:** Neon PostgreSQL connected and operational
- **CORS Configured:** Origins set to `https://app.ai-bookkeeper.app,https://ai-bookkeeper-web.onrender.com`
- **Smoke Tests:** Script created at `scripts/smoke_cutover.sh`
- **Documentation:** DNS setup guide at `tmp/MANUAL_DNS_SETUP.md`

### 🔄 PENDING (REQUIRES MANUAL ACTION)
- **Frontend Update:** Update NEXT_PUBLIC_API_URL in Render
- **DNS Setup:** Configure custom domain (optional)
- **Final Verification:** Run smoke tests after frontend update

---

## 🚀 IMMEDIATE ACTION REQUIRED

### STEP 1: Update Frontend in Render (5 minutes)

#### Option A: Automated (if you have RENDER_API_KEY)
```bash
export RENDER_API_KEY="your_render_api_key"
bash scripts/render_set_env.sh "ai-bookkeeper-web" "NEXT_PUBLIC_API_URL" "https://ai-bookkeeper-api-644842661403.us-central1.run.app"
```

#### Option B: Manual (recommended if no API key)
See detailed instructions in: `tmp/MANUAL_FRONTEND_UPDATE.md`

**Quick Steps:**
1. Go to https://dashboard.render.com/
2. Find service: **ai-bookkeeper-web**
3. Go to **Environment** tab
4. Update **NEXT_PUBLIC_API_URL** to:
   ```
   https://ai-bookkeeper-api-644842661403.us-central1.run.app
   ```
5. Click **"Save Changes"**
6. Click **"Manual Deploy"** if auto-deploy doesn't trigger

---

### STEP 2: Verify Frontend Deployment (2 minutes)

```bash
# Wait for Render deployment to complete (3-5 minutes)
# Then check the frontend
curl -I https://ai-bookkeeper-web.onrender.com

# Should return 200 OK
```

---

### STEP 3: Run Smoke Tests (1 minute)

```bash
# Run automated smoke tests
bash scripts/smoke_cutover.sh \
  "https://ai-bookkeeper-api-644842661403.us-central1.run.app" \
  "https://ai-bookkeeper-web.onrender.com"
```

**Expected Output:**
- ✅ API root endpoint responds correctly
- ✅ API documentation accessible
- ✅ Web frontend reachable
- ✅ CORS preflight succeeds

---

### STEP 4: Browser Verification (3 minutes)

1. Open https://ai-bookkeeper-web.onrender.com in browser
2. Open Developer Console (F12)
3. Go to **Console** tab
4. Try logging in or signing up
5. **Check for errors:**
   - ❌ CORS errors → CORS not configured correctly
   - ❌ Network errors → API not reachable
   - ✅ No errors → Everything working!

---

## 🌐 OPTIONAL: Custom Domain Setup

### Prerequisites
- Cloudflare account with access to `ai-bookkeeper.app`
- DNS propagation time: 5-10 minutes
- SSL certificate provisioning: 10-30 minutes

### Instructions
See detailed guide: `tmp/MANUAL_DNS_SETUP.md`

**Quick Steps:**
1. Add CNAME record in Cloudflare:
   - Name: `api`
   - Target: `ghs.googlehosted.com`
   - Proxy: Disabled (gray cloud)
2. Wait 5-10 minutes for DNS propagation
3. Wait 10-30 minutes for SSL certificate
4. Update frontend to use `https://api.ai-bookkeeper.app`
5. Update CORS to include custom domain

---

## 📊 CONFIGURATION SUMMARY

### Current Configuration
```yaml
API URL (Direct):
  https://ai-bookkeeper-api-644842661403.us-central1.run.app

API URL (Custom, after DNS setup):
  https://api.ai-bookkeeper.app

Frontend URL:
  https://ai-bookkeeper-web.onrender.com

Custom Frontend URL (if configured):
  https://app.ai-bookkeeper.app

CORS Origins:
  - https://app.ai-bookkeeper.app
  - https://ai-bookkeeper-web.onrender.com

Database:
  postgresql://neondb_owner:***@ep-summer-fog-aftcltuf-pooler.us-west-2.aws.neon.tech/neondb
```

---

## 🔧 TROUBLESHOOTING

### Frontend Not Updating
**Symptom:** Old API URL still being used after update

**Solutions:**
1. Check environment variable was saved in Render
2. Verify deployment completed successfully
3. Check deploy logs in Render dashboard
4. Clear browser cache (Ctrl+Shift+Delete)
5. Try incognito/private browsing mode

### CORS Errors
**Symptom:** "No 'Access-Control-Allow-Origin' header" in browser console

**Solutions:**
1. Verify CORS origins include exact frontend URL (no trailing slash)
2. Check Cloud Run environment variables:
   ```bash
   gcloud run services describe ai-bookkeeper-api \
     --region us-central1 \
     --format="get(spec.template.spec.containers[0].env)"
   ```
3. Update CORS if needed:
   ```bash
   cat > tmp/env_vars.yaml << EOF
   ALLOWED_ORIGINS: "https://app.ai-bookkeeper.app,https://ai-bookkeeper-web.onrender.com"
   EOF
   
   gcloud run services update ai-bookkeeper-api \
     --region us-central1 \
     --env-vars-file tmp/env_vars.yaml \
     --quiet
   ```

### API Not Responding
**Symptom:** 502 Bad Gateway or timeout errors

**Solutions:**
1. Check Cloud Run service status:
   ```bash
   gcloud run services describe ai-bookkeeper-api --region us-central1
   ```
2. Check Cloud Run logs:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ai-bookkeeper-api" \
     --limit 50 --format json
   ```
3. Verify database connection is working
4. Check for startup errors in logs

### DNS Not Resolving
**Symptom:** `api.ai-bookkeeper.app` not reachable

**Solutions:**
1. Verify CNAME record in Cloudflare DNS
2. Check DNS propagation:
   ```bash
   dig api.ai-bookkeeper.app
   ```
3. Ensure proxy is disabled (gray cloud in Cloudflare)
4. Wait 5-10 minutes and try again

### SSL Certificate Issues
**Symptom:** "Certificate not valid" or HTTPS not working

**Solutions:**
1. Verify DNS is resolving correctly first
2. Check domain mapping status:
   ```bash
   gcloud beta run domain-mappings describe api.ai-bookkeeper.app \
     --platform managed --region us-central1
   ```
3. Wait up to 30 minutes for automatic certificate provisioning
4. Ensure domain ownership is verified

---

## 🔄 ROLLBACK PLAN

### If Critical Issues Occur

#### Rollback Frontend
```bash
# Option 1: Via Render Dashboard
1. Go to Render dashboard
2. Find ai-bookkeeper-web service
3. Go to Environment tab
4. Change NEXT_PUBLIC_API_URL back to old Render API URL
5. Deploy

# Option 2: Via API (if RENDER_API_KEY set)
bash scripts/render_set_env.sh "ai-bookkeeper-web" "NEXT_PUBLIC_API_URL" "<old_render_api_url>"
```

#### Rollback DNS (if custom domain was set up)
```bash
# In Cloudflare:
1. Remove or disable the CNAME record for api.ai-bookkeeper.app
2. Update frontend NEXT_PUBLIC_API_URL back to direct Cloud Run URL
```

#### Keep Render Services
- **DO NOT delete Render services for 48 hours minimum**
- Use as backup during transition
- Only delete after confirming Cloud Run is 100% stable

---

## 📈 POST-CUTOVER MONITORING

### Immediate Monitoring (First 24 Hours)
```bash
# Check API health every 5 minutes
watch -n 300 'curl -s https://ai-bookkeeper-api-644842661403.us-central1.run.app/ | jq'

# Monitor Cloud Run logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=ai-bookkeeper-api"

# Check error rate
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ai-bookkeeper-api AND severity>=ERROR" \
  --limit 10 --format json
```

### Set Up Alerting (Recommended)
```bash
# Create uptime check
gcloud monitoring uptime create \
  --display-name='AI Bookkeeper API Health' \
  --resource-type='cloud_run_revision' \
  --resource-labels='service_name=ai-bookkeeper-api,location=us-central1' \
  --http-check-path='/' \
  --http-check-port='443' \
  --http-check-use-ssl \
  --check-interval='60s' \
  --timeout='10s'
```

---

## 🎯 SUCCESS CRITERIA

### Cutover is Complete When:
- [ ] Frontend NEXT_PUBLIC_API_URL updated to Cloud Run
- [ ] Frontend deploys successfully on Render
- [ ] Smoke tests pass (all 4 tests)
- [ ] Browser loads app without CORS errors
- [ ] Users can log in/sign up successfully
- [ ] API calls work from frontend
- [ ] No errors in browser console
- [ ] Cloud Run logs show successful requests

### Optional Success Criteria (if custom domain set up):
- [ ] api.ai-bookkeeper.app resolves in DNS
- [ ] SSL certificate is active
- [ ] Frontend using custom domain URL
- [ ] CORS updated to include custom domain

---

## 📞 NEXT STEPS AFTER CUTOVER

### 1. Monitoring (Day 1)
- Watch Cloud Run logs for errors
- Monitor response times
- Check error rates
- Verify database connections

### 2. Render Decommission (Day 3)
- Confirm Cloud Run is stable
- Disable auto-deploy on Render services
- Keep services for 1 week as backup

### 3. Google Ads Launch (Day 3-7)
- Verify system stability
- Confirm all features working
- Run final end-to-end tests
- **Launch Google Ads campaigns!** 🚀

### 4. Final Cleanup (Week 2)
- Delete Render services
- Remove old environment variables
- Update documentation
- Archive migration notes

---

## 📚 REFERENCE FILES

- **Render Update Script:** `scripts/render_set_env.sh`
- **Smoke Tests:** `scripts/smoke_cutover.sh`
- **Manual Frontend Update:** `tmp/MANUAL_FRONTEND_UPDATE.md`
- **Manual DNS Setup:** `tmp/MANUAL_DNS_SETUP.md`
- **Cutover Summary:** `CUTOVER_SUMMARY.md`
- **Migration Complete:** `GOOGLE_CLOUD_MIGRATION_COMPLETE_SUMMARY.md`

---

## ⚡ QUICK REFERENCE

### Essential URLs
```
API (Direct):     https://ai-bookkeeper-api-644842661403.us-central1.run.app
API (Custom):     https://api.ai-bookkeeper.app (after DNS setup)
Frontend:         https://ai-bookkeeper-web.onrender.com
Frontend (Custom): https://app.ai-bookkeeper.app (if configured)
API Docs:         https://ai-bookkeeper-api-644842661403.us-central1.run.app/docs
```

### Essential Commands
```bash
# Update frontend (automated)
bash scripts/render_set_env.sh "ai-bookkeeper-web" "NEXT_PUBLIC_API_URL" "https://ai-bookkeeper-api-644842661403.us-central1.run.app"

# Run smoke tests
bash scripts/smoke_cutover.sh "$API_RUN_URL" "$WEB_URL"

# Update CORS
gcloud run services update ai-bookkeeper-api --region us-central1 --env-vars-file tmp/env_vars.yaml

# Check API health
curl https://ai-bookkeeper-api-644842661403.us-central1.run.app/

# View logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=ai-bookkeeper-api"
```

---

**🎉 You're almost there! Just update the frontend and you're ready for Google Ads!**
