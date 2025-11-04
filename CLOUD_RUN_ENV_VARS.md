# Google Cloud Run Environment Variables

Copy and paste these into your Google Cloud Run service configuration.

## ✅ Already Configured
- `DATABASE_URL` = `postgresql://neondb_owner:npg_Gt8ocPATC3hQ(...` ✓

## 🔴 CRITICAL - Required for App to Work

### CORS & Security
```
ALLOWED_ORIGINS=https://ai-bookkeeper-nine.vercel.app,https://app.ai-bookkeeper.app
```

### JWT Authentication
```
JWT_SECRET=your-secret-key-minimum-32-characters-long-change-this
SECRET_KEY=your-secret-key-minimum-32-characters-long-change-this
```

### OpenAI API (for AI categorization)
```
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
LLM_MODEL=gpt-4o-mini
```

## 🟡 IMPORTANT - For Billing Features

### Stripe Configuration
```
STRIPE_SECRET_KEY=sk_test_YOUR_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE
```

### Stripe Price IDs (Starter Plan)
```
STRIPE_PRICE_STARTER_MONTHLY=price_YOUR_PRICE_ID
STRIPE_PRICE_TEAM_MONTHLY=price_YOUR_PRICE_ID
STRIPE_PRICE_FIRM_MONTHLY=price_YOUR_PRICE_ID
```

## 🟢 OPTIONAL - For Additional Features

### QuickBooks Integration
```
QBO_ENV=sandbox
QBO_CLIENT_ID_SANDBOX=YOUR_CLIENT_ID
QBO_CLIENT_SECRET_SANDBOX=YOUR_CLIENT_SECRET
QBO_REDIRECT_URI=https://ai-bookkeeper-api-ww4vg3u7eq-uc.a.run.app/api/qbo/oauth/callback
DEMO_MODE=true
```

### App URLs
```
APP_URL=https://ai-bookkeeper-nine.vercel.app
BACKEND_URL=https://ai-bookkeeper-api-ww4vg3u7eq-uc.a.run.app
FRONTEND_URL=https://ai-bookkeeper-nine.vercel.app
```

### Email (for notifications)
```
MAIL_PROVIDER=resend
RESEND_API_KEY=re_YOUR_KEY_HERE
FROM_EMAIL=noreply@ai-bookkeeper.app
```

### Other Settings
```
LOG_LEVEL=INFO
DEBUG=false
COOKIE_SECURE=true
COOKIE_SAMESITE=none
```

---

## 📝 How to Add These

### In Google Cloud Run:

1. **For each variable above:**
   - Click **"+ Add variable"**
   - Copy the **Name** (left side before `=`)
   - Copy the **Value** (right side after `=`)
   - Click outside the field to confirm

2. **Replace placeholder values:**
   - `your-secret-key-...` → Generate a random 32+ character string
   - `sk_proj_YOUR_KEY_HERE` → Your actual OpenAI API key
   - `sk_test_YOUR_KEY_HERE` → Your actual Stripe test key
   - `price_YOUR_PRICE_ID` → Your actual Stripe price IDs

3. **After adding all variables:**
   - Scroll to bottom
   - Click **"DEPLOY"** button
   - Wait ~2-3 minutes for deployment

---

## 🔑 Where to Get API Keys

### OpenAI API Key
1. Go to: https://platform.openai.com/api-keys
2. Click **"Create new secret key"**
3. Copy the key (starts with `sk-proj-`)

### Stripe Keys
1. Go to: https://dashboard.stripe.com/test/apikeys
2. Copy **Secret key** (starts with `sk_test_`)
3. Copy **Publishable key** (starts with `pk_test_`)

### Generate JWT Secret
```bash
# Run this command to generate a secure random key:
openssl rand -hex 32
```

Or use an online generator: https://randomkeygen.com/

---

## 🚨 Minimum Required to Fix Current Error

To fix the "Error loading access information" immediately, you MUST add these 3:

```
ALLOWED_ORIGINS=https://ai-bookkeeper-nine.vercel.app,https://app.ai-bookkeeper.app
JWT_SECRET=your-secret-key-minimum-32-characters-long
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
```

The rest can be added later as you enable those features.

