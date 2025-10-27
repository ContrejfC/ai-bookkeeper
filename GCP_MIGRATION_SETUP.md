# Google Cloud Run Migration - Complete Setup Guide

**Status:** Ready to execute migration  
**Prerequisites:** Need Google Cloud setup  
**Estimated Time:** 30-45 minutes

---

## 🚨 IMMEDIATE ACTION REQUIRED

To execute the migration **right now**, you need to complete these steps:

### **Step 1: Install Google Cloud CLI (5 minutes)**

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Verify installation
gcloud --version
```

### **Step 2: Create Google Cloud Project (5 minutes)**

1. **Go to:** https://console.cloud.google.com/
2. **Create new project** or select existing
3. **Note the Project ID** (e.g., `ai-bookkeeper-prod`)
4. **Enable billing** (required for Cloud Run)

### **Step 3: Create Service Account (10 minutes)**

1. **Go to:** IAM & Admin > Service Accounts
2. **Click:** "Create Service Account"
3. **Name:** `ai-bookkeeper-migration`
4. **Add these roles:**
   - Cloud Run Admin (`run.admin`)
   - Cloud Build Editor (`cloudbuild.builds.editor`)
   - Artifact Registry Writer (`artifactregistry.writer`)
   - Secret Manager Admin (`secretmanager.admin`)
   - Service Account User (`iam.serviceAccountUser`)
5. **Create and download JSON key**

### **Step 4: Enable Required APIs (5 minutes)**

```bash
# Replace PROJECT_ID with your actual project ID
export PROJECT="your-project-id"
gcloud config set project $PROJECT

# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### **Step 5: Set Environment Variables (2 minutes)**

```bash
# Required variables
export PROJECT="your-project-id"
export REGION="us-central1"
export GCP_SA_JSON_PATH="/path/to/downloaded/service-account.json"
export WEB_ORIGINS="https://app.ai-bookkeeper.app,https://ai-bookkeeper-web.onrender.com"
export JWT_SECRET="$(openssl rand -hex 32)"

# Optional variables
export MIGRATE_WEB=false
export DOMAIN_ROOT="ai-bookkeeper.app"
export CLOUDFLARE_API_TOKEN="your-cloudflare-token"  # if you have one
export CLOUDFLARE_ZONE_ID="your-zone-id"  # if you have one
```

---

## 🚀 EXECUTE MIGRATION

Once prerequisites are complete:

```bash
# 1. Check prerequisites
bash scripts/check_prerequisites.sh

# 2. Run migration
bash scripts/gcp_migrate.sh

# 3. Get service URLs
export API_URL="$(cat tmp/API_URL.txt)"
echo "API URL: $API_URL"

# 4. Run smoke tests
bash scripts/smoke.sh
```

---

## 📋 EXPECTED RESULTS

After successful migration:

- **API Service:** `https://ai-bookkeeper-api-[hash]-uc.a.run.app`
- **Health Check:** `GET /healthz` returns `{"status":"ok"}`
- **DNS:** `api.ai-bookkeeper.app` → API service
- **CORS:** Properly configured
- **Monitoring:** Full Cloud Run metrics

---

## 🔧 POST-MIGRATION STEPS

### **1. Update CORS (after DNS propagation)**
```bash
gcloud run services update ai-bookkeeper-api \
  --region us-central1 \
  --set-env-vars "ALLOWED_ORIGINS=https://app.ai-bookkeeper.app,https://your-web-domain.com"
```

### **2. Update Frontend**
Update your frontend (Vercel/Render) with:
```
NEXT_PUBLIC_API_URL=https://ai-bookkeeper-api-[hash]-uc.a.run.app
```

### **3. DNS Cutover**
- **If Cloudflare token provided:** DNS records created automatically
- **If manual:** Create CNAME `api` → `[API_URL host]`

### **4. Render Cleanup**
After traffic is stable:
1. Disable auto-deploy on Render
2. Monitor Cloud Run metrics
3. Remove Render services

---

## 🚨 TROUBLESHOOTING

### **Deploy Fails**
- Check Cloud Build logs
- Verify service account has required roles
- Ensure billing is enabled

### **403 Errors**
- Confirm `gcloud config set project $PROJECT`
- Check service account permissions

### **502 Errors**
- Verify `uvicorn app.api.main:app` command
- Check `/healthz` endpoint exists

### **CORS Errors**
- Ensure exact origin in `ALLOWED_ORIGINS`
- No trailing slashes in origins
- Include scheme (https://)

---

## 🎯 SUCCESS CRITERIA

- [ ] API responds to `/healthz` with `{"status":"ok"}`
- [ ] Frontend can call API without CORS errors
- [ ] DNS points to Cloud Run service
- [ ] Smoke tests pass
- [ ] Monitoring shows healthy metrics

---

## 📞 NEXT STEPS

1. **Complete prerequisites** (30 minutes)
2. **Run migration** (10 minutes)
3. **Test and verify** (5 minutes)
4. **Update DNS and frontend** (5 minutes)
5. **Monitor and optimize** (ongoing)

**Ready to migrate? Complete the prerequisites and run the migration!** 🚀






