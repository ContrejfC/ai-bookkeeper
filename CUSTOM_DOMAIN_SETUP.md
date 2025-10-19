# Custom Domain Setup: api.ai-bookkeeper.app

## ✅ Status: GPT LIVE on ChatGPT Store
## 🌐 Custom Domain: https://api.ai-bookkeeper.app

---

## 🔧 Render Configuration Steps

### **Step 1: Add Custom Domain in Render Dashboard**

1. Go to **Render Dashboard** → **ai-bookkeeper-api** service
2. Click **Settings** → **Custom Domains**
3. Click **Add Custom Domain**
4. Enter: `api.ai-bookkeeper.app`
5. Render will provide you with DNS records to configure

### **Step 2: Configure DNS Records**

Render will give you one of these options:

**Option A: CNAME (Recommended)**
```
Type: CNAME
Name: api
Value: <your-service>.onrender.com
```

**Option B: A Record**
```
Type: A
Name: api
Value: <IP address from Render>
```

### **Step 3: Update Environment Variables**

Once DNS is configured, update these environment variables in Render:

```bash
# Render Dashboard > ai-bookkeeper-api > Environment
PUBLIC_BASE_URL=https://api.ai-bookkeeper.app
NEXT_PUBLIC_BASE_URL=https://api.ai-bookkeeper.app
NEXT_PUBLIC_API_URL=https://api.ai-bookkeeper.app
```

### **Step 4: Update GPT Actions Configuration**

1. Go to **ChatGPT GPT Builder** → Your AI Bookkeeper GPT
2. Click **Configure** → **Actions**
3. Update the OpenAPI URL to:
   ```
   https://api.ai-bookkeeper.app/openapi.gpt.json
   ```
4. **Save** and test

### **Step 5: Update Stripe Webhook URL**

1. Go to **Stripe Dashboard** → **Developers** → **Webhooks**
2. Update the endpoint URL to:
   ```
   https://api.ai-bookkeeper.app/api/billing/stripe_webhook
   ```
3. **Save** changes

### **Step 6: Update QuickBooks OAuth Redirect URI**

1. Go to **Intuit Developer Portal** → Your App
2. Update the Redirect URI to:
   ```
   https://api.ai-bookkeeper.app/api/auth/qbo/callback
   ```
3. Update environment variable in Render:
   ```
   QBO_REDIRECT_URI=https://api.ai-bookkeeper.app/api/auth/qbo/callback
   ```

---

## 🧪 Verification Commands

After DNS propagation (can take 5-60 minutes):

```bash
# Test DNS resolution
dig api.ai-bookkeeper.app

# Test HTTPS endpoint
curl -s https://api.ai-bookkeeper.app/healthz | jq

# Test OpenAPI endpoint
curl -s https://api.ai-bookkeeper.app/openapi.gpt.json | jq '.servers'

# Test with API Key
curl -s -H "Authorization: Bearer ak_test_FrTuGAPXp-vFmOGrHuT86snso_eCnhFmgTCTurQ4VcA" \
  https://api.ai-bookkeeper.app/actions | jq
```

Expected response from `.servers`:
```json
[
  {
    "url": "https://api.ai-bookkeeper.app",
    "description": "Production"
  }
]
```

---

## 📋 Checklist

- [ ] Add custom domain in Render Dashboard
- [ ] Configure DNS records (CNAME or A record)
- [ ] Wait for DNS propagation
- [ ] Update `PUBLIC_BASE_URL` in Render environment
- [ ] Update GPT Actions OpenAPI URL
- [ ] Update Stripe webhook URL
- [ ] Update QBO redirect URI
- [ ] Test all endpoints with new domain
- [ ] Verify SSL certificate is active

---

## 🎯 Current API Key

Your production API key (already configured in GPT):
```
ak_test_FrTuGAPXp-vFmOGrHuT86snso_eCnhFmgTCTurQ4VcA
```

---

## 🔒 SSL Certificate

Render automatically provisions SSL certificates for custom domains via Let's Encrypt. This happens automatically once DNS is configured correctly.

---

## 📊 Monitoring

After domain is live, monitor:
- GPT Actions calls in your logs
- Stripe webhook deliveries
- QBO OAuth flow success rate
- API response times

---

## 🎉 You're LIVE!

Once DNS propagates and all steps are complete:
- ✅ Professional domain: `api.ai-bookkeeper.app`
- ✅ GPT live on ChatGPT Store
- ✅ Stripe payments ready
- ✅ QBO integration ready
- ✅ API key authentication working

**Your AI Bookkeeper is now available to users worldwide!** 🌍

