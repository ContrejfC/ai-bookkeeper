# 🎯 NEXT ACTIONS - Revenue Readiness

**Status:** ✅ Ready to enable revenue  
**Time Required:** ~45 minutes  
**Blocking Items:** 0 (all configuration)

---

## 📋 AUDIT RESULTS

### ✅ Verified Components
- **Webhook Path:** `/api/billing/stripe_webhook` (canonical, no conflicts)
- **Scripts:** All 6 required scripts present and functional
- **OpenAPI:** Synced with live (drift corrected)
- **Database:** Using external PostgreSQL (no localhost refs)

### 📊 Key Findings
```
WEBHOOK_PATH=/api/billing/stripe_webhook
REQUIRED_ENV_VARS=22
SCRIPTS_VERIFIED=6/6
OPENAPI_STATUS=SYNCED
```

---

## 🚀 EXECUTE IN ORDER

### 1. SET RENDER ENVIRONMENT (15 min)

**In Render Dashboard → ai-bookkeeper-api → Environment:**

Add these 22 variables (get values from your providers):

**Core (4 vars):**
```bash
DATABASE_URL=postgresql://ai-bookkeeper_owner:PASSWORD@ep-XXX.neon.tech/ai-bookkeeper?sslmode=require
JWT_SECRET=<64-char-random-hex>
CSRF_SECRET=<64-char-random-hex>
ENVIRONMENT=production
```

