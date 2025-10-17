# 🤖 AI Bookkeeper - Production Ready

An AI-powered bookkeeping system that ingests bank statements and produces double-entry journal entries with human review, plus Stripe billing, QuickBooks integration, and ChatGPT GPT Actions.

**Status:** ✅ **Ready to Deploy** | **Tests:** 74/74 passing | **Docs:** 17 guides

## 🚀 Quick Start

**Deploy to Render in 10 minutes:**

```bash
# 1. Pre-flight check
./ops/pre_deploy_check.sh

# 2. Deploy
# Follow DEPLOY_NOW.md for one-page quick reference
# Or docs/RENDER_DEPLOY_QUICKSTART.md for full guide

# 3. Verify
./ops/smoke_live.sh --base-url https://your-web-service.onrender.com
```

**See:** `DEPLOY_NOW.md` | `PRODUCTION_READY.md` | `docs/RENDER_DEPLOY_QUICKSTART.md`

## Features

- **Multi-format Ingestion**: Parse CSV, OFX, and PDF bank statements
- **Tiered Decisioning**: Rules → Embeddings Memory → LLM → Human Review
- **Double-Entry Validation**: All journal entries must balance (hard fail for unbalanced)
- **Reconciliation**: Deterministic matching of transactions to journal entries
- **Web UI**: Simple review interface for approving/posting entries
- **CSV Export**: Export to CSV for ledger, reconciliation, trial balance
- **Vector Memory**: Learn from historical categorizations using embeddings

## Architecture

```
Bank Statement (CSV/OFX/PDF)
    ↓
Parser → Normalized Transactions
    ↓
Decisioning Pipeline:
  1. Rules Engine (regex patterns)
  2. Embeddings Memory (similar vendors)
  3. LLM Function Calling (GPT-4)
  4. Human Review (confidence < 0.85 or large amounts)
    ↓
Proposed Journal Entries (must balance)
    ↓
Review UI → Approve → Post
    ↓
Reconciliation → Match to Transactions
    ↓
Export (CSV, Trial Balance, P&L, BS)
```

## Tech Stack

- **Backend**: Python 3.11, FastAPI
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Migrations**: Alembic
- **Vector Store**: ChromaDB (with FAISS fallback)
- **LLM**: OpenAI GPT-4 (function calling)
- **OCR**: Tesseract (optional, for PDFs)
- **Frontend**: FastAPI + Jinja2 templates
- **Tests**: pytest

## Quick Start

### Prerequisites

- Python 3.11+
- pip or uv

### Installation

```bash
# Clone or navigate to project directory
cd ai-bookkeeper

# Install dependencies
pip install -e .
# OR with uv:
# uv pip install -e .

# Create .env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# For local dev, SQLite is used by default
```

### Setup Database

```bash
# Run migrations (creates tables)
alembic upgrade head

# OR if alembic command not found:
python -m alembic upgrade head
```

### Seed Sample Data

```bash
# Load sample transactions from fixtures
python scripts/seed_sample_data.py
```

### Run the Application

```bash
# Start the FastAPI server
uvicorn app.api.main:app --reload

# Server runs at http://localhost:8000
```

## Usage Guide

### 1. Upload Bank Statement

```bash
# Upload a CSV file
curl -X POST http://localhost:8000/api/upload \
  -F "file=@tests/fixtures/sample_bank_statement.csv"
```

### 2. Generate Proposed Journal Entries

```bash
# Run the decisioning pipeline
curl -X POST http://localhost:8000/api/post/propose
```

This will:
- Match transactions against rules (vendor patterns)
- Check embeddings memory for similar vendors
- Use LLM to categorize and create journal entries
- Flag entries needing review (low confidence, large amounts, unbalanced)

### 3. Review in UI

Open http://localhost:8000/ui/review in your browser to:
- See all proposed journal entries
- View confidence scores and rationale
- Check for unbalanced entries
- Approve or post entries

### 4. Approve/Post Entries (API)

```bash
# Approve entries
curl -X POST http://localhost:8000/api/post/approve \
  -H "Content-Type: application/json" \
  -d '{"je_ids": ["je_abc123", "je_def456"], "action": "approve"}'

# Post entries (final)
curl -X POST http://localhost:8000/api/post/approve \
  -H "Content-Type: application/json" \
  -d '{"je_ids": ["je_abc123"], "action": "post"}'
```

### 5. Run Reconciliation

```bash
# Match transactions to journal entries
curl -X POST http://localhost:8000/api/reconcile/run

# View unmatched transactions
curl http://localhost:8000/api/reconcile/unmatched
```

### 6. Export Reports

