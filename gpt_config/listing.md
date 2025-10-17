# GPT Listing Bundle - ChatGPT Store Submission

**Status:** Store-ready materials for ChatGPT GPT Store submission

---

## Basic Information

### Title
```
AI Bookkeeper for QuickBooks — Propose & Post Journal Entries
```

**Alternative (if trademark restricted):**
```
AI Bookkeeper — Automated Journal Entry Assistant
```

### Subtitle
```
Explainable JE proposals with confidence scores, then idempotent posting to QuickBooks Online.
```

### Category
**Business & Productivity**

### Tags/Keywords
```
QuickBooks, QBO, bookkeeping, journal entries, reconciliation, accounting automation, categorize transactions, small business, accounting software, QuickBooks Online
```

---

## Description (Store-Safe, 60-90 words)

**Version 1 (with QuickBooks):**
```
Automate journal entry creation for QuickBooks Online. Upload transactions, get AI-powered categorization proposals with confidence scores and detailed explanations. Review, approve, and post entries with one-click idempotent posting. Includes free tier (50 analyses/day) and paid plans for posting. Perfect for small businesses and accounting professionals who want to save time on data entry while maintaining full audit trails.
```

**Version 2 (brand-neutral, if trademark concerns):**
```
AI-powered bookkeeping assistant that analyzes transactions and proposes journal entries with confidence scores. Review detailed explanations, approve entries, and post them to your accounting software with idempotent safety. Includes free tier for analysis and paid plans for automated posting. Designed for small businesses and accounting professionals seeking efficient, explainable automation.
```

---

## Conversation Starters (3-5)

**From `gpt_config/starters.md`:**

1. **Connect my QuickBooks and propose entries for the last 7 days.**
2. **Propose entries from this CSV and explain your choices.**
3. **Approve the top 3 proposals over 0.93 confidence and post them.**
4. **Why did you map these transactions to Supplies? Show confidence and rule version.**
5. **Show my plan and what I can do without upgrading.**

---

## Screenshots (3 required)

### Screenshot 1: Connection & Discovery
**Filename:** `screenshot-1-discovery.png`

**Content:**
- User asks: "Check my system status"
- GPT displays: QBO connection status, billing plan, trial info
- Shows `/actions` response formatted nicely

**Annotations:**
- "Real-time connection status"
- "Free tier: 50 analyses/day"
- "14-day trial available"

### Screenshot 2: Proposal & Explanation
**Filename:** `screenshot-2-proposals.png`

**Content:**
- User uploads transactions or describes them
- GPT shows table of proposals:
  - Date | Vendor | Amount | Account | Confidence | Explanation
- User asks: "Why Office Supplies?"
- GPT explains: Vendor pattern match, rule version, historical accuracy

**Annotations:**
- "Confidence scores (0-1)"
- "Explainable reasoning"
- "Vendor pattern matching"

### Screenshot 3: Posting & Idempotency
**Filename:** `screenshot-3-posting.png`

**Content:**
- User: "Approve and post the top 3"
- GPT checks billing status (shows trial countdown)
- Posts to QuickBooks
- Shows: "✅ Posted 3 entries. QBO Doc IDs: 123, 124, 125"
- User repeats same request
- GPT: "Already posted (idempotent). QBO Doc IDs: 123, 124, 125"

**Annotations:**
- "One-click posting"
- "Idempotent safety (no duplicates)"
- "Real QuickBooks Doc IDs"

---

## Demo Video (60-90 seconds)

### Loom/Video Outline

**Script:**

1. **Intro (0-10s):**
   - "Hi, I'm the AI Bookkeeper for QuickBooks."
   - "I help you automate journal entries with confidence."

2. **Connect (10-20s):**
   - "First, let's connect your QuickBooks."
   - [Show OAuth click → QuickBooks login → Connect]
   - "✓ Connected to QuickBooks Sandbox"

3. **Propose (20-40s):**
   - "Now upload your transactions or describe them."
   - [Upload CSV or paste: "OFFICE DEPOT $150, UBER $45"]
   - "Here are my proposals with confidence scores..."
   - [Show table with vendor, account, confidence]

4. **Explain (40-50s):**
   - "You can ask why I chose any account."
   - [User: "Why Office Supplies?"]
   - "This vendor matches pattern OFFICE DEPOT (96% confidence)..."

5. **Post (50-70s):**
   - "Ready to post? I'll check your plan first."
   - [Shows: "Trial: 14 days left"]
   - "Posting... ✓ Posted 2 entries. QBO Doc IDs: 123, 124"

6. **Idempotency (70-85s):**
   - "If you post again, I'll detect duplicates."
   - [Repeat post → "Already posted (idempotent)"]

7. **Closing (85-90s):**
   - "Free tier: 50 analyses/day. Paid plans for posting."
   - "Start your 14-day trial!"

---

## Privacy & Legal Links

**Required for Store:**