**Stripe LIVE (10 vars - get from https://dashboard.stripe.com):**
```bash
STRIPE_SECRET_KEY=sk_live_XXXXXXXX
STRIPE_PUBLISHABLE_KEY=pk_live_XXXXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXX
STRIPE_PRODUCT_STARTER=prod_XXXXX
STRIPE_PRICE_STARTER=price_XXXXX
STRIPE_PRODUCT_PRO=prod_XXXXX
STRIPE_PRICE_PRO=price_XXXXX
STRIPE_PRODUCT_FIRM=prod_XXXXX
STRIPE_PRICE_FIRM=price_XXXXX
BILLING_RETURN_URL=https://ai-bookkeeper.onrender.com
```

**QBO Production (5 vars - get from https://developer.intuit.com):**
```bash
QBO_CLIENT_ID=ABxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
QBO_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
QBO_REDIRECT_URI=https://ai-bookkeeper.onrender.com/api/auth/qbo/callback
QBO_BASE=https://quickbooks.api.intuit.com
QBO_ENVIRONMENT=production
```

**Then:** Click "Save Changes" → Manual Deploy → Deploy latest commit (wait ~5 min)

---

### 2. CREATE STRIPE WEBHOOK (5 min)

**In Stripe Dashboard (LIVE mode):**

1. Developers → Webhooks → Add endpoint
2. **URL:** `https://ai-bookkeeper.onrender.com/api/billing/stripe_webhook`
3. **Events:** Select these 6:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
   - `customer.subscription.trial_will_end`
4. Copy the `whsec_...` signing secret
5. Go back to Render → Add `STRIPE_WEBHOOK_SECRET=whsec_...`
6. Redeploy if needed

**Verify:**
```bash
curl -X POST https://ai-bookkeeper.onrender.com/api/billing/stripe_webhook \
  -H "Content-Type: application/json" \
  -H "Stripe-Signature: test" \
  -d '{}'
# Expected: 400 (signature error) = webhook endpoint is reachable
```

---

### 3. CREATE API KEY LOCALLY (5 min)

```bash
# On your laptop
export DATABASE_URL="postgresql://ai-bookkeeper_owner:YOUR_PASSWORD@ep-XXX.neon.tech/ai-bookkeeper?sslmode=require"
cd /Users/fabiancontreras/ai-bookkeeper

python scripts/create_api_key.py --tenant prod_tenant_1 --name "Production GPT"
# Copy the ak_live_... token and save in password manager
```

**Test:**
```bash
curl -H "Authorization: Bearer ak_live_YOUR_TOKEN" \
  https://ai-bookkeeper.onrender.com/actions | jq
# Expected: {"version":"0.9.1","links":{...},"connected":{"qbo":false}}
```

---

### 4. RUN SMOKE TEST (5 min)

```bash
./ops/smoke_live.sh \
  --base-url https://ai-bookkeeper.onrender.com \
  --api-key ak_live_YOUR_TOKEN \
  --spec-version v1.0

# Expected output:
# ✅ PASS - All smoke tests passed
# Tests run: 7
# Tests passed: 7
```

---

### 5. CREATE GPT (10 min)

**In ChatGPT → Create GPT:**

1. **Name:** `AI Bookkeeper for QuickBooks`
2. **Instructions:** Paste from `gpt_config/instructions.txt`
3. **Actions:** Import `https://ai-bookkeeper.onrender.com/openapi.json`
4. **Auth:** API Key, Bearer, paste `ak_live_YOUR_TOKEN`
5. **Starters:** Add 5 from `gpt_config/starters.md`
6. **Privacy:** Set to Public (or "Anyone with link" for beta)

**Test in GPT:**
```
Show my system status
```
Expected: Calls `/actions`, shows plan=none, qbo=false

---

### 6. TEST REVENUE FLOW (5 min)

**In GPT:**
1. Say: `Post entry: Debit 46 $0.01, Credit 7 $0.01`
2. Expected: 402 error, shows paywall
3. Click billing portal link → Complete checkout with test card
4. Retry post → 200 OK, returns qbo_doc_id
5. Repeat same post → 200 OK, idempotent=true

---

## 📊 ENV VAR QUICK REFERENCE

| Category | Count | Source | Time to Get |
|----------|-------|--------|-------------|
| Core | 4 | Generate locally | 2 min |
| Stripe LIVE | 10 | Stripe Dashboard | 15 min |
| QBO Production | 5 | Intuit Portal | 10 min |
| **Total** | **22** | | **~27 min** |

---

## 🔍 VERIFICATION COMMANDS

```bash
# Health
curl https://ai-bookkeeper.onrender.com/healthz

# Actions (requires API key)
curl -H "Authorization: Bearer ak_live_XXX" \
  https://ai-bookkeeper.onrender.com/actions

# Billing (requires API key)
curl -H "Authorization: Bearer ak_live_XXX" \
  https://ai-bookkeeper.onrender.com/api/billing/status

# QBO OAuth (requires API key)
curl -H "Authorization: Bearer ak_live_XXX" \
  https://ai-bookkeeper.onrender.com/api/auth/qbo/start
```

All should return 200 OK (except webhook test which returns 400).

---

## 📂 FILES UPDATED

- ✅ `docs/openapi-latest.json` - Synced with live
- ✅ `REVENUE_READINESS_RUNSHEET.md` - Comprehensive guide (new)
- ✅ `NEXT_ACTIONS.md` - This file (new)

**No code changes required** - All tasks are configuration.

---

## ⏱️ TIME ESTIMATE

| Task | Time | Dependencies |
|------|------|--------------|
| 1. Set Render env vars | 15 min | Stripe/QBO credentials |
| 2. Create Stripe webhook | 5 min | Task 1 complete |
| 3. Create API key | 5 min | Local database access |
| 4. Smoke test | 5 min | Tasks 1-3 complete |
| 5. Create GPT | 10 min | ChatGPT Plus account |
| 6. Test revenue flow | 5 min | Stripe test card |
| **Total** | **45 min** | |

---

## 🎯 SUCCESS CRITERIA

- [ ] All 22 env vars set in Render
- [ ] Webhook responds (400 signature error is OK)
- [ ] API key created (starts with `ak_live_`)
- [ ] Smoke test passes (7/7)
- [ ] GPT created and calls `/actions` successfully
- [ ] Paywall shows on free tier
- [ ] Post works after subscription
- [ ] Idempotency verified

**When all checked:** 🎉 **REVENUE ENABLED** 🎉

---

**For full details, see:** `REVENUE_READINESS_RUNSHEET.md`

