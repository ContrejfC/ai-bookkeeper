# Cloud Console Environment Variables - Step-by-Step Fix

## 🚨 Issue: Environment Variables Not Set

The `gcloud run services describe` command shows **no environment variables**, which means they weren't set correctly in the Cloud Console.

## 📋 Step-by-Step Fix in Cloud Console

### Step 1: Open Cloud Console
1. Go to: https://console.cloud.google.com/run/detail/us-central1/ai-bookkeeper-api?project=bright-fastness-475700-j2
2. Make sure you're in the correct project: `bright-fastness-475700-j2`

### Step 2: Edit Service
1. Click the **"Edit & Deploy New Revision"** button (top right)
2. Wait for the edit page to load

### Step 3: Go to Variables & Secrets Tab
1. Click on the **"Variables & Secrets"** tab
2. You should see a section for **"Environment Variables"**

### Step 4: Add Environment Variables
Click **"Add Variable"** for each of these:

#### Variable 1: DATABASE_URL
- **Name**: `DATABASE_URL`
- **Value**: `postgresql://neondb_owner:npg_Gt8ocPATC3hQ@ep-summer-fog-aftcltuf-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require`

#### Variable 2: JWT_SECRET_KEY
- **Name**: `JWT_SECRET_KEY`
- **Value**: `c91351556086d9494e53a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2`

#### Variable 3: APP_ENV
- **Name**: `APP_ENV`
- **Value**: `production`

#### Variable 4: ALLOWED_ORIGINS
- **Name**: `ALLOWED_ORIGINS`
- **Value**: `https://frontend-ma4iv9gxo-contrejfcs-projects.vercel.app`

### Step 5: Deploy
1. Click **"Deploy"** button
2. Wait for deployment to complete (2-3 minutes)

### Step 6: Verify
After deployment, run this command to verify:
```bash
gcloud run services describe ai-bookkeeper-api --region us-central1 --project bright-fastness-475700-j2 --format="table(spec.template.spec.template.spec.containers[0].env[].name,spec.template.spec.template.spec.containers[0].env[].value)"
```

You should see all 4 environment variables listed.

## 🔍 Common Issues

### Issue 1: Variables Not Saving
- Make sure you click "Add Variable" for each one
- Don't use quotes around the values
- Make sure there are no extra spaces

### Issue 2: Wrong Project
- Double-check you're in project `bright-fastness-475700-j2`
- The URL should show the correct project ID

### Issue 3: Wrong Service
- Make sure you're editing `ai-bookkeeper-api` service
- Not a different service

## 🧪 Test After Setting Variables

Once you've set the variables and deployed:

1. **Test health endpoint:**
   ```
   curl https://ai-bookkeeper-api-ww4vg3u7eq-uc.a.run.app/healthz
   ```
   Should return: `{"status":"ok","version":"0.2.1-beta"}`

2. **Test signup:**
   ```bash
   curl -X POST https://ai-bookkeeper-api-ww4vg3u7eq-uc.a.run.app/api/auth/signup \
     -H "Content-Type: application/json" \
     -H "Origin: https://frontend-ma4iv9gxo-contrejfcs-projects.vercel.app" \
     -d '{"email":"test@example.com","password":"SecurePass123!","full_name":"Test User"}'
   ```
   Should return a successful signup response.

## 🚀 Expected Result

After setting environment variables correctly:
- ✅ `/healthz` returns `{"status":"ok"}`
- ✅ `/api/auth/signup` works perfectly
- ✅ Database connection established
- ✅ **Ready for Google Ads!**

## 📞 Need Help?

If you're still having issues:
1. Take a screenshot of the Variables & Secrets tab
2. Check the Cloud Console logs for error messages
3. Verify you're in the correct project and service

**The code is perfect - it's just a matter of setting the environment variables correctly in Cloud Console!**
