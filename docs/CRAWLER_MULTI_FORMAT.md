# Multi-Format Financial Document Crawler

## Overview

The AI-Bookkeeper crawler has been expanded to discover and process **4 file formats** from **150+ financial institutions** across **14 categories**.

### Supported Formats

- **PDF**: Bank statements, brokerage statements, merchant reports
- **CSV**: Transaction exports, reconciliation files
- **XML**: OFX, QFX, camt.053/054, ISO20022 messages
- **TXT**: BAI2, MT940, generic transaction files

### Coverage

```
150+ Institutions across 14 Categories:
├── Traditional Banks (40+)
├── Credit Unions (10+)
├── Online/Digital Banks (13)
├── Brokerages/Investment (10)
├── Business Banking (8)
├── Payment Processors (5)
├── Marketplaces (4)
├── Gig Platforms (4)
├── Loan Servicers (2)
├── Utilities/Telecom (4)
├── Government/Standards (2)
├── Accounting/ERP (10+)
├── Open-Banking Standards (4)
└── Crypto Exchanges (4)
```

---

## Architecture

### Core Modules

#### 1. Content Type Detection (`content_types.py`)

Multi-strategy file type detection:
```
Detection Flow:
  1. Magic bytes (highest confidence)
  2. Content-Type header
  3. File extension
  4. Content analysis
```

Features:
- Detects PDF, CSV, XML, TXT
- Handles specialized formats (OFX, BAI2, MT940)
- Statement relevance filtering
- Size limit validation per format

#### 2. Category-Aware Link Filtering (`html_rules.py`)

Smart URL scoring for discovery:
```
Scoring Factors:
  - File extensions (+100 for PDF, +80 for CSV/XML)
  - Keywords in path (+15 each)
  - Category-specific patterns (+20)
  - Path depth heuristics (±10)
```

Auto-categorization:
- Banks, Brokerages, Merchants, Marketplaces
- Gig platforms, Accounting, Standards, Crypto

#### 3. Multi-Format Feature Extraction (`csv_xml_features.py`)

**CSV Features:**
- Encoding detection (UTF-8, Latin-1, etc.)
- Delimiter detection (comma, tab, pipe, semicolon)
- Header row identification
- Column type guessing (date, amount, balance, description)
- PII-redacted sample rows

**XML Features:**
- Format detection (OFX, camt.053/054, generic)
- Namespace extraction
- Tag path mapping
- Currency/date format detection
- Simplified structure representation

**TXT Features:**
- Format detection (BAI2, MT940, generic)
- Record/tag type analysis
- Structure validation

---

## Configuration

### `configs/crawler_config.yaml`

```yaml
# Multi-format support
content_type_whitelist:
  - application/pdf
  - text/csv
  - application/xml
  - text/plain
  
# Per-format size limits
pdf_max_mb: 10
csv_max_mb: 5
xml_max_mb: 5
txt_max_mb: 2

# Per-format crawl limits
max_pdfs_per_domain: 25
max_csvs_per_domain: 15
max_xmls_per_domain: 15
max_txts_per_domain: 10

# Output directories
output_pdf_features_dir: "tests/fixtures/pdf/features/crawled"
output_csv_features_dir: "tests/fixtures/csv/features/crawled"
output_xml_features_dir: "tests/fixtures/xml/features/crawled"
output_txt_features_dir: "tests/fixtures/txt/features/crawled"
```

### Category-Specific Seeds

```yaml
seed_urls:
  # Marketplaces
  - https://sellercentral.amazon.com/help/hub/reference/
  - https://help.etsy.com/hc/en-us/categories/115001053007
  - https://help.shopify.com/en/manual/finances/finances-overview
  
  # Gig Platforms
  - https://help.uber.com/driving-and-delivering/article/understanding-your-earnings-statement
  - https://help.doordash.com/dashers/s/article/DoorDash-Dasher-Support
  
  # Accounting/ERP
  - https://quickbooks.intuit.com/learn-support/en-us/help-article/bank-accounts/import-bank-transactions-using-webconnect
  - https://central.xero.com/s/article/Import-a-bank-statement
  - https://plaid.com/docs/api/products/statements/
  
  # Open-Banking Standards
  - https://www.iso20022.org/iso-20022-message-definitions
  - https://www.swift.com/standards/mt-standards
  - https://www.ofx.net/downloads.html
  - https://www.bai.org/banking-strategies/cash-management-bai-file-format-basics/
  
  # Crypto Exchanges
  - https://help.coinbase.com/en/coinbase/taxes-reports-and-financial-services/taxes
  - https://support.kraken.com/hc/en-us/articles/360001169383
```

---

## Usage

### Basic Crawl

```bash
# Crawl all configured institutions
python3 -m scripts.crawler.cli crawl

# Crawl specific domain
python3 -m scripts.crawler.cli crawl --domain stripe.com --max-pdfs 5
```

