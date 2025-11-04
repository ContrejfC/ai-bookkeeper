# Reader Training & Evaluation Suite

## Overview

The AI-Bookkeeper reader training suite provides **synthetic training assets**, **standards-based parsers**, and a **comprehensive evaluation harness** to ensure the ingestion pipeline correctly handles diverse bank statement formats.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    READER TRAINING SUITE                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Standards Parsers          2. CSV Templates & Fuzzers   │
│     • CAMT.053/054                • QBO 3-col/4-col         │
│     • MT940                       • Xero templates          │
│     • BAI2                        • Locale variants         │
│     • OFX                         • Sign conventions        │
│                                                               │
│  3. Synthetic PDF Generator    4. Evaluation Harness        │
│     • Checking statements         • Roundtrip tests         │
│     • Credit card statements      • Reconciliation          │
│     • Account analysis            • Confidence scoring      │
│     • Noise/scan simulation       • Error taxonomy          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
            ┌──────────────────────────────┐
            │   Ingestion Pipeline         │
            │   (Existing)                 │
            └──────────────────────────────┘
                            ↓
            ┌──────────────────────────────┐
            │   Evaluation Report          │
            │   • Pass/Fail by dataset     │
            │   • Reconciliation rate      │
            │   • Confidence distribution  │
            │   • Error taxonomy coverage  │
            └──────────────────────────────┘
```

## Components

### 1. Standards Parsers

Located in `app/ingestion/standards/`, these parsers handle international banking formats:

#### CAMT (ISO 20022)

**File:** `camt_parser.py`

- Formats: camt.053 (bank statement), camt.054 (debit/credit notification)
- Handles XML namespaces, multiple accounts, ISO currency codes
- Extracts: booking date, value date, amount, debtor/creditor, references

**Fixture:** `tests/fixtures/standards/camt053_min.xml`

#### MT940 (SWIFT)

**File:** `mt940_parser.py`

- Tagged field format (`:XX:` tags)
- Key tags: `:20:` (reference), `:25:` (account), `:60F:` (opening), `:61:` (transaction), `:62F:` (closing)
- Handles multi-line descriptions (`:86:` tags)

**Fixture:** `tests/fixtures/standards/mt940_min.txt`

#### BAI2 (Cash Management)

**File:** `bai2_parser.py`

- Segment-based format (01/02/03/16/49/98/99 records)
- Used by US banks for account analysis
- Handles type codes (credit/debit), availability

**Fixture:** `tests/fixtures/standards/bai2_min.txt`

#### OFX (Open Financial Exchange)

**File:** `ofx_parser.py`

- Both SGML and XML variants
- Extracts: FITID, DTPOSTED, TRNAMT, NAME, MEMO
- Maps to canonical transaction schema

**Fixture:** `tests/fixtures/standards/ofx_min.ofx`

### 2. CSV Templates & Fuzzers

#### Templates

Located in `app/ingestion/csv_templates/`:

- **qbo_3col.csv**: QuickBooks 3-column (Date, Description, Amount)
- **qbo_4col.csv**: QuickBooks 4-column (Date, Description, Debit, Credit)
- **xero_template.csv**: Xero format (Date, Amount, Payee, Description, Reference)

#### Fuzzer

**File:** `app/ingestion/csv_fuzz/fuzz_csv.py`

Generates locale variants to stress-test CSV normalization:

- **Delimiters**: comma, semicolon, tab, pipe
- **Decimals**: period vs comma (123.45 vs 123,45)
- **Thousands**: comma, period, space, apostrophe
- **Negative signs**: `-123.45`, `(123.45)`, `123.45 CR`, `123.45-`
- **Dates**: MDY, DMY, YMD, various separators
- **Encodings**: UTF-8, Latin-1, Windows-1252

**Usage:**
```bash
python -m app.ingestion.csv_fuzz.fuzz_csv \
  --in app/ingestion/csv_templates/qbo_4col.csv \
  --out tests/fixtures/csv/locale_variants \
  --variants 12