### Privacy Policy
```
https://YOUR_DOMAIN/legal/privacy
```

**Must include:**
- Data collection practices (consent-based)
- Redaction strategy (SHA-256 with salts)
- QuickBooks OAuth token storage
- Stripe payment processing
- User rights (export, purge)

### Terms of Service
```
https://YOUR_DOMAIN/legal/terms
```

**Must include:**
- Subscription terms (trial, billing, cancellation)
- Usage limits (free tier, paid caps)
- QuickBooks integration terms
- Liability limitations
- Refund policy

### Data Processing Agreement (optional, enterprise)
```
https://YOUR_DOMAIN/legal/dpa
```

---

## Technical Configuration

### Actions Import

**OpenAPI URL:**
```
https://YOUR_PRODUCTION_DOMAIN/openapi.json
```

**Or versioned (stable):**
```
https://YOUR_PRODUCTION_DOMAIN/docs/openapi-v1.0.json
```

### Authentication

**Type:** API Key  
**Method:** Bearer  
**Header:** `Authorization`  
**Format:** `Bearer ak_live_xxxxxxxxxx...`

**How to get:**
```bash
python scripts/create_api_key.py --tenant YOUR_TENANT --name "ChatGPT GPT"
```

---

## Store Review Checklist

### Before Submission

- [ ] Privacy Policy live and accessible (no 404)
- [ ] Terms of Service live and accessible
- [ ] 3 high-quality screenshots (1280x720 or higher)
- [ ] Demo video (60-90s, Loom or YouTube unlisted)
- [ ] GPT tested end-to-end (connect → propose → post)
- [ ] No trademark violations in name/description
- [ ] No overclaims ("best," "only," "guaranteed")
- [ ] Free tier clearly explained
- [ ] Pricing visible and accurate

### During Review

- [ ] Respond to OpenAI reviewer questions within 48 hours
- [ ] Provide test account if requested
- [ ] Fix any compliance issues flagged
- [ ] Don't modify GPT during review (creates new review cycle)

### After Approval

- [ ] Set to "Public" (or "Anyone with a link" for soft launch)
- [ ] Share link on social media, email list
- [ ] Monitor reviews and feedback
- [ ] Update regularly (monthly or when major features added)

---

## Marketing Copy (Optional)

### One-Liner
```
Save 10+ hours/week on journal entries with AI-powered proposals and confidence-based automation.
```

### Value Props (for landing page/marketing)
- ✨ **Explainable AI** - See why every entry was categorized
- 🎯 **Confidence Scores** - Only post high-confidence entries automatically
- 🔒 **Idempotent** - Never duplicate entries, safe to retry
- 📊 **Audit Trails** - Full je_idempotency and consent logs
- 💰 **Free Tier** - 50 analyses/day, no credit card required
- ⚡ **14-Day Trial** - Test posting with real QuickBooks data

---

## Brand Guidelines

### Approved Phrases
- "AI-powered bookkeeping"
- "Automated journal entries"
- "QuickBooks Online integration" (factual reference)
- "Confidence-based proposals"
- "Idempotent posting"

### Avoid (Trademark/Legal Issues)
- "Official QuickBooks AI" (implies endorsement)
- "Intuit-powered" (not affiliated)
- "Only AI bookkeeper" (overclaim)
- "Guaranteed accuracy" (overclaim)
- "Replace your accountant" (misleading)

### Safe Branding
- "AI Bookkeeper for QuickBooks" (descriptive, factual)
- "Powered by GPT-4" (if using OpenAI models)
- "Works with QuickBooks Online" (factual compatibility)

---

## Asset Checklist

- [ ] `screenshot-1-discovery.png` (1280x720, PNG)
- [ ] `screenshot-2-proposals.png` (1280x720, PNG)
- [ ] `screenshot-3-posting.png` (1280x720, PNG)
- [ ] `demo-video.mp4` or Loom link (60-90s)
- [ ] `icon.png` (512x512, transparent background)
- [ ] Privacy Policy URL confirmed live
- [ ] Terms of Service URL confirmed live
- [ ] OpenAPI URL public and stable

---

## Submission Links

- **ChatGPT GPT Builder:** https://chatgpt.com/gpts/editor
- **OpenAI Platform:** https://platform.openai.com
- **GPT Store Guidelines:** https://help.openai.com/en/articles/8554397-gpt-store

---

## Post-Submission Monitoring

### Week 1
- Check review status daily
- Respond to reviewer questions
- Don't modify GPT (creates new review)

### After Approval
- Monitor usage analytics (if available)
- Read user reviews (reply within 24 hours)
- Track error rates (402/429 responses)
- Update instructions based on feedback

### Monthly
- Re-test all conversation starters
- Update screenshots if UI changed
- Refresh demo video if major features added
- Review and update description/tags

---

**Bundle Version:** 1.0  
**Last Updated:** 2025-10-17  
**Submission Status:** Ready for review

