# Deploy Split Services - Quick Start

**ETA**: 30-45 minutes  
**Result**: Full working app with API + Web frontend

---

## 🚀 **Step-by-Step (Follow Exactly)**

### **Step 1: Go to Render Blueprints** (2 minutes)

1. Open: https://dashboard.render.com/blueprints
2. Click: **New Blueprint Instance**
3. Select repo: `ContrejfC/ai-bookkeeper`
4. **Blueprint file**: Select `render-split.yaml` from dropdown
5. Click: **Apply**

Render will create 3 resources:
- ✅ `ai-bookkeeper-api` (Web Service)
- ✅ `ai-bookkeeper-web` (Web Service)  
- ✅ `ai-bookkeeper-db` (PostgreSQL)

---

### **Step 2: Add Secrets to API Service** (5 minutes)

Go to: Dashboard → **ai-bookkeeper-api** → **Environment**

**Add these secrets** (click "Add Environment Variable"):

```bash
# Generate with: openssl rand -hex 32
JWT_SECRET=<paste_32_char_hex>
CSRF_SECRET=<paste_32_char_hex>

# From your existing Neon.tech database OR use Render DB
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require

# Stripe (get from Stripe Dashboard)
STRIPE_SECRET_KEY=sk_live_YOUR_KEY
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET
STRIPE_PRICE_STARTER=price_YOUR_ID
STRIPE_PRICE_PRO=price_YOUR_ID
STRIPE_PRICE_FIRM=price_YOUR_ID

# QuickBooks (get from developer.intuit.com)
QBO_CLIENT_ID=YOUR_ID
QBO_CLIENT_SECRET=YOUR_SECRET
```

Click: **Save Changes**

---

### **Step 3: Mark Build-Time Variables for Web Service** (2 minutes)

Go to: Dashboard → **ai-bookkeeper-web** → **Environment**

For **EACH** of these variables:
1. Find `NEXT_PUBLIC_API_URL`
2. Click the **⚙️ icon** on the right
3. Check: ☑️ **"Available during build"**
4. Repeat for `NEXT_PUBLIC_BASE_URL`

Click: **Save Changes** (this triggers a rebuild)

---

### **Step 4: Wait for Deployment** (5-10 minutes)

Watch in Render Dashboard:
- `ai-bookkeeper-api`: Building... → Live ✅
- `ai-bookkeeper-web`: Building... → Live ✅
- `ai-bookkeeper-db`: Available ✅

---

### **Step 5: Test API Service** (2 minutes)

```bash
# Health check
curl https://ai-bookkeeper-api.onrender.com/healthz

# Expected: {"status":"ok",...}

# API docs
open https://ai-bookkeeper-api.onrender.com/docs

# Expected: Swagger UI page loads

# GPT Actions spec
curl https://ai-bookkeeper-api.onrender.com/openapi.gpt.json | jq '.servers'

# Expected: [{"url":"https://api.ai-bookkeeper.app",...}]
```

---

### **Step 6: Test Web Service** (2 minutes)

```bash
# Home page
open https://ai-bookkeeper-web.onrender.com/

# Expected: Next.js React app loads (NOT static HTML)

# Dashboard
open https://ai-bookkeeper-web.onrender.com/dashboard

# Expected: Dashboard page or redirect to /login

# Check browser console
# Expected: No CORS errors, no 404s
```

---

### **Step 7: Configure Custom Domains** (10 minutes + DNS wait)

#### **For API** (`api.ai-bookkeeper.app`):

**In Render**:
1. Dashboard → **ai-bookkeeper-api** → **Settings** → **Custom Domains**
2. Click: **Add Custom Domain**
3. Enter: `api.ai-bookkeeper.app`

**At your domain registrar**:
```
Type: CNAME
Name: api
Value: ai-bookkeeper-api.onrender.com
```

#### **For Web** (`app.ai-bookkeeper.app`):

**In Render**:
1. Dashboard → **ai-bookkeeper-web** → **Settings** → **Custom Domains**
2. Click: **Add Custom Domain**
3. Enter: `app.ai-bookkeeper.app`

**At your domain registrar**:
```
Type: CNAME
Name: app
Value: ai-bookkeeper-web.onrender.com
```

Wait 5-60 minutes for DNS propagation + SSL certificate.

---

### **Step 8: Update External Services** (5 minutes)

Once custom domains are working:

**Update GPT Actions**:
- Go to: ChatGPT GPT Builder → Configure → Actions
- Change URL to: `https://api.ai-bookkeeper.app/openapi.gpt.json`

**Update Stripe Webhook**:
- Go to: Stripe Dashboard → Developers → Webhooks
- Change URL to: `https://api.ai-bookkeeper.app/api/billing/stripe_webhook`

**Update QuickBooks**:
- Go to: Intuit Developer Portal → Your App
- Change Redirect URI to: `https://api.ai-bookkeeper.app/api/auth/qbo/callback`
- Update `QBO_REDIRECT_URI` in Render env vars

---

## ✅ **Done When**

- [x] Both services show "Live" in Render
- [x] API health check returns 200 OK
- [x] Web home page shows Next.js React app
- [x] Can access `/dashboard`, `/login`, `/transactions`
- [x] Browser console has no errors
- [x] API calls from frontend work
- [x] GPT Actions still functional
- [x] Custom domains working (after DNS)
- [x] SSL certificates valid

---

## 🎯 **Success**!

Once all checkmarks are complete:
- ✅ **Your entire Next.js app is accessible**
- ✅ **Users can sign up and use the dashboard**
- ✅ **Revenue-ready** (paywall, billing, QBO posting)
- ✅ **GPT Store integration** working
- ✅ **Professional architecture** that won't break
- ✅ **Fixed once and for all** 🎉

---

## 🆘 **If Something Goes Wrong**

**See full guide**: `SPLIT_SERVICES_DEPLOYMENT_GUIDE.md`

**Common issues**:
1. **Blueprint not found**: Select `render-split.yaml` manually
2. **Build fails**: Check Dockerfile paths are correct
3. **CORS errors**: Update `CORS_ALLOWED_ORIGINS` in API service
4. **Next.js build fails**: Ensure `NEXT_PUBLIC_*` vars marked "Available during build"
5. **Database connection fails**: Check `DATABASE_URL` format

**Get help**: Paste error logs and I'll diagnose immediately.

---

**Ready? Go to https://dashboard.render.com/blueprints and start!** 🚀

