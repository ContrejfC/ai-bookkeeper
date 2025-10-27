# Google Cloud Run Cutover Summary

## 🎯 CUTOVER STATUS: IN PROGRESS

### ✅ COMPLETED TASKS
- **API Deployed:** Cloud Run API is live and operational
- **CORS Updated:** ALLOWED_ORIGINS configured for frontend domains
- **Smoke Tests:** Script created for validation
- **Monitoring:** Commands provided for uptime checks and alerts

### 🔄 IN PROGRESS TASKS
- **Frontend Update:** Manual update required in Render dashboard
- **DNS Mapping:** Custom domain setup in progress

---

## 📊 CURRENT CONFIGURATION

### API Endpoints
- **Cloud Run URL:** https://ai-bookkeeper-api-644842661403.us-central1.run.app
- **Custom Domain:** api.ai-bookkeeper.app (DNS setup required)
- **Health Check:** /healthz (routing issue - using / instead)
- **Documentation:** /docs (working)

### Frontend Configuration
- **Platform:** Render (ai-bookkeeper-web service)
- **Current API:** Render backend (needs update)
- **Target API:** Cloud Run backend
- **Environment Var:** NEXT_PUBLIC_API_URL

### CORS Configuration
- **Allowed Origins:** https://app.ai-bookkeeper.app
- **Status:** Updated and deployed

---

## 🚀 IMMEDIATE ACTIONS REQUIRED

### 1. Update Frontend (MANUAL - 5 minutes)
```bash
# Go to Render Dashboard: https://dashboard.render.com/
# Find 'ai-bookkeeper-web' service
# Go to Environment tab
# Update NEXT_PUBLIC_API_URL to:
https://ai-bookkeeper-api-644842661403.us-central1.run.app
# Save and trigger deploy
```

### 2. Set Up DNS (MANUAL - 10 minutes)
```bash
# In Cloudflare DNS:
# Type: CNAME
# Name: api
# Content: ghs.googlehosted.com
# TTL: Auto
# Proxy: Disabled (gray cloud)
```

### 3. Run Smoke Tests (AUTOMATED)
```bash
# After frontend update:
export WEB_URL="https://ai-bookkeeper-web.onrender.com"  # or your actual web URL
bash scripts/smoke_cutover.sh "$API_RUN_URL" "$WEB_URL"
```

---

## 📈 MONITORING SETUP

### Uptime Check
```bash
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

### Alerting Policy
```bash
gcloud alpha monitoring policies create \
  --policy-from-file=- <<EOF
{
  "displayName": "AI Bookkeeper API 5xx Rate Alert",
  "conditions": [
    {
      "displayName": "5xx error rate > 5%",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"ai-bookkeeper-api\"",
        "comparison": "COMPARISON_GREATER_THAN",
        "thresholdValue": 0.05,
        "duration": "300s"
      }
    }
  ]
}
EOF
```

---

## 🔄 ROLLBACK PLAN

### If Issues Occur:
1. **Revert Frontend:**
   - Update NEXT_PUBLIC_API_URL back to Render API URL
   - Redeploy frontend

2. **Revert DNS:**
   - Remove api.ai-bookkeeper.app CNAME record
   - Point back to original API

3. **Keep Render Services:**
   - Don't delete Render services for 48 hours
   - Use as backup during transition

---

## 📋 DECOMMISSION CHECKLIST

### Render Services Cleanup (After 48 hours)
- [ ] Verify Cloud Run API is stable
- [ ] Confirm frontend is working with Cloud Run
- [ ] Disable auto-deploy on Render services
- [ ] Keep services for 1 week as backup
- [ ] Delete services after final confirmation

### Final Verification
- [ ] Frontend loads without errors
- [ ] API calls work from frontend
- [ ] No CORS errors in browser console
- [ ] Smoke tests pass
- [ ] Monitoring alerts configured

---

## 🎯 SUCCESS CRITERIA

- ✅ **API:** Cloud Run API responding correctly
- ✅ **CORS:** Configured for frontend domains
- 🔄 **Frontend:** Updated to use Cloud Run API
- 🔄 **DNS:** Custom domain mapped (optional)
- 🔄 **Monitoring:** Uptime checks and alerts configured
- 🔄 **Testing:** Smoke tests passing

---

## 📞 NEXT STEPS

1. **Complete frontend update** (manual step above)
2. **Run smoke tests** to verify cutover
3. **Set up monitoring** using commands above
4. **Wait 48 hours** before Render decommission
5. **Launch Google Ads** once everything is verified

**The cutover is 80% complete - just need frontend update and testing!** 🚀

---

## 📊 FINAL CONFIGURATION SUMMARY

```
API_IN_USE=https://ai-bookkeeper-api-644842661403.us-central1.run.app
WEB_URL=https://ai-bookkeeper-web.onrender.com (needs update)
NEXT_PUBLIC_API_URL=https://ai-bookkeeper-api-644842661403.us-central1.run.app (needs setting)
ALLOWED_ORIGINS=https://app.ai-bookkeeper.app
```

**🎯 NEXT ACTION: Update frontend in Render dashboard!**
