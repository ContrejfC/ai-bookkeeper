# GPT Actions Notes

## Call Order & Dependencies

### 1. Discovery (First Call)
```
GET /actions
```
**Purpose:** Check system status, QBO connection, and billing plan
**Returns:** Links, paywall text, free caps, connection status

**Use this to:**
- Orient yourself at session start
- Check if QBO is connected
- Verify billing plan before posting
- Get paywall message for 402 responses

---

### 2. QuickBooks Connection
```
GET /auth/qbo/start
```
**Purpose:** Initiate OAuth2 flow for QuickBooks Online
**Returns:** Authorization URL for user to click

**Flow:**
1. User clicks the URL
2. Logs into QuickBooks
3. Grants permissions
4. Redirected back to callback
5. Token stored automatically

**Check connection status:**
```
GET /qbo/status
```

---

### 3. Billing Check (Before Posting)
```
GET /billing/status
```
**Purpose:** Verify entitlements and usage before commit
**Returns:** 
```json
{
  "active": true/false,
  "plan": "starter|pro|firm|none",
  "limits": {
    "tx_cap": 300,
    "bulk_approve": true/false
  },
  "usage": {
    "tx_analyzed": 45,
    "tx_posted": 120
  }
}
```

---

### 4. Propose Entries
```
POST /post/propose
```
**Purpose:** Analyze transactions and generate journal entry proposals
**Free Tier:** 50 calls/day per tenant (429 if exceeded)

**Request:**
```json
{
  "transactions": [
    {
      "id": "tx1",
      "date": "2025-10-16",
      "description": "OFFICE DEPOT",
      "amount": 150.00
    }
  ]
}
```

**Response:**
```json
{
  "proposals": [
    {
      "txn_id": "tx1",
      "confidence": 0.96,
      "reasoning": "Vendor pattern match",
      "je": { ... }
    }
  ]
}
```

---

### 5. Commit Entries
```
POST /post/commit
```
**Purpose:** Post approved entries to QuickBooks Online
**Requires:** Active subscription (Starter/Pro/Firm)

**Request:**
```json
{
  "approvals": [
    {
      "txn_id": "tx1",
      "je": {
        "txnDate": "2025-10-16",
        "refNumber": "AB-1001",
        "lines": [
          {"amount": 150.00, "postingType": "Debit", "accountRef": {"value": "46"}},
          {"amount": 150.00, "postingType": "Credit", "accountRef": {"value": "7"}}
        ]
      }
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "txn_id": "tx1",
      "qbo_doc_id": "123",
      "idempotent": false,
      "status": "posted"
    }
  ]
}
```

---

## Error Codes & Branching

### 402 ENTITLEMENT_REQUIRED
**When:** Trying to POST /post/commit without active subscription
**Response:**
```json
{
  "code": "ENTITLEMENT_REQUIRED",
  "message": "Activate a plan to post to QuickBooks.",
  "actions": ["/billing/portal"]
}
```

**GPT Action:**
1. Display `paywall_md` from GET /actions
2. Offer: "Start 14-day trial" → GET /billing/portal
3. Offer: "Continue free" → explain review-only mode

---

### 429 FREE_CAP_EXCEEDED
**When:** Exceeding 50 daily analyses on free tier
**Response:**
```json
{
  "code": "FREE_CAP_EXCEEDED",
  "message": "Free daily analysis cap (50) reached.",
  "actions": ["/billing/portal"]
}
```

**GPT Action:**
1. Explain daily cap reached
2. Offer upgrade via /billing/portal
3. Mention cap resets at midnight UTC

---

### 400/422 Validation Errors
**When:** Invalid request (unbalanced JE, missing fields, etc.)
**Response:**
```json
{
  "detail": "Debits must equal credits. Got debit=150.00, credit=140.00"
}
```

**GPT Action:**
1. Parse the error message
2. Explain the issue in plain language
3. Suggest corrections
4. Ask user to confirm fix

---

### 502/504 QuickBooks Upstream
**When:** QBO API is down or timeout
**Response:**
```json
{
  "code": "QBO_UPSTREAM",
  "message": "QuickBooks API temporarily unavailable."
}
```

**GPT Action:**
1. Apologize and explain it's a QBO issue
2. Suggest retrying in a few minutes
3. Don't retry automatically (user may have limited quota)

---

## Idempotency

**POST /post/commit** is idempotent:
- Identical JE payloads return existing `qbo_doc_id`
- Safe to retry on network failures
- Response includes `"idempotent": true` flag

**Hash computed on:**
- Transaction date
- Account refs (sorted)
- Amounts (rounded to 0.01)
- Line order (stable)

---

## Billing Portal

```
POST /billing/portal
```
**Purpose:** Generate Stripe Billing Portal URL
**Returns:**
```json
{
  "url": "https://billing.stripe.com/session/..."
}
```

**Use when:**
- User hits 402 and wants to subscribe
- User wants to manage subscription/payment
- User wants to upgrade/downgrade plan

---

## Tips for GPT Integration

1. **Always start with GET /actions** to check status
2. **Check billing before commit** to avoid 402 mid-flow
3. **Show confidence scores** from proposals to help user decide
4. **Explain reasoning** when user asks "why this account?"
5. **Batch approvals** when possible (user says "approve all >0.9")
6. **Handle errors gracefully** with clear user actions
7. **Celebrate successes** ("Posted 5 entries to QBO!")

