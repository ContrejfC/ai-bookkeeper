# 🚀 AI Bookkeeper - Beta Onboarding Guide

Welcome to the AI Bookkeeper closed beta! This guide will walk you through setting up your account and automating your bookkeeping.

---

## 📋 Quick Start Checklist

- [ ] Sign up and create your account
- [ ] Create your company profile
- [ ] Import chart of accounts (optional)
- [ ] Upload sample bank statement
- [ ] Map vendors to accounts
- [ ] Generate & approve journal entries
- [ ] Export to QuickBooks/Xero
- [ ] Review automation metrics

**Expected Time:** 20-30 minutes

---

## Step 1: Sign Up & Create Account

### Create Your Account

```bash
# Via API
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "secure_password",
    "full_name": "Your Name",
    "company_name": "Your Company LLC",
    "company_tax_id": "12-3456789"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "user_id": "user_abc123",
    "email": "your@email.com",
    "full_name": "Your Name"
  },
  "companies": [{
    "company_id": "company_xyz789",
    "company_name": "Your Company LLC",
    "role": "owner"
  }]
}
```

**Save your access token!** You'll need it for all subsequent API calls.

---

## Step 2: Set Up Authentication

### Store Your Token

```bash
# Store in environment variable
export TOKEN="your_access_token_here"

# Or create a .env file
echo "AUTH_TOKEN=$TOKEN" > .env.local
```

### Test Authentication

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## Step 3: Import Chart of Accounts (Optional)

### Option A: Use Default Chart

Skip this step to use the built-in chart of accounts.

### Option B: Import from QuickBooks

```bash
# Export your chart of accounts from QuickBooks as CSV
# Format: Account Number, Account Name, Account Type, Description

curl -X POST http://localhost:8000/api/import/quickbooks \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@chart_of_accounts.csv"
```

### Option C: Import from Xero

```bash
curl -X POST http://localhost:8000/api/import/xero \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@xero_chart_of_accounts.csv"
```

---

## Step 4: Upload Bank Statements

### Prepare Your Data

Download bank statements in one of these formats:
- **CSV** (preferred)
- **OFX** (from most banks)
- **PDF** (with OCR, experimental)

### Upload via API

```bash
curl -X POST http://localhost:8000/api/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@bank_statement_sept_2025.csv"
```

**Response:**
```json
{
  "message": "Uploaded and parsed 50 transactions",
  "transactions": [
    {
      "txn_id": "txn_abc123",
      "date": "2025-09-01",
      "amount": -45.23,
      "description": "AMZN Mktp US*2L3X4Y5Z",
      "counterparty": "Amazon"
    }
  ]
}
```

---

## Step 5: Generate Journal Entries

### Run AI Categorization

```bash
curl -X POST http://localhost:8000/api/post/propose \
  -H "Authorization: Bearer $TOKEN"
```

This will:
1. Match transactions against rules
2. Check embeddings for similar vendors
3. Use AI to categorize and create journal entries
4. Flag entries needing review

**Response:**
```json
{
  "message": "Proposed 50 journal entries",
  "proposed": [
    {
      "je_id": "je_xyz789",
      "date": "2025-09-01",
      "lines": [
        {"account": "6100 Office Supplies", "debit": 45.23, "credit": 0.0},
        {"account": "1000 Cash at Bank", "debit": 0.0, "credit": 45.23}
      ],
      "confidence": 1.0,
      "needs_review": false,
      "memo": "Matched rule pattern: (?i)(amazon|amzn).*"
    }
  ],
  "review_needed": 5
}
```

---

## Step 6: Review & Approve

### View in UI

Open: http://localhost:8000/ui/review

- ✅ Green cards = high confidence, ready to approve
- ⚠️ Yellow cards = needs review
- ❌ Red = unbalanced or error

### Approve via API

```bash
# Approve specific entries
curl -X POST http://localhost:8000/api/post/approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "je_ids": ["je_xyz789", "je_abc456"],
    "action": "approve"
  }'

# Post (finalize) entries
curl -X POST http://localhost:8000/api/post/approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "je_ids": ["je_xyz789"],
    "action": "post"
  }'
```

---

## Step 7: Run Reconciliation

### Automatic Reconciliation

```bash
curl -X POST http://localhost:8000/api/reconcile/run \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "statistics": {
    "total_transactions": 50,
    "total_journal_entries": 50,
    "matched": 47,
    "unmatched_transactions": 3,
    "orphaned_journal_entries": 0,
    "match_rate": 0.94
  }
}
```

### View Unmatched Items

```bash
curl http://localhost:8000/api/reconcile/unmatched \
  -H "Authorization: Bearer $TOKEN"
```

---

## Step 8: Export to QuickBooks/Xero

### Export to QuickBooks Desktop (IIF)

```bash
curl -X POST "http://localhost:8000/api/export/quickbooks?format=iif" \
  -H "Authorization: Bearer $TOKEN" \
  > quickbooks_export.iif
```

### Export to QuickBooks Online (CSV)

```bash
curl -X POST "http://localhost:8000/api/export/quickbooks?format=csv" \
  -H "Authorization: Bearer $TOKEN" \
  > quickbooks_export.csv
```

