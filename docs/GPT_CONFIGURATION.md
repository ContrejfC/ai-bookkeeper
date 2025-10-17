# GPT Configuration Guide

**AI Bookkeeper for QuickBooks - ChatGPT GPT Setup**

This guide walks through creating a custom ChatGPT GPT that integrates with the AI Bookkeeper API using GPT Actions.

---

## Prerequisites

1. **ChatGPT Plus or Enterprise** (required for custom GPTs)
2. **API deployment** running at a public URL (e.g., Render)
3. **Tenant ID** for your organization

---

## Step 1: Create API Key

First, generate an API key for your GPT to authenticate:

```bash
python scripts/create_api_key.py --tenant YOUR_TENANT_ID --name "ChatGPT GPT"
```

**Output:**
```
======================================================================
  🔑 API KEY (SAVE THIS - SHOWN ONCE ONLY)
======================================================================

  ak_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

======================================================================
```

⚠️ **Copy this key immediately** - it will not be shown again.

---

## Step 2: Create GPT in ChatGPT

1. Go to [ChatGPT](https://chatgpt.com)
2. Click **Explore GPTs** (left sidebar)
3. Click **Create** (top right)
4. Click **Configure** tab

---

## Step 3: Basic Configuration

### Name
```
AI Bookkeeper for QuickBooks
```

### Description
```
Automate QuickBooks journal entries with AI-powered transaction analysis, proposals, and posting. Connect your QuickBooks, analyze transactions, and post entries with confidence.
```

### Instructions

Copy the contents from:
```
gpt_config/instructions.txt
```

Or use this:

```
[Paste the full contents of instructions.txt here]
```

### Conversation Starters

Add these (from `gpt_config/starters.md`):

1. **Connect my QuickBooks and propose entries for the last 7 days.**
2. **Propose entries from this CSV and explain your choices.**
3. **Approve the top 3 proposals over 0.93 confidence and post them.**
4. **Why did you map these transactions to Supplies? Show confidence and rule version.**
5. **Show my plan and what I can do without upgrading.**

### Knowledge

Leave empty (API-driven, no static files needed)

### Capabilities

- [x] **Web Browsing** - OFF
- [x] **DALL·E Image Generation** - OFF
- [x] **Code Interpreter** - OFF

---

## Step 4: Configure Actions

### Import OpenAPI Schema

1. In the **Configure** tab, scroll to **Actions**
2. Click **Create new action**
3. Click **Import from URL**
4. Enter your API's OpenAPI URL:

**Production:**
```
https://YOUR-DOMAIN/openapi.json
```

**Render:**
```
https://ai-bookkeeper.onrender.com/openapi.json
```

**Local Testing:**
```
http://localhost:8000/openapi.json
```

5. Click **Import**

ChatGPT will automatically parse all endpoints and schemas.

---

### Configure Authentication

1. Still in **Actions**, click **Authentication**
2. Select: **API Key**
3. Configure:
   - **Auth Type:** `Bearer`
   - **API Key:** Paste the key from Step 1 (`ak_live_...`)
   - **Custom Header Name:** `Authorization` (default)

4. Click **Save**

---

### Test Connection

1. In Actions, click **Test** next to any action (e.g., `GET /actions`)
2. Verify you see a successful response with status 200
3. Check the response includes your tenant's connection status

---

## Step 5: Privacy Settings

### For Private Pilot (Recommended)
- **Privacy:** Only me
- **Usage:** Your personal testing

### For Closed Beta
- **Privacy:** Anyone with a link
- Generate and share the link with pilot users

### For Public Launch
- **Privacy:** Public
- Add to GPT Store (requires OpenAI review)

---

## Step 6: Test the GPT

### Initial Discovery Test

In the GPT chat:
```
Check my system status
```

Expected response:
- GPT calls `GET /actions`
- Shows your plan, QBO connection status, free cap info

### QuickBooks Connection Test

```
Connect my QuickBooks
```

Expected flow:
1. GPT calls `GET /qbo/status` → sees not connected
2. GPT calls `GET /auth/qbo/start` → gets OAuth URL
3. GPT displays clickable link
4. You click → OAuth flow → callback
5. GPT confirms connection

### Proposal Test

```
Analyze this transaction: "OFFICE DEPOT - 2025-10-16 - $150.00"
```

Expected flow:
1. GPT calls `POST /post/propose`
2. Returns confidence score, account mapping, reasoning
3. Asks if you want to approve and post

### Posting Test (Requires Subscription)

```
Approve and post that entry
```

Expected flow:
1. GPT calls `GET /billing/status` → checks entitlement
2. If inactive → shows paywall, offers trial link
3. If active → calls `POST /post/commit` → posts to QBO
4. Returns QBO Doc ID and success message

---

## Troubleshooting

### GPT says "API authentication failed"

**Cause:** API key invalid or revoked

**Fix:**
1. Generate new key: `python scripts/create_api_key.py --tenant TENANT_ID`
2. Update in GPT Actions → Authentication
3. Click Save

---

### GPT can't access `/actions` endpoint

**Cause:** OpenAPI schema not imported or endpoint missing

**Fix:**
1. Verify endpoint works: `curl https://YOUR-DOMAIN/actions`
2. Re-import OpenAPI schema in Actions
3. Ensure Actions are enabled (toggle switch)

---

### GPT shows 402 error when posting

**Cause:** No active subscription

**Expected behavior!** GPT should:
1. Display paywall message
2. Offer billing portal link
3. Suggest "continue free" path

**Fix (if you want to post):**
1. Click the billing portal link
2. Complete Stripe checkout
3. Return and say "retry post"

---

### GPT can't connect to QuickBooks

**Cause:** OAuth flow not completed or tokens expired

**Fix:**
1. Say "reconnect my QuickBooks"
2. GPT will provide fresh OAuth URL
3. Complete the flow
4. Verify: "check my QBO status"

---

## Advanced Configuration

### Custom Domain (Production)

1. Set up custom domain in Render (e.g., `api.yourdomain.com`)
2. Update OpenAPI URL in GPT Actions
3. Update `BILLING_RETURN_URL` environment variable
4. Update QBO OAuth redirect URIs in Intuit Developer Portal

### Multiple Environments

Create separate GPTs for each environment:

- **AI Bookkeeper (Dev)** → `http://localhost:8000`
- **AI Bookkeeper (Staging)** → `https://staging.onrender.com`
- **AI Bookkeeper (Prod)** → `https://api.yourdomain.com`

Each uses a different API key tied to a test tenant.

### Rate Limiting

GPT Actions respect:
- **Free tier:** 50 analyses/day (429 if exceeded)
- **Paid tier:** Subscription-based post caps (402 if over limit)

GPT will automatically explain these errors and offer upgrades.

---

## Maintenance

### Rotating API Keys

To rotate keys (recommended every 90 days):

1. Generate new key:
   ```bash
   python scripts/create_api_key.py --tenant TENANT_ID --name "GPT Q4 2025"
   ```

2. Update in GPT Actions → Authentication

3. Test connection

4. Revoke old key:
   ```bash
   python scripts/revoke_api_key.py --token OLD_TOKEN
   ```

### Updating OpenAPI Schema

When you add new endpoints:

1. Export latest OpenAPI:
   ```bash
   curl https://YOUR-DOMAIN/openapi.json > docs/openapi-latest.json
   ```

2. In GPT Actions → Click action → Edit schema
3. Re-import from URL
4. Verify new endpoints appear

### Monitoring Usage

Check tenant usage:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://YOUR-DOMAIN/billing/status
```

Response includes:
- `tx_analyzed` - Total analyses this month
- `tx_posted` - Total posts this month
- `plan` - Current subscription tier

---

## Security Best Practices

1. **Never commit API keys** to git
2. **Use environment-specific keys** (test vs live)
3. **Rotate keys regularly** (every 90 days)
4. **Revoke compromised keys immediately**
5. **Monitor API logs** for suspicious activity
6. **Use HTTPS only** (no HTTP in production)
7. **Set restrictive CORS** if needed

---

## Support

- **Technical Issues:** Check `docs/QBO_RUNBOOK.md` and `docs/BILLING_RUNBOOK.md`
- **API Docs:** `https://YOUR-DOMAIN/docs` (FastAPI auto-generated)
- **Test Endpoints:** Use `ops/smoke_commit.sh` for manual testing

---

## Next Steps

1. ✅ Complete this setup
2. Test all conversation starters
3. Connect real QuickBooks Sandbox
4. Run pilot with 3-5 users
5. Collect feedback on GPT prompts/responses
6. Iterate on instructions and starters
7. Launch to broader beta
8. Consider GPT Store submission (public)

---

## Example Workflows

### Daily Reconciliation

User:
> "Connect QBO and propose entries for yesterday"

GPT:
1. Checks connection (`/qbo/status`)
2. If connected, prompts for transaction source
3. Analyzes transactions (`/post/propose`)
4. Shows proposals with confidence scores
5. Asks for approval
6. Posts approved entries (`/post/commit`)
7. Confirms QBO Doc IDs

### Bulk Approval

User:
> "Approve all proposals over 0.95 confidence and post"

GPT:
1. Filters proposals by confidence
2. Checks billing status
3. Posts batch to `/post/commit`
4. Reports success/failures per item

### Explain Reasoning

User:
> "Why did you map 'AMAZON' to Office Supplies?"

GPT:
1. Retrieves proposal reasoning from prior response
2. Explains: vendor pattern, rule version, historical accuracy
3. Offers to adjust if needed

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-17  
**API Version:** 0.9.1

