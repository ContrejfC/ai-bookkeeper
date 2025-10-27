# Updated Google Cloud Run Cutover Plan

## 🎯 CURRENT SITUATION DISCOVERED

### What We Found
- ✅ **Backend:** Successfully migrated to Google Cloud Run
- ✅ **API URL:** https://ai-bookkeeper-api-644842661403.us-central1.run.app
- ✅ **Database:** Neon PostgreSQL connected and working
- ❌ **Frontend:** NOT currently deployed anywhere
- ⚠️  **Render:** Only `ai-bookkeeper-redis` service exists

### What This Means
The frontend has never been deployed to production! We need to deploy it for the first time.

---

## 🚀 UPDATED DEPLOYMENT STRATEGY

### Option 1: Deploy Frontend to Vercel (RECOMMENDED - Fastest)
**Time:** 10 minutes  
**Cost:** Free  
**Advantages:**
- Optimized for Next.js
- Automatic HTTPS and CDN
- Zero configuration
- Instant deployments
- Better performance than Render

### Option 2: Deploy Frontend to Render
**Time:** 15 minutes  
**Cost:** $7/month  
**Advantages:**
- Everything in one platform
- Consistent management
- Known platform

### Option 3: Deploy Frontend to Google Cloud Run
**Time:** 20 minutes  
**Cost:** ~$5-10/month  
**Advantages:**
- Everything in Google Cloud
- Consistent infrastructure
- Same monitoring/logging

---

## 📋 OPTION 1: VERCEL DEPLOYMENT (RECOMMENDED)

### Step 1: Install Vercel CLI
```bash
npm install -g vercel
```

### Step 2: Deploy Frontend
```bash
cd frontend
vercel login
vercel --prod
```

### Step 3: Configure Environment Variables
In Vercel dashboard (or via CLI):
```bash
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://ai-bookkeeper-api-644842661403.us-central1.run.app
```

### Step 4: Update CORS
```bash
# Get your Vercel URL from the deploy output (e.g., https://ai-bookkeeper.vercel.app)
# Then update CORS:

cat > tmp/env_vars_vercel.yaml << EOF
ALLOWED_ORIGINS: "https://app.ai-bookkeeper.app,https://ai-bookkeeper.vercel.app"
EOF

gcloud run services update ai-bookkeeper-api \
  --region us-central1 \
  --env-vars-file tmp/env_vars_vercel.yaml \
  --quiet
```

### Step 5: Test
```bash
# Get your Vercel URL
VERCEL_URL="<your-vercel-url>"

bash scripts/smoke_cutover.sh \
  "https://ai-bookkeeper-api-644842661403.us-central1.run.app" \
  "$VERCEL_URL"
```

### Step 6: Set Up Custom Domain (Optional)
1. Go to Vercel dashboard
2. Project Settings → Domains
3. Add: `app.ai-bookkeeper.app`
4. Configure DNS in Cloudflare as instructed by Vercel

---

## 📋 OPTION 2: RENDER DEPLOYMENT

### Step 1: Create New Web Service in Render
1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"Web Service"**
3. Connect your repository
4. Configure:
   - **Name:** ai-bookkeeper-web
   - **Root Directory:** frontend
   - **Build Command:** `npm install && npm run build`
   - **Start Command:** `npm run start`

### Step 2: Set Environment Variables
Add in Render dashboard:
```
NEXT_PUBLIC_API_URL=https://ai-bookkeeper-api-644842661403.us-central1.run.app
NODE_VERSION=20
```

### Step 3: Deploy and Get URL
Wait for deployment, then note the URL (e.g., https://ai-bookkeeper-web.onrender.com)

### Step 4: Update CORS
```bash
cat > tmp/env_vars_render.yaml << EOF
ALLOWED_ORIGINS: "https://app.ai-bookkeeper.app,https://ai-bookkeeper-web.onrender.com"
EOF

gcloud run services update ai-bookkeeper-api \
  --region us-central1 \
  --env-vars-file tmp/env_vars_render.yaml \
  --quiet
```

### Step 5: Test
```bash
bash scripts/smoke_cutover.sh \
  "https://ai-bookkeeper-api-644842661403.us-central1.run.app" \
  "https://ai-bookkeeper-web.onrender.com"
```

---

## 📋 OPTION 3: GOOGLE CLOUD RUN DEPLOYMENT

### Step 1: Build Frontend Docker Image
```bash
cd frontend

# Create Dockerfile if not exists
cat > Dockerfile << 'EOF'
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
ENV PORT=3000
EXPOSE 3000
CMD ["npm", "run", "start"]
EOF
```

### Step 2: Deploy to Cloud Run
```bash
# Build and push image
gcloud builds submit --tag gcr.io/bright-fastness-475700-j2/web:latest

# Deploy service
gcloud run deploy ai-bookkeeper-web \
  --image gcr.io/bright-fastness-475700-j2/web:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --port 3000 \
  --min-instances 0 \
  --max-instances 5 \
  --cpu 1 \
  --memory 512Mi \
  --set-env-vars "NEXT_PUBLIC_API_URL=https://ai-bookkeeper-api-644842661403.us-central1.run.app"
```

### Step 3: Get URL
```bash
WEB_URL=$(gcloud run services describe ai-bookkeeper-web --region us-central1 --format='value(status.url)')
echo "Web URL: $WEB_URL"
```

### Step 4: Update CORS
```bash
cat > tmp/env_vars_gcp.yaml << EOF
ALLOWED_ORIGINS: "https://app.ai-bookkeeper.app,$WEB_URL"
EOF

gcloud run services update ai-bookkeeper-api \
  --region us-central1 \
  --env-vars-file tmp/env_vars_gcp.yaml \
  --quiet
```

### Step 5: Test
```bash
bash scripts/smoke_cutover.sh \
  "https://ai-bookkeeper-api-644842661403.us-central1.run.app" \
  "$WEB_URL"
```

---

## 🎯 RECOMMENDED PATH: VERCEL

**Why Vercel?**
1. **Fastest:** 5-10 minute deployment
2. **Free:** No cost for hobby/small projects
3. **Optimized:** Built specifically for Next.js
4. **Reliable:** Better uptime than Render free tier
5. **Performance:** Global CDN, edge functions
6. **Easy:** One command deployment

**Quick Start:**
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel login
vercel --prod

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL production
# Paste: https://ai-bookkeeper-api-644842661403.us-central1.run.app

# Update CORS (use URL from deploy output)
cat > tmp/env_vars.yaml << EOF
ALLOWED_ORIGINS: "https://app.ai-bookkeeper.app,https://<your-vercel-url>"
EOF

gcloud run services update ai-bookkeeper-api \
  --region us-central1 \
  --env-vars-file tmp/env_vars.yaml \
  --quiet

# Test
bash scripts/smoke_cutover.sh \
  "https://ai-bookkeeper-api-644842661403.us-central1.run.app" \
  "https://<your-vercel-url>"
```

---

## ⚡ IMMEDIATE ACTION

Choose your deployment option and follow the steps above. I recommend **Option 1 (Vercel)** for the fastest and most reliable deployment.

**After deployment:**
1. ✅ Note your frontend URL
2. ✅ Update CORS on API
3. ✅ Run smoke tests
4. ✅ Test in browser
5. ✅ Set up custom domain (optional)
6. 🚀 Launch Google Ads!

---

## 📞 NEED HELP?

If you choose Vercel and need automated deployment:
```bash
# I can create a deployment script for you
# Just let me know which option you prefer!
```

**You're 15 minutes away from having a fully deployed application ready for Google Ads!** 🚀
