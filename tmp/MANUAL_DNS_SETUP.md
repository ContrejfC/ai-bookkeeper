# Manual DNS Setup for api.ai-bookkeeper.app

## Cloudflare DNS Configuration

### Step 1: Access Cloudflare DNS
1. Go to: https://dash.cloudflare.com/
2. Select your domain: **ai-bookkeeper.app**
3. Click on **"DNS"** in the left sidebar

### Step 2: Add CNAME Record for API
1. Click **"Add record"**
2. Configure as follows:
   - **Type:** CNAME
   - **Name:** api
   - **Target:** ghs.googlehosted.com
   - **TTL:** Auto (or 300 seconds)
   - **Proxy status:** DNS only (gray cloud icon)
3. Click **"Save"**

### Step 3: Verify DNS Propagation
```bash
# Check DNS resolution (wait 5-10 minutes after creating record)
dig api.ai-bookkeeper.app

# Should show CNAME pointing to ghs.googlehosted.com
```

### Step 4: Wait for SSL Certificate
- Google Cloud Run will automatically provision an SSL certificate
- This takes 10-30 minutes after DNS propagates
- You can check status with:
  ```bash
  gcloud beta run domain-mappings describe api.ai-bookkeeper.app \
    --platform managed \
    --region us-central1
  ```

### Step 5: Update Frontend (After Certificate is Active)
Once the certificate is active and api.ai-bookkeeper.app is working:

1. Update NEXT_PUBLIC_API_URL in Render to:
   ```
   https://api.ai-bookkeeper.app
   ```

2. Update CORS on Cloud Run:
   ```bash
   # Create updated env file
   cat > tmp/env_vars_custom.yaml << ENVEOF
ALLOWED_ORIGINS: "https://app.ai-bookkeeper.app,https://ai-bookkeeper-web.onrender.com,https://api.ai-bookkeeper.app"
ENVEOF

   # Update Cloud Run
   gcloud run services update ai-bookkeeper-api \
     --region us-central1 \
     --env-vars-file tmp/env_vars_custom.yaml \
     --quiet
   ```

## Troubleshooting

### DNS Not Resolving
- Wait 5-10 minutes for propagation
- Verify Cloudflare proxy is disabled (gray cloud)
- Check that CNAME target is exactly: ghs.googlehosted.com

### Certificate Not Issuing
- Verify DNS is resolving correctly
- Ensure domain ownership is verified
- Check Cloud Run console for certificate status
- May take up to 30 minutes

### CORS Errors After Switching
- Verify ALLOWED_ORIGINS includes both the .onrender.com URL and custom domain
- Check that frontend NEXT_PUBLIC_API_URL matches exactly (no trailing slash)
- Clear browser cache and try again

---

**For now, continue using the direct Cloud Run URL until DNS and SSL are ready!**