```bash
# Export journal entries
curl http://localhost:8000/api/export/journal-entries > journal_entries.csv

# Export reconciliation results
curl http://localhost:8000/api/export/reconciliation > reconciliation.csv

# Export general ledger
curl http://localhost:8000/api/export/general-ledger > general_ledger.csv

# Export trial balance
curl http://localhost:8000/api/export/trial-balance > trial_balance.csv
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| POST | `/api/upload` | Upload bank statement (CSV/OFX/PDF) |
| POST | `/api/post/propose` | Generate proposed journal entries |
| POST | `/api/post/approve` | Approve or post journal entries |
| POST | `/api/reconcile/run` | Run reconciliation |
| GET | `/api/reconcile/unmatched` | Get unmatched transactions |
| GET | `/api/chart-of-accounts` | Get chart of accounts |
| GET | `/api/export/journal-entries` | Export JEs to CSV |
| GET | `/api/export/reconciliation` | Export reconciliation to CSV |
| GET | `/api/export/general-ledger` | Export GL to CSV |
| GET | `/api/export/trial-balance` | Export trial balance to CSV |
| GET | `/ui/review` | Review page (web UI) |
| GET | `/health` | Health check |

## Configuration

Edit `.env` file:

```bash
APP_ENV=dev
DATABASE_URL=sqlite:///./aibookkeeper.db
VECTOR_BACKEND=chroma
OPENAI_API_KEY=your_key_here
```

### Advanced Settings

In `config/settings.py`:

- `confidence_threshold`: Minimum confidence to avoid review (default 0.85)
- `recon_date_tolerance_days`: Days tolerance for reconciliation (default 3)
- `large_amount_threshold`: Amount threshold for auto-review (default $5000)

## Chart of Accounts

The MVP uses a simple CoA (see `app/api/main.py`):

**Assets:**
- 1000 Cash at Bank

**Liabilities:**
- 2000 Credit Card Payable
- 2100 Taxes Payable

**Expenses:**
- 6100 Office Supplies
- 6150 Computer Equipment
- 6200 Utilities
- 6300 Software Subscriptions
- 6500 Travel & Transport
- 6600 Shipping & Freight
- 6700 Contract Labor
- 6800 Insurance
- 6900 Rent Expense
- 6999 Miscellaneous Expense
- 7000 Advertising

**Revenue:**
- 8000 Sales Revenue
- 8100 Payroll Income

## Rules Engine

Vendor categorization rules are in `app/rules/vendor_rules.yaml`. Example:

```yaml
rules:
  - pattern: "(?i)(amazon|amzn).*"
    account: "6100 Office Supplies"
    category: "office_supplies"
  
  - pattern: "(?i)(google ads|linkedin)"
    account: "7000 Advertising"
    category: "advertising"
```

## LLM Integration

The system uses OpenAI's function calling with this system prompt:

> You are an accounting assistant. Follow U.S. GAAP and double-entry.
> Return ONLY valid JSON for the function call. Use the provided Chart of Accounts.
> If uncertain, set "needs_review": true and explain briefly in "rationale".
> Ensure journal entries are balanced; otherwise force review.

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_posting.py

# Run with verbose output
pytest -v
```

### Test Coverage

- `test_posting.py`: Journal entry balance validation
- `test_recon.py`: Reconciliation matching logic
- `test_csv_parser.py`: CSV parsing and counterparty extraction

## Project Structure

```
ai-bookkeeper/
├── app/
│   ├── api/
│   │   └── main.py              # FastAPI application
│   ├── db/
│   │   ├── models.py            # SQLAlchemy & Pydantic models
│   │   ├── session.py           # Database session management
│   │   └── migrations/          # Alembic migrations
│   ├── ingest/
│   │   ├── csv_parser.py        # CSV parser
│   │   ├── ofx_parser.py        # OFX parser
│   │   └── pdf_bank_parser.py   # PDF parser with OCR
│   ├── ocr/
│   │   └── extract_text.py      # Tesseract OCR wrapper
│   ├── rules/
│   │   ├── engine.py            # Rules engine
│   │   └── vendor_rules.yaml    # Vendor categorization rules
│   ├── vendor_knowledge/
│   │   └── embeddings.py        # Embeddings-based memory
│   ├── llm/
│   │   ├── prompts.py           # LLM prompts
│   │   └── categorize_post.py   # LLM categorization
│   ├── recon/
│   │   └── matcher.py           # Reconciliation matcher
│   ├── exporters/
│   │   └── csv_export.py        # CSV export functions
│   └── ui/
│       ├── templates/
│       │   └── review.html      # Review page template
│       └── static/
│           └── styles.css       # CSS styles
├── config/
│   └── settings.py              # Application settings
├── scripts/
│   └── seed_sample_data.py      # Sample data loader
├── tests/
│   ├── fixtures/
│   │   └── sample_bank_statement.csv
│   ├── test_posting.py
│   ├── test_recon.py
│   └── test_csv_parser.py
├── .env.example
├── alembic.ini
├── pyproject.toml
└── README.md
```

## Decisioning Pipeline Details

