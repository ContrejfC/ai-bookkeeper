# Deploy Signup Fix to Google Cloud

## ✅ Changes Already Pushed to GitHub

The signup fix has been committed and pushed to GitHub:
- **Commit:** `2282c71` - "fix: Resolve signup JSON parsing error and startup timing issues"
- **Branch:** `main`
- **GitHub URL:** https://github.com/ContrejfC/ai-bookkeeper

## What Was Fixed

1. **JSON Parsing Error** - Frontend now checks response status before parsing JSON
2. **Startup Timing** - Backend waits for health check before starting frontend
3. **Error Messages** - Clear, user-friendly error messages for all scenarios

## Option 1: Deploy via Google Cloud Console (Recommended)

### Step 1: Authenticate with Your Personal Account
```bash
gcloud auth login
gcloud config set account YOUR_EMAIL@gmail.com
gcloud config set project bright-fastness-475700-j2
```

### Step 2: Build and Deploy
```bash
cd /Users/fabiancontreras/ai-bookkeeper
./scripts/deploy_mvp_to_gcp.sh
```

### Or Use the Console UI:
1. Go to [Google Cloud Console - Cloud Run](https://console.cloud.google.com/run?project=bright-fastness-475700-j2)
2. Find your services:
   - `ai-bookkeeper-api-mvp`
   - `ai-bookkeeper-web-mvp`
3. For each service, click **"Edit & Deploy New Revision"**
4. Under "Container image URL", click **"Deploy from source"**
5. Select **"GitHub"** as source and choose the `main` branch
6. Click **"Deploy"**

## Option 2: Fix Service Account Permissions

Your current service account `id-ai-bookkeeper-migration@...` needs these roles:

```bash
# Authenticate with owner account first
gcloud auth login

# Grant necessary permissions to service account
gcloud projects add-iam-policy-binding bright-fastness-475700-j2 \
  --member="serviceAccount:id-ai-bookkeeper-migration@bright-fastness-475700-j2.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding bright-fastness-475700-j2 \
  --member="serviceAccount:id-ai-bookkeeper-migration@bright-fastness-475700-j2.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding bright-fastness-475700-j2 \
  --member="serviceAccount:id-ai-bookkeeper-migration@bright-fastness-475700-j2.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Then retry deployment
./scripts/deploy_mvp_to_gcp.sh
```

## Option 3: Manual Docker Build & Push

If you prefer to build locally:

```bash
# Set project
export PROJECT_ID=bright-fastness-475700-j2

# Authenticate with personal account
gcloud auth login
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build image
cd /Users/fabiancontreras/ai-bookkeeper
docker build -t ai-bookkeeper .

# Tag for Artifact Registry
docker tag ai-bookkeeper \
  us-central1-docker.pkg.dev/${PROJECT_ID}/ai-bookkeeper/fullstack:latest

# Push to registry
docker push us-central1-docker.pkg.dev/${PROJECT_ID}/ai-bookkeeper/fullstack:latest

# Deploy to Cloud Run
gcloud run deploy ai-bookkeeper-web-mvp \
  --image=us-central1-docker.pkg.dev/${PROJECT_ID}/ai-bookkeeper/fullstack:latest \
  --region=us-central1 \
  --platform=managed \
  --port=10000 \
  --allow-unauthenticated
```

## After Deployment

### Verify the Fix

1. **Check Service Status:**
   ```bash
   gcloud run services describe ai-bookkeeper-web-mvp \
     --region=us-central1 \
     --format="value(status.url)"
   ```

2. **Test Signup Flow:**
   - Go to your app URL
   - Navigate to `/signup`
   - Try to create an account
   - **Expected:** Either success or clear error message (NOT JSON parsing error)

3. **Check Logs:**
   ```bash
   # View startup logs to verify health check wait
   gcloud run services logs read ai-bookkeeper-web-mvp \
     --region=us-central1 \
     --limit=50
   ```

   **Look for:**
   ```
   🚀 Starting AI Bookkeeper...
   📡 Starting FastAPI backend on port 8000...
   ⏳ Waiting for backend to be ready...
   ✅ Backend is ready!
   🌐 Starting Next.js frontend on port 10000...
   ✅ Both services started successfully
   ```

### Test Error Handling

**Intentional Test (Optional):**
1. Temporarily set an invalid DATABASE_URL to break the backend
2. Try to sign up
3. **Expected message:** "API endpoint not found. Please ensure the backend is running."
4. **NOT expected:** "Unexpected token 'N', "Not Found " is not valid JSON"

## Current Service URLs

Based on your previous deployment:
- **Frontend:** https://ai-bookkeeper-web-mvp-[random].a.run.app
- **Backend:** https://ai-bookkeeper-api-mvp-[random].a.run.app

To get the exact URLs:
```bash
gcloud run services list --format="table(SERVICE,REGION,URL)"
```

## Rollback (If Needed)

If something goes wrong:
```bash
# List revisions
gcloud run revisions list --service=ai-bookkeeper-web-mvp --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic ai-bookkeeper-web-mvp \
  --to-revisions=PREVIOUS_REVISION_NAME=100 \
  --region=us-central1
```

## Support

If you encounter issues:
1. Check logs: `gcloud run services logs read ai-bookkeeper-web-mvp --region=us-central1`
2. Verify environment variables in Cloud Run console
3. Ensure DATABASE_URL is set correctly
4. Check that backend is healthy: `curl YOUR_BACKEND_URL/healthz`

---

**Status:** Code ready, deployment pending  
**Commit:** 2282c71  
**Next Step:** Choose one of the deployment options above



