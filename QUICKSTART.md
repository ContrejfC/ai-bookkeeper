# 🚀 AI Bookkeeper - Quick Start Guide

## Project Successfully Built! ✅

**36 Python files created** across a complete AI bookkeeping system with:
- ✅ FastAPI backend with 15+ endpoints
- ✅ SQLite/PostgreSQL support with Alembic migrations
- ✅ CSV/OFX/PDF parsers
- ✅ Rules engine + Embeddings + LLM decisioning
- ✅ Reconciliation system
- ✅ Web UI for review/approval
- ✅ CSV exporters (ledger, trial balance, etc.)
- ✅ 11 passing unit tests
- ✅ 50-row sample dataset
- ✅ Complete documentation

## 30-Second Demo

```bash
cd ~/ai-bookkeeper

# 1. Seed sample data (50 transactions)
python3 scripts/seed_sample_data.py

# 2. Install FastAPI (if needed)
python3 -m pip install fastapi uvicorn -q

# 3. Start the server
uvicorn app.api.main:app --reload
```

Then open in browser:
- http://localhost:8000 - API documentation
- http://localhost:8000/docs - Interactive Swagger UI

## Complete Workflow

### Step 1: Start the Application

```bash
# Make sure you're in the project directory
cd ~/ai-bookkeeper

# Start the server
uvicorn app.api.main:app --reload
```

### Step 2: Propose Journal Entries

```bash
# In a new terminal, run the decisioning pipeline
curl -X POST http://localhost:8000/api/post/propose | jq
```

This will:
- Load all 50 transactions
- Match against rules (Amazon → Office Supplies, etc.)
- Check embeddings memory for similar vendors
- Use LLM (or fallback) to categorize
- Create balanced journal entries
- Flag entries needing review

### Step 3: Review in UI

Open: http://localhost:8000/ui/review

You'll see:
- All proposed journal entries
- Confidence scores and rationale
- Balance validation (must be balanced!)
- Color-coded status (proposed/approved/posted)
- Interactive approve/post buttons

### Step 4: Approve & Post

```bash
# Get the JE IDs from the UI or API
curl -X POST http://localhost:8000/api/post/approve \
  -H "Content-Type: application/json" \
  -d '{
    "je_ids": ["je_abc123"],
    "action": "post"
  }' | jq
```

### Step 5: Reconcile

```bash
# Match transactions to journal entries
curl -X POST http://localhost:8000/api/reconcile/run | jq

# View unmatched transactions
curl http://localhost:8000/api/reconcile/unmatched | jq
```

### Step 6: Export Reports

```bash
# Download reports
curl http://localhost:8000/api/export/journal-entries > journal_entries.csv
curl http://localhost:8000/api/export/trial-balance > trial_balance.csv
curl http://localhost:8000/api/export/general-ledger > general_ledger.csv

# Open in Excel/Numbers
open journal_entries.csv
```

## Running Tests

```bash
# Install test dependencies (if not already installed)
python3 -m pip install pytest pytest-asyncio

# Run all tests
python3 -m pytest tests/ -v

# Expected output: 11 passed ✅
```

## Sample API Calls

### Upload a New Bank Statement

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@tests/fixtures/sample_bank_statement.csv"
```

### Get Chart of Accounts

```bash
curl http://localhost:8000/api/chart-of-accounts | jq
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Configuration

Edit `.env` file:

```bash
cp .env.example .env

# Add your OpenAI API key
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# For PostgreSQL:
echo "DATABASE_URL=postgresql+psycopg://user:pass@localhost/aibookkeeper" >> .env
```

## Key Features Demonstrated

### 1. Tiered Decisioning
- **Rules**: Instant categorization for known patterns
- **Embeddings**: Learns from past categorizations
- **LLM**: Uses GPT-4 function calling for complex cases
- **Human**: Forces review for low confidence or large amounts

### 2. Balance Validation
All journal entries MUST balance (debits = credits). Unbalanced entries are:
- Automatically flagged `needs_review: true`
- Shown in red in the UI
- Cannot be posted until corrected

### 3. Sample Rules

From `app/rules/vendor_rules.yaml`:

```yaml
- pattern: "(?i)(amazon|amzn).*"
  account: "6100 Office Supplies"
  
- pattern: "(?i)(google ads|linkedin)"
  account: "7000 Advertising"
```

### 4. Reconciliation

Matches transactions to journal entries using:
- Exact: Same source_txn_id
- Heuristic: Same amount + date within ±3 days

## Project Structure Summary

```
ai-bookkeeper/
├── app/
│   ├── api/main.py              # FastAPI app (500+ lines)
│   ├── db/models.py             # SQLAlchemy + Pydantic models
│   ├── ingest/                  # CSV/OFX/PDF parsers
│   ├── rules/engine.py          # Rules-based categorization
│   ├── vendor_knowledge/        # Embeddings memory
│   ├── llm/categorize_post.py   # LLM wrapper
│   ├── recon/matcher.py         # Reconciliation
│   ├── exporters/csv_export.py  # CSV exporters
│   └── ui/                      # Web UI templates
├── tests/                       # 11 unit tests ✅
├── scripts/seed_sample_data.py  # Sample data loader
└── README.md                    # Full documentation
```

## Troubleshooting

### "No module named 'app'"

```bash
# Make sure you're in the project root
cd ~/ai-bookkeeper
export PYTHONPATH=$PWD:$PYTHONPATH
```

### "Database is locked"

```bash
# Close all other connections or use PostgreSQL
rm aibookkeeper.db
python3 scripts/seed_sample_data.py
```

### "OpenAI API error"

The system automatically falls back to simple heuristics if OpenAI fails:
- Revenue: debit Cash, credit Sales Revenue
- Expense: debit Expense account, credit Cash
- All fallback entries are flagged for review

## Next Steps

1. **Add your own bank statements**: Upload CSV/OFX files
2. **Customize rules**: Edit `app/rules/vendor_rules.yaml`
3. **Adjust thresholds**: Change confidence_threshold in `config/settings.py`
4. **Add accounts**: Extend CHART_OF_ACCOUNTS in `app/api/main.py`
5. **Deploy**: Use Postgres and deploy to cloud

## Sample Output

When you run `propose`, you'll see entries like:

```json
{
  "je_id": "je_abc123",
  "date": "2025-09-01",
  "lines": [
    {"account": "6100 Office Supplies", "debit": 45.23, "credit": 0.0},
    {"account": "1000 Cash at Bank", "debit": 0.0, "credit": 45.23}
  ],
  "confidence": 1.0,
  "needs_review": false,
  "memo": "Matched rule pattern: (?i)(amazon|amzn).*"
}
```

## Support

For issues or questions:
1. Check README.md for detailed docs
2. Review test files for examples
3. Check FastAPI docs at /docs endpoint

---

**Built and tested successfully! 🎉**

All 11 tests passing | 50 sample transactions loaded | Ready to use