### Export to Xero

```bash
curl -X POST http://localhost:8000/api/export/xero \
  -H "Authorization: Bearer $TOKEN" \
  > xero_export.csv
```

### Import into QuickBooks

1. Open QuickBooks Desktop
2. Go to `File` → `Utilities` → `Import` → `IIF Files`
3. Select `quickbooks_export.iif`
4. Review and confirm

---

## Step 9: View Dashboard & Metrics

### Access Dashboard

Open: http://localhost:8000/ui/dashboard

You'll see:
- 🤖 Auto-approval rate (target: ≥80%)
- ✅ Reconciliation match rate (target: ≥90%)
- 👁️ Manual review rate (target: ≤20%)
- 📈 Transaction volume
- 📊 P&L overview
- 💰 Cash flow trend

### API Access

```bash
# Automation metrics
curl "http://localhost:8000/api/analytics/automation-metrics?company_id=$COMPANY_ID&days=30" \
  -H "Authorization: Bearer $TOKEN"

# P&L
curl "http://localhost:8000/api/analytics/pnl?company_id=$COMPANY_ID&start_date=2025-09-01&end_date=2025-09-30" \
  -H "Authorization: Bearer $TOKEN"

# Balance Sheet
curl "http://localhost:8000/api/analytics/balance-sheet?company_id=$COMPANY_ID&as_of_date=2025-09-30" \
  -H "Authorization: Bearer $TOKEN"

# Cash Flow
curl "http://localhost:8000/api/analytics/cashflow?company_id=$COMPANY_ID&start_date=2025-09-01&end_date=2025-09-30" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📊 Success Metrics Checklist

Track these metrics to measure automation success:

- [ ] **Auto-Approval Rate**: ≥80%
  - _What % of entries don't need review?_
  
- [ ] **Reconciliation Match Rate**: ≥90%
  - _What % of transactions match to journal entries?_
  
- [ ] **Manual Review Rate**: ≤20%
  - _What % require human intervention?_
  
- [ ] **Time Saved**: Track monthly
  - _How much time vs manual bookkeeping?_
  
- [ ] **Accuracy**: 95%+
  - _% of entries that don't need correction_

---

## 🐛 Troubleshooting

### Issue: "Company context required"

**Solution:** Your token expired or missing company_id. Refresh token:

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Authorization: Bearer $TOKEN"
```

### Issue: "Unbalanced journal entry"

**Solution:** This is intentional! The system won't let you post unbalanced entries. Review in UI and correct.

### Issue: Low auto-approval rate (<70%)

**Solutions:**
1. Add custom rules in `app/rules/vendor_rules.yaml`
2. Train the system by approving entries (builds embeddings)
3. Check vendor name consistency in bank data

### Issue: Reconciliation rate low (<80%)

**Solutions:**
1. Check date tolerance setting (default: ±3 days)
2. Verify amounts match exactly
3. Ensure all transactions have journal entries

---

## 💬 Feedback Collection

### Quick Feedback

Rate these aspects (1-5):

- [ ] **Ease of Setup**: ___/5
- [ ] **UI/UX**: ___/5
- [ ] **Categorization Accuracy**: ___/5
- [ ] **Speed**: ___/5
- [ ] **Overall Experience**: ___/5

### Detailed Feedback

Please share:

1. **What worked well?**
   
2. **What was confusing?**
   
3. **What features are missing?**
   
4. **Would you recommend this? (NPS 0-10)**

**Submit feedback:** beta-feedback@aibookkeeper.com

---

## 🆘 Support

### Documentation
- README.md - Full documentation
- API Docs: http://localhost:8000/docs

### Contact
- 📧 Email: support@aibookkeeper.com
- 💬 Slack: #beta-users
- 🐛 Issues: GitHub Issues

### Office Hours
- Tuesday & Thursday, 2-4pm PT
- Zoom link: [provided separately]

---

## 🎯 Next Steps

After completing onboarding:

1. **Week 1**: Process 1 month of transactions
2. **Week 2**: Export to QuickBooks and verify
3. **Week 3**: Set up recurring workflows
4. **Week 4**: Provide detailed feedback

### Advanced Features (Coming Soon)

- 📷 Receipt OCR and matching
- 📅 Automated month-end close
- 🔄 Real-time bank feeds (Plaid)
- 📊 Custom reports
- 👥 Multi-user collaboration

---

## 📝 Sample Data

Want to try before uploading real data?

```bash
# Seed demo company
python scripts/seed_demo_company.py

# This creates:
# - Demo company with 50 sample transactions
# - Pre-configured rules
# - Sample journal entries
```

---

## ✅ Beta Completion Checklist

- [ ] Onboarded successfully
- [ ] Processed 1+ month of statements
- [ ] Achieved >80% auto-approval rate
- [ ] Exported to accounting software
- [ ] Submitted feedback survey
- [ ] Participated in feedback call

**Thank you for being a beta tester! 🙏**

Your feedback is invaluable in making AI Bookkeeper better for everyone.

---

**Version:** 0.2.0-beta
**Last Updated:** October 9, 2025

