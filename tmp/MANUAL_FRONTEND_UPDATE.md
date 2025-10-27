# Manual Frontend Update Instructions

Since RENDER_API_KEY is not set, follow these manual steps:

## Step 1: Access Render Dashboard
1. Go to: https://dashboard.render.com/
2. Log in to your account

## Step 2: Find Your Web Service
1. Look for service named: **ai-bookkeeper-web**
2. Click on the service name

## Step 3: Update Environment Variable
1. Click on the **"Environment"** tab in the left sidebar
2. Find the environment variable: **NEXT_PUBLIC_API_URL**
3. Click **"Edit"** next to it
4. Update the value to:
   ```
   https://ai-bookkeeper-api-644842661403.us-central1.run.app
   ```
5. Click **"Save Changes"**

## Step 4: Deploy
1. The service should automatically start deploying
2. If not, click **"Manual Deploy"** → **"Deploy latest commit"**
3. Wait for deployment to complete (usually 3-5 minutes)

## Step 5: Verify
1. Once deployed, note the service URL (e.g., https://ai-bookkeeper-web.onrender.com)
2. Open the URL in your browser
3. Check browser console (F12) for any CORS or API errors
4. Try logging in or signing up to test API connectivity

## Troubleshooting
- If you see CORS errors: verify the API URL is exactly correct (no trailing slash)
- If deploy fails: check the deploy logs in Render dashboard
- If API calls fail: verify the Cloud Run API is accessible at the URL above

---

**After completing these steps, save the web URL and run smoke tests!**