### By Category

```bash
# Marketplaces
python3 -m scripts.crawler.cli crawl --domain amazon.com
python3 -m scripts.crawler.cli crawl --domain etsy.com

# Gig platforms
python3 -m scripts.crawler.cli crawl --domain uber.com
python3 -m scripts.crawler.cli crawl --domain doordash.com

# Accounting/ERP
python3 -m scripts.crawler.cli crawl --domain quickbooks.intuit.com
python3 -m scripts.crawler.cli crawl --domain xero.com
python3 -m scripts.crawler.cli crawl --domain plaid.com

# Standards bodies
python3 -m scripts.crawler.cli crawl --domain iso20022.org
python3 -m scripts.crawler.cli crawl --domain swift.com

# Crypto
python3 -m scripts.crawler.cli crawl --domain coinbase.com
python3 -m scripts.crawler.cli crawl --domain kraken.com
```

---

## Output Structure

```
tests/fixtures/
├── pdf/features/crawled/
│   ├── stripe.com/
│   │   └── merchant_statement_abc123.json
│   └── fidelity.com/
│       └── brokerage_statement_def456.json
├── csv/features/crawled/
│   ├── quickbooks.intuit.com/
│   │   └── sample_export_ghi789.json
│   └── xero.com/
│       └── bank_feed_jkl012.json
├── xml/features/crawled/
│   ├── ofx.net/
│   │   └── ofx_sample_mno345.json
│   └── swift.com/
│       └── camt053_sample_pqr678.json
└── txt/features/crawled/
    ├── bai.org/
    │   └── bai2_sample_stu901.json
    └── iso20022.org/
        └── mt940_sample_vwx234.json
```

### Feature JSON Examples

**CSV Features:**
```json
{
  "file_name": "sample_transactions.csv",
  "format": "csv",
  "encoding": "utf-8",
  "delimiter": ",",
  "has_header": true,
  "column_count": 5,
  "header_tokens": ["Date", "Description", "Amount", "Balance", "Category"],
  "column_map_guess": {
    "Date": "date",
    "Description": "description",
    "Amount": "amount",
    "Balance": "balance",
    "Category": "unknown"
  },
  "sample_rows": [
    ["01/01/2023", "***PII_REDACTED***", "-50.00", "1000.00", "Shopping"],
    ["01/02/2023", "***PII_REDACTED***", "100.00", "1100.00", "Income"]
  ]
}
```

**XML Features (OFX):**
```json
{
  "file_name": "statement.ofx",
  "format": "ofx",
  "encoding": "utf-8",
  "root_tag": "OFX",
  "namespace": "",
  "tag_paths": [
    "OFX",
    "OFX/BANKMSGSRSV1",
    "OFX/BANKMSGSRSV1/STMTTRNRS",
    "OFX/BANKMSGSRSV1/STMTTRNRS/STMTRS"
  ],
  "currency": "USD",
  "date_format_hints": ["YYYYMMDD"],
  "sample_structure": {...}
}
```

**TXT Features (BAI2):**
```json
{
  "file_name": "statement.bai",
  "format": "bai2",
  "encoding": "utf-8",
  "line_count": 25,
  "record_types": ["01", "02", "03", "16", "49", "98", "99"],
  "structure_summary": {
    "01_file_header": true,
    "02_group_header": true,
    "03_account_identifier": true,
    "16_transaction_detail": true,
    "49_account_trailer": true,
    "98_group_trailer": true,
    "99_file_trailer": true
  }
}
```

---

## Crawl Report

After each crawl, `out/crawler_report.json` contains:

```json
{
  "start_time": "2025-10-30T10:00:00",
  "end_time": "2025-10-30T10:15:32",
  "duration_seconds": 932.5,
  "summary": {
    "domains_crawled": 12,
    "html_pages_visited": 245,
    "total_files_discovered": 48,
    "total_files_downloaded": 42,
    "total_files_failed": 6,
    "total_features_extracted": 42,
    "success_rate": 87.5
  },
  "by_format": {
    "pdf": {
      "discovered": 25,
      "downloaded": 22,
      "failed": 3,
      "features_extracted": 22
    },
    "csv": {
      "discovered": 10,
      "downloaded": 9,
      "failed": 1,
      "features_extracted": 9
    },
    "xml": {
      "discovered": 8,
      "downloaded": 7,
      "failed": 1,
      "features_extracted": 7
    },
    "txt": {
      "discovered": 5,
      "downloaded": 4,
      "failed": 1,
      "features_extracted": 4
    }
  }
}
```

---

## Safety & Compliance

### PII Redaction

All feature extraction includes automatic PII redaction:
- Emails → `***EMAIL_REDACTED***`
- Phone numbers → `***PHONE_REDACTED***`
- SSNs → `***SSN_REDACTED***`
- Account numbers → `***BANK_ACCOUNT_REDACTED***`
- Credit cards → `***CREDIT_CARD_REDACTED***`

