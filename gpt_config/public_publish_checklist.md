# 🤖 ChatGPT GPT - Public Publish Checklist

**GPT Name:** AI Bookkeeper for QuickBooks  
**Target:** Public GPT Store  
**Time Required:** ~30 minutes

---

## 📋 Prerequisites

Before starting, ensure you have:
- [ ] Production API key from `ops/.last_api_key.txt` (starts with `ak_live_`)
- [ ] Production URL: `https://ai-bookkeeper.onrender.com`
- [ ] All services deployed and passing health checks
- [ ] `ops/launch_live.sh` completed successfully

---

## 🎯 Step 1: Create/Edit GPT

### A. Access GPT Builder

1. Go to **ChatGPT** → **Explore GPTs**
2. Click **Create** (or edit existing GPT)
3. Select **Configure** tab

### B. Basic Information

**Name:**
```
AI Bookkeeper for QuickBooks
```

**Description:**
```
Automate your bookkeeping with AI-powered journal entry generation and direct posting to QuickBooks Online. Connect your books, review AI proposals, and post with confidence.
```

**Instructions:**
Copy from `gpt_config/instructions.txt` (entire file)

**Conversation Starters:**
Copy from `gpt_config/starters.md`:
```
1. "Check my billing status and QBO connection"
2. "Help me connect my QuickBooks account"
3. "Show me my current automation plan limits"
4. "What do I need to do to post journal entries?"
5. "Explain the free tier vs paid plans"
```

**Capabilities:**
- ☑ **Web Browsing** (Optional - for looking up accounting guidance)
- ☐ **DALL-E Image Generation** (Not needed)
- ☐ **Code Interpreter** (Not needed)

---

## 🔗 Step 2: Configure Actions

### A. Import OpenAPI Schema

1. In GPT Builder, click **Actions** tab
2. Click **Create new action**
3. **Import from URL:**
   ```
   https://ai-bookkeeper.onrender.com/openapi.json
   ```
4. Click **Import**
5. Wait for schema to load (should show ~50+ endpoints)

**Verify endpoints imported:**
- ✓ `GET /actions` (discovery)
- ✓ `GET /api/billing/status` (billing check)
- ✓ `POST /api/billing/portal_link` (upgrade link)
- ✓ `GET /api/auth/qbo/start` (QBO connect)
- ✓ `GET /api/qbo/status` (QBO status)
- ✓ `POST /api/qbo/journalentry` (posting)

### B. Configure Authentication

1. In Actions → **Authentication** section
2. Select: **API Key**
3. **Auth Type:** `Bearer`
4. **API Key:**
   ```
   Bearer ak_live_xxxxxxxxxxxxxxxxxxxxx
   ```
   *(Replace with your actual API key from `ops/.last_api_key.txt`)*

5. **Header Name:** `Authorization`

**⚠️ IMPORTANT:** The format must be exactly:
```
Bearer ak_live_xxxxxxxxxxxxxxxxxxxxx
```
(With "Bearer " prefix and space after)

### C. Verify Actions Configuration

**Test the Actions:**
1. In GPT Builder → **Actions** → **Test**
2. Try calling:
   ```
   GET /actions
   ```
3. Should return JSON with version, links, paywall info

**If test fails:**
- Check API key format (must include "Bearer " prefix)
- Verify API key is valid (check `ops/.last_api_key.txt`)
- Ensure services are running (check Render Dashboard)

---

## 🎨 Step 3: Branding & Settings

### A. Profile Picture

**Upload icon:**
- Use logo from `gpt_config/` directory (if available)
- Or create a simple icon representing bookkeeping + AI
- Recommended: 1024x1024 PNG with transparent background

### B. Additional Settings

**Category:** (Select most appropriate)
- **Productivity** or **Business**

**Example Prompts:** (Optional, in addition to starters)
- Already set in Conversation Starters above

---

## 🚀 Step 4: Publish to Public

### A. Toggle Public Access

1. In GPT Builder, click **Settings** (gear icon)
2. Find **"Who can access this GPT?"**
3. Select: **Anyone with the link** or **Public** (GPT Store)
4. Click **Update GPT** or **Publish**

### B. Review Publishing Requirements

**ChatGPT will check:**
- ✓ Name and description are set
- ✓ Instructions are provided
- ✓ Conversation starters are set
- ✓ Actions are configured (if applicable)

**If any checks fail:**
- Go back and complete missing sections
- Ensure all required fields are filled

### C. Accept Terms

- Read and accept GPT Builder terms
- Confirm you have rights to publish
- Click **Confirm** or **Publish**

---

## ✅ Step 5: Validation Tests

**Run these 3 prompts in your published GPT:**

### Test 1: Discovery & Status
```
Check my billing status and QBO connection
```

