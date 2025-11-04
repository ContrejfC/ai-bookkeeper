# Unified Docker Deployment - Setup Guide

## 🎯 What This Does

Deploys **both frontend and backend** to Google Cloud Run in a **single container**, eliminating all the split deployment issues you've been experiencing.

---

## ✅ Benefits of Unified Deployment

| Before (Split) | After (Unified) |
|----------------|-----------------|
| ❌ Frontend on Vercel | ✅ Everything on Cloud Run |
| ❌ Backend on Cloud Run | ✅ Single deployment |
| ❌ NEXT_PUBLIC_API_URL confusion | ✅ Frontend talks to localhost |
| ❌ CORS issues | ✅ Same origin, no CORS |
| ❌ Version sync problems | ✅ Always in sync |
| ❌ 2 deployments to manage | ✅ 1 deployment |

---

## 🚀 Quick Start (30 minutes)

### **Step 1: Install Google Cloud CLI (5 minutes)**

**macOS:**
```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash

# Restart your shell
exec -l $SHELL

# Verify installation
gcloud --version
```

**Alternative (Homebrew):**
```bash
brew install --cask google-cloud-sdk
gcloud --version
```

---

### **Step 2: Authenticate (2 minutes)**

```bash
# Login to Google Cloud
gcloud auth login

# This will open a browser window
# Sign in with your Google account
```

---

### **Step 3: Set Project (2 minutes)**

If you already have a project (you do - `ai-bookkeeper-api-ww4vg3u7eq-uc.a.run.app`):

```bash
# Find your project ID
gcloud projects list

# Set it (replace with your actual project ID)
gcloud config set project YOUR_PROJECT_ID
```

**Don't know your project ID?** Look at your current backend URL:
```
https://ai-bookkeeper-api-ww4vg3u7eq-uc.a.run.app
                         ^^^^^^^^^^^^^^^^
```

Run this to find it:
```bash
gcloud run services list --region us-central1
```

---

### **Step 4: Enable Required APIs (2 minutes)**

```bash
# Enable Cloud Run API
gcloud services enable run.googleapis.com

# Enable Cloud Build API (for building Docker images)
gcloud services enable cloudbuild.googleapis.com

# Enable Artifact Registry (for storing images)
gcloud services enable artifactregistry.googleapis.com
```

---

### **Step 5: Set Database URL (1 minute)**

```bash
# Set your Neon PostgreSQL connection string
export DATABASE_URL='postgresql://neondb_owner:npg_Gt8ocPATC3hQ@ep-summer-fog-aftcltuf-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require'
```

---

### **Step 6: Deploy! (15 minutes)**

```bash
# Navigate to your project
cd /Users/fabiancontreras/ai-bookkeeper

# Run the deployment script
bash scripts/deploy_unified.sh
```

This will:
1. ⚙️ Build your Docker image (frontend + backend)
2. ☁️ Push to Google Container Registry
3. 🚀 Deploy to Cloud Run
4. 🔗 Give you a live URL
5. ✅ Run smoke tests

---

## 📊 What Happens During Deployment?

```
┌─────────────────────────────────────────┐
│  1. Docker Build (8-10 minutes)         │
│     - Build Next.js frontend            │
│     - Install Python dependencies       │
│     - Create production image           │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  2. Push to Registry (2-3 minutes)      │
│     - Upload image to GCP               │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  3. Deploy to Cloud Run (2-3 minutes)   │
│     - Start container                   │
│     - Health checks                     │
│     - Assign URL                        │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  4. Your App is Live! 🎉                │
│     Frontend + Backend working together │
└─────────────────────────────────────────┘
```

---

## 🧪 After Deployment

You'll get a URL like:
```
https://ai-bookkeeper-xxxxx.run.app
```

This URL serves:
- ✅ Frontend (landing page, dashboard, etc.)
- ✅ Backend API (`/api/*`)
- ✅ API Documentation (`/docs`)
- ✅ Health checks (`/api/health`)

---

## 🔄 Updating Your App

After making code changes:

```bash
# Just run the script again!
bash scripts/deploy_unified.sh
```

Cloud Run will:
- Build the new image
- Deploy with zero downtime
- Route traffic to the new version

---

## 🧹 Cleanup Old Deployments

After the unified deployment is working:

1. **Vercel (Frontend)**
   - Go to Vercel dashboard
   - Delete the `ai-bookkeeper` project
   - ✅ Saves $20/month

2. **Old Cloud Run Backend** (optional)
   ```bash
   # If you want to keep the old backend as backup, skip this
   # Otherwise, delete it:
   gcloud run services delete ai-bookkeeper-api --region us-central1
   ```

---

## 🎯 Success Criteria

After deployment, verify:

- [ ] Frontend loads: `https://ai-bookkeeper-xxxxx.run.app`
- [ ] Can sign up for an account
- [ ] Can log in
- [ ] Dashboard loads
- [ ] Upload page works
- [ ] Transactions page works
- [ ] Export page works
- [ ] No "Error loading access information" errors

---

## 🐛 Troubleshooting

### **Build fails**
```bash
# Check Cloud Build logs
gcloud builds list --limit 5
gcloud builds log BUILD_ID
```

### **Service won't start**
```bash
# Check Cloud Run logs
gcloud run services logs tail ai-bookkeeper --region us-central1
```

### **404 errors**
- Frontend should proxy `/api/*` to backend automatically
- Check that `NEXT_PUBLIC_API_URL=http://localhost:8000` in Cloud Run env vars

### **Database connection fails**
- Verify `DATABASE_URL` is set correctly
- Check that it includes `sslmode=require`

---

## 📞 Support

If you get stuck:
1. Check Cloud Run logs: `gcloud run services logs tail ai-bookkeeper --region us-central1`
2. Check build logs: `gcloud builds list --limit 5`
3. Verify environment variables in Cloud Console

---

## 🎊 You're Almost There!

Once `gcloud` is installed, you're just **one command away**:

```bash
bash scripts/deploy_unified.sh
```

Let's get started! 🚀





