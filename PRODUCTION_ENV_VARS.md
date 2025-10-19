# Production Environment Variables
## Domain: https://api.ai-bookkeeper.app

Copy these to **Render Dashboard** → **ai-bookkeeper-api** → **Environment**

---

## 🌐 Core Application Settings

```bash
PUBLIC_BASE_URL=https://api.ai-bookkeeper.app
NEXT_PUBLIC_BASE_URL=https://api.ai-bookkeeper.app
NEXT_PUBLIC_API_URL=https://api.ai-bookkeeper.app
```

---

## 🗄️ Database

```bash
# Your Neon.tech or Render PostgreSQL connection string
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
PGSSLMODE=require
```

---

## 🔒 Security

```bash
# Generate with: openssl rand -hex 32
JWT_SECRET=your_jwt_secret_here
CSRF_SECRET=your_csrf_secret_here
```

---

## 💳 Stripe LIVE Mode

```bash
STRIPE_SECRET_KEY=sk_live_YOUR_LIVE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_LIVE_PUBLISHABLE_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET

# Product/Price IDs (create with scripts/stripe_bootstrap.py)
STRIPE_PRODUCT_STARTER=prod_YOUR_STARTER_PRODUCT_ID
STRIPE_PRICE_STARTER=price_YOUR_STARTER_PRICE_ID
STRIPE_PRODUCT_PRO=prod_YOUR_PRO_PRODUCT_ID
STRIPE_PRICE_PRO=price_YOUR_PRO_PRICE_ID
STRIPE_PRODUCT_FIRM=prod_YOUR_FIRM_PRODUCT_ID
STRIPE_PRICE_FIRM=price_YOUR_FIRM_PRICE_ID

# Return URL after checkout
BILLING_RETURN_URL=https://api.ai-bookkeeper.app
```

**Webhook URL** (configure in Stripe Dashboard):
```
https://api.ai-bookkeeper.app/api/billing/stripe_webhook
```

---

## 📊 QuickBooks Online - Production

```bash
QBO_CLIENT_ID=your_production_client_id
QBO_CLIENT_SECRET=your_production_client_secret
QBO_REDIRECT_URI=https://api.ai-bookkeeper.app/api/auth/qbo/callback
QBO_BASE=https://quickbooks.api.intuit.com
QBO_ENVIRONMENT=production
```

---

## ⚙️ API Configuration

```bash
PORT=10000
```

---

## 📝 Optional: Logging & Monitoring

```bash
LOG_LEVEL=INFO
SENTRY_DSN=your_sentry_dsn_if_using
```

---

## 🔄 After Updating

1. **Save** all environment variables in Render
2. **Redeploy** the service (Render will auto-redeploy)
3. Wait 2-3 minutes for deployment
4. Test with: `curl https://api.ai-bookkeeper.app/healthz`