### 1. Rules Engine
- Regex pattern matching on description/counterparty
- Instant categorization for known vendors
- 100% confidence when matched

### 2. Embeddings Memory
- Finds similar past categorizations using semantic search
- ChromaDB with sentence transformers
- Provides historical context to LLM

### 3. LLM Categorization
- OpenAI GPT-4 with function calling
- Given transaction + CoA + historical mappings
- Returns account, journal entry, confidence, rationale

### 4. Human Review Triggers
- Confidence < 0.85
- Amount > $5,000
- Unbalanced journal entry
- LLM sets `needs_review: true`

## Balance Validation

**Hard Fail**: All journal entries MUST balance (debits = credits within $0.01).

If unbalanced:
- Entry is flagged `needs_review: true`
- Warning shown in UI
- Cannot be posted until corrected

## Reconciliation

Matches transactions to journal entries using:

1. **Exact Match**: Same txn_id and same date
2. **Heuristic Match**: Same amount, date within ±3 days
3. **Flags**: Unmatched transactions and orphaned JEs

## Export Formats

All exports are CSV:

- **Journal Entries**: JE ID, Date, Account, Debit, Credit, Status, Memo
- **Reconciliation**: Txn ID, JE ID, Match Type, Score
- **General Ledger**: Date, JE ID, Account, Debit, Credit, Memo
- **Trial Balance**: Account, Total Debits, Total Credits, Balance

## Troubleshooting

### ChromaDB Issues

If ChromaDB fails to initialize:
```bash
# System falls back to in-memory FAISS automatically
# To fix, reinstall:
pip install --upgrade chromadb
```

### OpenAI API Errors

If LLM calls fail:
- Check `.env` has valid `OPENAI_API_KEY`
- System falls back to simple heuristics (expense vs revenue)
- All fallback entries are flagged for review

### Database Locked (SQLite)

If you see "database is locked":
- Close all other connections
- Or switch to PostgreSQL:
  ```bash
  DATABASE_URL=postgresql+psycopg://user:pass@localhost/aibookkeeper
  ```

## Future Enhancements

- QuickBooks CSV export
- PostgreSQL with pgvector
- Multi-currency support
- P&L and Balance Sheet reports
- PDF statement template detection
- Bank reconciliation workflow
- Multi-company support
- Role-based access control

## License

MIT License - see LICENSE file

## Contributing

PRs welcome! Please:
1. Add tests for new features
2. Ensure `pytest` passes
3. Follow existing code style
4. Update README if adding endpoints/features

---

**Built with ❤️ for bookkeepers everywhere**


---

## 🚀 Sprint 3.1 — Production-Ready Features

### Quick Start (Local Development)

```bash
# 1. Fresh database setup
rm -f aibookkeeper.db
python3 -c "from app.db.session import engine; from app.db.models import Base; Base.metadata.create_all(bind=engine)"

# 2. Generate 5 simulated companies
python3 scripts/simulate_companies.py

# 3. Run ingestion pipeline (1,702 transactions in ~8 seconds)
python3 scripts/run_simulation_ingest.py

# 4. Generate reports
python3 scripts/generate_pilot_report.py
python3 scripts/generate_feedback_dataset.py

# 5. View results
cat reports/pilot_metrics.md
head -10 data/feedback/training.csv
```

### Staging Deployment

```bash
# Using Docker Compose with PostgreSQL
docker-compose -f deploy/staging_postgres.yml up -d

# Run migrations
docker-compose exec app alembic upgrade head

# Verify health
curl http://localhost/healthz
```

### Load Testing

```bash
# Install Locust
pip3 install locust

# Run performance tests
locust -f tests/performance/locustfile.py \
    --host http://localhost:8000 \
    --users 50 --spawn-rate 10 --run-time 5m \
    --headless --html reports/load_test_$(date +%Y%m%d).html
```

### Security Scanning

```bash
# Static analysis with Bandit
bandit -r app -f json -o reports/bandit_results.json

# Dynamic scan with OWASP ZAP
docker run -t owasp/zap2docker-stable zap-baseline.py \
    -t http://localhost:8000 \
    -r reports/zap_baseline.html
```

### Sprint 3.1 Highlights

- ✅ **UUID-based IDs:** 0 collisions in 10,000 tests
- ✅ **Per-file Error Isolation:** Robust rollback mechanism
- ✅ **Security:** 0 high-severity issues, OWASP Top 10 compliant
- ✅ **Performance:** 67.8 RPS, p95 < 500ms for reads
- ✅ **Training Dataset:** 1,702 records for ML model training
- ✅ **Auto-Approval Rate:** 61.6% average (target: 80%)

### Documentation

- `SPRINT_3.1_COMPLETE.md` - Full sprint report (596 lines)
- `reports/pilot_metrics.md` - Performance metrics for 5 companies
- `reports/load_test.md` - Locust performance results
- `reports/security_baseline.md` - Security scan results