### No Raw Files in Git

- `tests/fixtures/_public/` is gitignored
- Only non-PII feature JSONs are committed
- Original files deleted after extraction (configurable)

### Robots.txt Compliance

- Always respects robots.txt (configurable)
- 1.5s polite delay between requests
- Domain allowlist prevents off-target crawling

---

## Use Cases

### 1. Merchant/Marketplace Statements

**Target**: Stripe, Square, PayPal, Amazon, Etsy

**Formats**: PDF, CSV

**Use**: Business users reconciling sales/payouts

### 2. Gig Platform Earnings

**Target**: Uber, Lyft, DoorDash, Instacart

**Formats**: PDF, CSV

**Use**: Independent contractors tracking income

### 3. Brokerage/Investment Statements

**Target**: Fidelity, Schwab, Vanguard, E*TRADE

**Formats**: PDF, CSV

**Use**: Investors reconciling trades and dividends

### 4. Open Banking Formats

**Target**: ISO20022, SWIFT, OFX, BAI

**Formats**: XML, TXT

**Use**: Standard format parsers for banking integrations

### 5. Accounting System Imports

**Target**: QuickBooks, Xero, Wave, Plaid

**Formats**: CSV, XML, OFX

**Use**: Bank feed connectors and reconciliation

### 6. Crypto Exchange Reports

**Target**: Coinbase, Kraken, Gemini

**Formats**: CSV, PDF

**Use**: Tax reporting and transaction history

---

## Integration with Ingestion Pipeline

The crawler feeds the main ingestion pipeline:

```
Crawler → Feature Extraction → Template Learning → Auto-Processing
```

1. **Crawler** discovers and extracts features
2. **Template Builder** analyzes features to create bank-specific templates
3. **Ingestion Pipeline** uses templates to parse user uploads
4. **System** continuously improves from new data

---

## CI/CD Integration

### GitHub Actions (`.github/workflows/crawl-samples.yml`)

```yaml
name: Crawl Financial Samples

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly, Sunday 2 AM
  workflow_dispatch:  # Manual trigger

jobs:
  crawl:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install httpx pdfplumber pyyaml chardet
      
      - name: Run crawler
        run: |
          python -m scripts.crawler.run_crawl \
            --config configs/crawler_config.yaml \
            --report out/crawler_report.json
      
      - name: Upload features
        uses: actions/upload-artifact@v3
        with:
          name: crawled-features
          path: tests/fixtures/*/features/crawled/**/*.json
      
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: crawler-report
          path: out/crawler_report.json
```

---

## Testing

### Unit Tests

```bash
# Test content type detection
python -m pytest tests/crawler/test_content_types.py

# Test feature extraction
python -m pytest tests/crawler/test_csv_xml_features.py

# Test PII redaction
python -m pytest tests/crawler/test_feature_safety_multi.py
```

### Integration Test

```bash
# Run a small test crawl
python -m scripts.crawler.cli crawl \
  --domain stripe.com \
  --max-pdfs 2 \
  --verbose
```

---

## Troubleshooting

### No Files Found

**Common Causes:**
1. Files behind login walls (most common)
2. Outdated seed URLs
3. robots.txt disallows crawling

**Solutions:**
- Check `out/crawler_report.json` for skip reasons
- Try different seed URLs
- Verify domain in `allow_domains`

### Content Type Misdetection

**Solution:**
```python
# Test detection manually
from scripts.crawler.content_types import detect_content_type

file_content = Path("test.csv").read_bytes()
detected_type, confidence = detect_content_type(
    file_content,
    content_type_header="text/csv",
    file_name="test.csv"
)
print(f"Detected: {detected_type} ({confidence})")
```

### Feature Extraction Errors

**Solution:**
```python
# Test extraction manually
from scripts.crawler.csv_xml_features import extract_features

features = extract_features(file_content, "csv", "test.csv")
print(json.dumps(features, indent=2))
```

---

## Future Enhancements

- [ ] Add more crypto exchanges
- [ ] Support XLSX (Excel) format
- [ ] Add JSON transaction export support
- [ ] International bank support (UK, EU, CA)
- [ ] Machine learning for template matching
- [ ] Community template marketplace

---

## Summary

The multi-format crawler expansion enables AI-Bookkeeper to:

✅ Support **4 file formats** (PDF, CSV, XML, TXT)  
✅ Cover **150+ financial institutions**  
✅ Handle **14 institution categories**  
✅ Extract **PII-safe layout features**  
✅ Process **specialized banking formats** (OFX, BAI2, MT940, camt.053)  
✅ Respect **robots.txt and rate limits**  
✅ Generate **comprehensive reports**  

This provides a robust foundation for building statement templates and supporting diverse user needs across traditional banking, modern fintech, gig economy, and open banking standards.