**Expected Response:**
- Shows current plan (free/starter/pro/firm)
- Shows QBO connection status (connected/not connected)
- Shows usage limits and current usage
- Offers link to billing portal if not subscribed

### Test 2: Connect QuickBooks
```
Help me connect my QuickBooks account
```

**Expected Response:**
- Provides OAuth link to connect QuickBooks
- Explains what permissions are needed
- Guides through authorization flow

### Test 3: Post Journal Entry (End-to-End)
```
I want to post a test journal entry:
- Date: today
- Debit: Meals & Entertainment ($150)
- Credit: Cash ($150)
```

**Expected Response (Free Tier):**
- Checks billing status
- Shows 402 ENTITLEMENT_REQUIRED if not subscribed
- Displays paywall message with upgrade options
- OR if subscribed: Posts to QBO and shows confirmation

**Expected Response (Paid Tier):**
- Checks QBO connection status
- Validates journal entry is balanced
- Posts to QuickBooks via idempotent endpoint
- Shows QBO document ID
- Indicates if it was duplicate (idempotent:true)

### Test 4: Idempotency Check
```
Post the same journal entry again
```

**Expected Response:**
- Recognizes duplicate payload
- Returns same QBO document ID
- Indicates idempotent:true
- Does not create duplicate entry in QuickBooks

---

## 🔍 Step 6: Monitor & Verify

### A. Check GPT Analytics

**In ChatGPT:**
- Go to **My GPTs** → Select your GPT
- Check **Analytics** (if available)
- Monitor usage, errors, ratings

### B. Monitor Backend Logs

**In Render Dashboard:**
- API Service → **Logs**
- Watch for:
  - `✅ GPT Actions discovery route loaded`
  - `✅ API key authentication middleware enabled`
  - Successful `/actions` calls
  - Successful `/api/billing/status` calls
  - Successful `/api/qbo/journalentry` posts

### C. Test from Different Accounts

- [ ] Test with your own ChatGPT account
- [ ] Test with a colleague's account (if available)
- [ ] Verify Actions work for all users
- [ ] Check paywall messages display correctly

---

## 🚨 Troubleshooting

### Issue: Actions Return "Unauthorized"

**Cause:** API key not set correctly

**Fix:**
1. Go to GPT Builder → **Actions** → **Authentication**
2. Verify format: `Bearer ak_live_xxxxxxxxxxxxxxxxxxxxx`
3. Ensure "Bearer " prefix with space
4. Update and save

### Issue: Actions Return "Not Found"

**Cause:** Service not deployed or wrong URL

**Fix:**
1. Check Render Dashboard → Services are "Live"
2. Verify OpenAPI URL: `https://ai-bookkeeper.onrender.com/openapi.json`
3. Test endpoints directly with curl
4. Reimport OpenAPI schema if needed

### Issue: Paywall Not Displaying

**Cause:** Billing endpoints not working

**Fix:**
1. Check `/api/billing/status` returns 200
2. Verify Stripe credentials are set in Render
3. Check middleware is enabled in logs
4. Test billing endpoint directly:
   ```bash
   curl -H "Authorization: Bearer ak_live_xxx" \
     https://ai-bookkeeper.onrender.com/api/billing/status
   ```

### Issue: QBO Connection Fails

**Cause:** OAuth redirect URI mismatch

**Fix:**
1. Verify redirect URI in Intuit Dashboard matches:
   `https://ai-bookkeeper.onrender.com/api/auth/qbo/callback`
2. Ensure QBO_BASE is production:
   `https://quickbooks.api.intuit.com`
3. Check QBO credentials are production (not sandbox)

---

## 📞 Support & Resources

**Documentation:**
- Full launch guide: `docs/GO_LIVE_NOW.md`
- GPT instructions: `gpt_config/instructions.txt`
- GPT starters: `gpt_config/starters.md`
- Actions notes: `gpt_config/actions_notes.md`

**Testing:**
- Smoke tests: `ops/smoke_live.sh`
- API key generation: `scripts/create_api_key.py`
- Environment verification: `scripts/verify_prod_env.py`

**Monitoring:**
- Render logs: Render Dashboard → API Service → Logs
- Health checks: `/healthz` on both services
- Actions discovery: `/actions` endpoint

---

## ✅ Launch Checklist

**Before marking complete, verify:**

- [ ] GPT is published and publicly accessible
- [ ] All 4 validation tests pass
- [ ] Actions authentication works
- [ ] Billing status check works
- [ ] QBO connection flow works
- [ ] Paywall messages display correctly
- [ ] End-to-end posting workflow succeeds
- [ ] Idempotency check confirms no duplicates
- [ ] GPT shows in GPT Store (if public)
- [ ] Monitoring shows no errors

---

**Publish Date:** _______________  
**Published By:** _______________  
**GPT URL:** _______________  
**Status:** ⬜ DRAFT | ⬜ TESTING | ⬜ PUBLIC