```

**Output:** 12 CSV files with different locale conventions, all representing the same transactions.

### 3. Synthetic PDF Generator

**Location:** `scripts/synth_statements/`

Uses ReportLab to generate realistic bank statement PDFs from YAML style definitions.

#### Generator

**File:** `generator.py`

Features:
- Multi-page rendering
- Header token placement (account numbers, dates, balances)
- Tabular transaction data with proper alignment
- Running balance calculations
- Credit/debit markers
- Page rotation and noise simulation (scan artifacts)

#### Style Definitions

**Files:** `scripts/synth_statements/styles/*.yaml`

1. **checking.yaml**: Personal checking account
   - Header: account number, period, beginning/ending balance
   - Columns: Date, Description, Amount, Balance
   - Debit-negative convention

2. **credit_card.yaml**: Credit card statement
   - Header: card number (masked), due date, minimum payment
   - Columns: Date, Merchant, Amount
   - All amounts positive (purchases vs payments)

3. **account_analysis.yaml**: Business account analysis
   - Header: account number, analysis period, fees summary
   - Columns: Date, Description, Debit, Credit, Balance
   - Separate debit/credit columns

#### Usage

```python
from scripts.synth_statements.generator import generate_statement

generate_statement(
    style_path="scripts/synth_statements/styles/checking.yaml",
    output_path="tests/fixtures/pdf_synth/checking_001.pdf",
    num_rows=50,
    num_pages=3,
    add_noise=True
)
```

### 4. Reader Evaluation Harness

**Location:** `ops/reader_eval/`

Runs all fixtures through the ingestion pipeline and produces a scored report.

#### Configuration

**File:** `config.yaml`

```yaml
datasets:
  - name: camt053_min
    kind: camt
    path: tests/fixtures/standards/camt053_min.xml
    expected_rows: 10
    expected_currency: EUR
  
  - name: qbo_3col
    kind: csv
    path: app/ingestion/csv_templates/qbo_3col.csv
    expected_rows: 10
    expected_currency: USD
  
  - name: pdf_checking_synth
    kind: pdf_synth
    style: scripts/synth_statements/styles/checking.yaml
    rows: 50
    pages: 3
```

#### Evaluation Runner

**File:** `run_eval.py`

Process:
1. Load config and dataset manifest
2. For each dataset:
   - Feed file to ingestion pipeline (in-proc or HTTP)
   - Capture output: rows, errors, warnings
   - Validate:
     - **Row count**: actual vs expected (±10%)
     - **Date parsing**: 100% success required
     - **Currency detection**: matches expected
     - **Reconciliation**: opening + net transactions ≈ closing (±$0.01)
     - **Duplicates**: dedup rate < 5%
     - **Confidence**: median ≥ 0.85, needs_review ≤ 15%
     - **Error taxonomy**: proper error codes for invalid inputs
3. Compute per-dataset score (0.0-1.0)
4. Write `report.json` with metrics

**Usage:**
```bash
python ops/reader_eval/run_eval.py \
  --config ops/reader_eval/config.yaml \
  --out out/reader_eval
```

**Output:** `out/reader_eval/<timestamp>/report.json`

#### Report Schema

**File:** `report_schema.json`

```json
{
  "timestamp": "2025-10-30T12:00:00",
  "summary": {
    "datasets": 15,
    "pass": 14,
    "fail": 1,
    "skip": 0
  },
  "metrics": {
    "reconcile_pass_rate": 0.98,
    "date_parse_rate": 1.00,
    "currency_detect_rate": 1.00,
    "low_conf_fraction": 0.12,
    "dedup_rate": 0.98
  },
  "datasets": [
    {
      "name": "camt053_min",
      "kind": "camt",
      "files": 1,
      "score": 0.95,
      "checks": {
        "reconcile": true,
        "dates": true,
        "currency": true,
        "confidence": true,
        "dedup": true
      },
      "details": {
        "rows_expected": 10,
        "rows_actual": 10,
        "reconcile_error_cents": 0,
        "median_confidence": 0.92
      }
    }
  ]
}
```

#### Report Renderer

**File:** `report_render.py`

Converts `report.json` to Markdown summary:

```bash
python ops/reader_eval/report_render.py \
  out/reader_eval/*/report.json > out/reader_eval/*/report.md
```

**Output:** Human-readable Markdown with pass/fail badges, metric charts, and per-dataset details.

### 5. Launch-Checks Integration

**File:** `ops/launch_checks/check_reader_eval.py`

Optional pre-deployment gate that runs a subset of the evaluation harness.

**Configuration:** `ops/launch_checks/config.yaml`

```yaml
checks:
  reader_eval:
    enabled: false  # Toggle on when ready
    datasets:
      - camt053_min
      - mt940_min
      - ofx_min
      - qbo_3col
      - pdf_checking_synth
    min_pass_rate: 0.95
```

**Behavior:**
- If `enabled: false`, check returns `SKIP`
- If enabled, runs evaluation on specified datasets
- Returns `PASS` if pass rate ≥ min_pass_rate
- Returns `FAIL` otherwise, with details in launch-checks report

## Data Safety

### No Real Bank Data

**All fixtures are synthetic or based on public standards.**

- Standards fixtures (CAMT, MT940, BAI2, OFX): minimal examples with fake account numbers, names, and amounts
- CSV templates: generated data with generic descriptions
- PDF synthetics: created programmatically with placeholder data

### Crawler Outputs

The web crawler (separate component) stores **features only**, not PDFs:

- Layout geometry (header positions, table bands)
- Header tokens (redacted)
- Column types (date, amount, balance)
- Sample rows (PII-redacted, hashed descriptions)

**No raw PDFs are committed to git.**

### .gitignore Rules

```gitignore
# Generated assets
tests/fixtures/pdf_synth/*.pdf
tests/fixtures/csv/locale_variants/*.csv
out/reader_eval/

# Never commit real statements
tests/fixtures/pdf/_real/
tests/fixtures/pdf/_public/
```

## Testing Strategy

### Test Files

Located in `tests/reader/`:

1. **test_standards_roundtrip.py**
   - Parse each standard fixture to canonical rows
   - Verify reconciliation passes
   - Check currency and sign conventions

2. **test_csv_normalization_fuzz.py**
   - Generate locale variants with fuzzer
   - Ingest all variants
   - Verify consistent canonical output

3. **test_pdf_synthetic_roundtrip.py**
   - Generate PDFs for each style
   - Parse via text → layout → OCR fallback paths
   - Verify stable row counts and header detection

4. **test_reconciliation_and_signs.py**
   - Adversarial test cases (off-by-one-cent, flipped signs)
   - Expect `needs_review` flag
   - Verify reconciliation failure detection

5. **test_confidence_thresholds.py**
   - Verify extractor path weights
   - Check needs_review cutoff at 0.85
   - Test confidence scoring consistency

6. **test_error_taxonomy_surface.py**
   - Password-protected PDF → proper error code
   - Oversized file → proper error code
   - Nested ZIP → proper error code
   - Verify hints and evidence in errors

### Running Tests

```bash
# All reader tests
pytest tests/reader/ -v

# Specific test file
pytest tests/reader/test_standards_roundtrip.py -v

# Generate CSV fuzz variants first
python -m app.ingestion.csv_fuzz.fuzz_csv \
  --in app/ingestion/csv_templates/qbo_4col.csv \
  --out tests/fixtures/csv/locale_variants

# Then run fuzz tests
pytest tests/reader/test_csv_normalization_fuzz.py -v
```

## CI/CD Integration

### GitHub Actions

**File:** `.github/workflows/reader-eval.yml`

Triggers:
- **Manual:** `workflow_dispatch`
- **Scheduled:** Weekly on Sundays at 2 AM UTC

Steps:
1. Setup Python 3.11
2. Install dependencies (pytest, reportlab, pdfplumber, lxml, pyyaml)
3. Generate CSV fuzz variants
4. Generate synthetic PDFs
5. Run all reader tests (`pytest tests/reader/`)
6. Run evaluation harness (`ops/reader_eval/run_eval.py`)
7. Render report Markdown
8. Upload artifacts:
   - `report.json`
   - `report.md`
   - Test results

### Performance Targets

- **Local test run**: ≤ 3 minutes
- **CI full suite**: ≤ 5 minutes
- **Evaluation harness**: ≤ 2 minutes (15 datasets)

## Metrics & Scoring

### Per-Dataset Score

Score = average of check results (0 or 1 each):

```
score = (
    reconcile_pass +
    date_parse_pass +
    currency_detect_pass +
    confidence_pass +
    dedup_pass
) / 5.0
```

### Overall Metrics

- **Reconcile Pass Rate**: % of datasets with reconciliation within ±$0.01
- **Date Parse Rate**: % of rows with successfully parsed dates
- **Currency Detect Rate**: % of datasets with correct currency
- **Low Conf Fraction**: % of rows with confidence < 0.85
- **Dedup Rate**: % of duplicate transactions correctly identified

### Pass/Fail Criteria

- **Dataset PASS**: score ≥ 0.80 (4/5 checks)
- **Overall PASS**: ≥ 95% of datasets pass

## Extending the Suite

### Adding a New Standard Format

1. Create parser in `app/ingestion/standards/<format>_parser.py`
2. Implement `parse_file(path) -> List[CanonicalTransaction]`
3. Add fixture in `tests/fixtures/standards/<format>_min.<ext>`
4. Add dataset entry to `ops/reader_eval/config.yaml`
5. Add test case to `tests/reader/test_standards_roundtrip.py`

### Adding a New PDF Style

1. Create YAML in `scripts/synth_statements/styles/<name>.yaml`
2. Define header tokens, table layout, noise parameters
3. Add dataset entry to `ops/reader_eval/config.yaml`
4. Generate and verify: `pytest tests/reader/test_pdf_synthetic_roundtrip.py`

### Adding a New CSV Template

1. Create CSV in `app/ingestion/csv_templates/<name>.csv`
2. Add dataset entry to `ops/reader_eval/config.yaml`
3. Generate fuzz variants
4. Verify: `pytest tests/reader/test_csv_normalization_fuzz.py`

## Troubleshooting

### Evaluation Fails for All Datasets

**Symptom:** All datasets score 0.0

**Likely cause:** Ingestion pipeline not running or API unavailable

**Solution:** Check ingestion service status, verify config points to correct API

### Reconciliation Fails for Standards

**Symptom:** camt/mt940/bai2 reconciliation errors

**Likely cause:** Sign convention mismatch (credit vs debit)

**Solution:** Check parser sign logic, verify opening/closing balance calculation

### PDF Synthetics Parse as 0 Rows

**Symptom:** Synthetic PDFs extract no transactions

**Likely cause:** Text extraction failed, OCR path not configured

**Solution:** Verify pdfplumber/Tesseract installation, check table detection logic

### Fuzzer Generates Invalid CSVs

**Symptom:** Fuzz variants fail to parse

**Likely cause:** Encoding or delimiter detection issue

**Solution:** Check chardet installation, verify CSV sniffer logic

## Summary

The reader training suite provides:

✅ **Standards compliance** via CAMT, MT940, BAI2, OFX parsers  
✅ **Robustness** via CSV locale fuzzers and synthetic PDFs  
✅ **Quality gates** via comprehensive evaluation harness  
✅ **Safety** via synthetic-only fixtures and PII redaction  
✅ **Confidence** via deterministic scoring and error taxonomy  

This ensures the AI-Bookkeeper ingestion pipeline can handle diverse real-world bank statement formats with high accuracy and reliability.



