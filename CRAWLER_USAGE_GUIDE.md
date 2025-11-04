# Bank Statement Crawler - Usage Guide

## Overview

The bank statement crawler discovers and extracts layout features from **public sample/guide PDFs** published by financial institutions. It now supports **100+ financial institutions** across multiple categories.

## 🌐 Supported Institutions

### Categories Covered
- ✅ **Top 10 US Banks** (Chase, BofA, Wells Fargo, Citi, etc.)
- ✅ **Regional Banks** (40+ including Fifth Third, KeyBank, Regions, etc.)
- ✅ **Credit Unions** (Navy Federal, PenFed, Alliant, etc.)
- ✅ **Online/Digital Banks** (Ally, Marcus, Discover, SoFi, Chime, etc.)
- ✅ **Investment/Brokerage** (Schwab, Fidelity, E*TRADE, Vanguard, etc.)
- ✅ **Credit Card Issuers** (Amex, Capital One, Discover, Barclays)
- ✅ **Business Banking** (Brex, Mercury, Ramp, etc.)
- ✅ **Payment Processors** (Stripe, Square, PayPal)
- ✅ **Wealth Management** (Morgan Stanley, UBS, Merrill Lynch, etc.)

**Total: 100+ domains configured with 60+ seed URLs**

---

## 🚀 Quick Start

### 1. Basic Crawl (Single Institution)

```bash
# Crawl a specific bank for up to 5 PDFs
python3 -m scripts.crawler.cli crawl --domain ally.com --max-pdfs 5
```

### 2. Crawl All Configured Institutions

```bash
# Crawl all 100+ institutions (respects max limits per config)
python3 -m scripts.crawler.cli crawl
```

### 3. Crawl Multiple Specific Institutions

```bash
# Online banks only
python3 -m scripts.crawler.cli crawl --domain ally.com
python3 -m scripts.crawler.cli crawl --domain marcus.com
python3 -m scripts.crawler.cli crawl --domain discover.com
```

### 4. Crawl Investment/Brokerage Platforms

```bash
# Brokerage statements
python3 -m scripts.crawler.cli crawl --domain schwab.com --max-pdfs 10
python3 -m scripts.crawler.cli crawl --domain fidelity.com --max-pdfs 10
python3 -m scripts.crawler.cli crawl --domain etrade.com --max-pdfs 10
```

### 5. Crawl Business Banking

```bash
# Modern fintech business banking
python3 -m scripts.crawler.cli crawl --domain brex.com --max-pdfs 5
python3 -m scripts.crawler.cli crawl --domain mercury.com --max-pdfs 5
python3 -m scripts.crawler.cli crawl --domain ramp.com --max-pdfs 5
```

### 6. Crawl Payment Processors

```bash
# Merchant statements
python3 -m scripts.crawler.cli crawl --domain stripe.com --max-pdfs 10
python3 -m scripts.crawler.cli crawl --domain square.com --max-pdfs 10
```

---

## 📖 Command Reference

### Basic Command Structure

```bash
python3 -m scripts.crawler.cli crawl [OPTIONS]
```

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `--config PATH` | Path to config file | `--config configs/crawler_config.yaml` |
| `--domain DOMAIN` | Filter to specific domain | `--domain chase.com` |
| `--max-pdfs N` | Maximum PDFs to download | `--max-pdfs 10` |
| `--verbose` | Enable verbose logging | `--verbose` |
| `--output-dir DIR` | Output directory for features | `--output-dir out/features` |

### Examples with Options

```bash
# Verbose crawl of Ally Bank with custom output
python3 -m scripts.crawler.cli crawl \
  --domain ally.com \
  --max-pdfs 5 \
  --verbose \
  --output-dir tests/fixtures/pdf/features/ally

# Quick test crawl with limit
python3 -m scripts.crawler.cli crawl \
  --domain fidelity.com \
  --max-pdfs 3

# Full crawl with custom config
python3 -m scripts.crawler.cli crawl \
  --config configs/custom_crawler.yaml \
  --verbose
```

---

## 🎯 Use Cases & Strategies

### Use Case 1: Building a Comprehensive Template Library

**Goal:** Extract features from as many institutions as possible

```bash
#!/bin/bash
# crawl_all_banks.sh

DOMAINS=(
  "chase.com" "bankofamerica.com" "wellsfargo.com" "citi.com"
  "usbank.com" "pnc.com" "capitalone.com" "ally.com"
  "schwab.com" "fidelity.com" "discover.com" "marcus.com"
)

for domain in "${DOMAINS[@]}"; do
  echo "Crawling $domain..."
  python3 -m scripts.crawler.cli crawl \
    --domain "$domain" \
    --max-pdfs 5 \
    --verbose
  sleep 10  # Be extra polite between institutions
done
```

### Use Case 2: Focus on Digital Banks

**Goal:** Target modern online/digital banks with simpler statements

```bash
# Online banks typically have cleaner, more consistent formats
python3 -m scripts.crawler.cli crawl --domain ally.com --max-pdfs 10
python3 -m scripts.crawler.cli crawl --domain marcus.com --max-pdfs 10
python3 -m scripts.crawler.cli crawl --domain sofi.com --max-pdfs 10
python3 -m scripts.crawler.cli crawl --domain chime.com --max-pdfs 10
```

### Use Case 3: Investment Statements

**Goal:** Build templates for brokerage/investment statements

```bash
# Brokerage statements have different formats than bank statements
python3 -m scripts.crawler.cli crawl --domain schwab.com --max-pdfs 15
python3 -m scripts.crawler.cli crawl --domain fidelity.com --max-pdfs 15
python3 -m scripts.crawler.cli crawl --domain vanguard.com --max-pdfs 15
python3 -m scripts.crawler.cli crawl --domain etrade.com --max-pdfs 15
```

### Use Case 4: Business/Merchant Statements

**Goal:** Support business users with merchant and business banking statements

```bash
# Business banking
python3 -m scripts.crawler.cli crawl --domain brex.com --max-pdfs 10
python3 -m scripts.crawler.cli crawl --domain mercury.com --max-pdfs 10

# Payment processors
python3 -m scripts.crawler.cli crawl --domain stripe.com --max-pdfs 20
python3 -m scripts.crawler.cli crawl --domain square.com --max-pdfs 20
```

### Use Case 5: Regional Bank Coverage

**Goal:** Support regional banks for specific geographic areas

```bash
# Southeast US
python3 -m scripts.crawler.cli crawl --domain regions.com --max-pdfs 5
python3 -m scripts.crawler.cli crawl --domain synovus.com --max-pdfs 5

# Northeast US
python3 -m scripts.crawler.cli crawl --domain mtb.com --max-pdfs 5
python3 -m scripts.crawler.cli crawl --domain citizensbank.com --max-pdfs 5

# West Coast
python3 -m scripts.crawler.cli crawl --domain zionsbank.com --max-pdfs 5
python3 -m scripts.crawler.cli crawl --domain umpquabank.com --max-pdfs 5
```

---

## 📂 Output Structure

After running the crawler, you'll find:

```
tests/fixtures/pdf/
├── features/
│   └── crawled/
│       ├── ally_20251030_statement_001.json
│       ├── chase_20251030_statement_001.json
│       ├── fidelity_20251030_brokerage_001.json
│       └── ...
├── _public/
│   └── crawled/
│       └── (PDFs, if save_pdfs=true in config)
└── metadata/
    └── crawled/
        └── (Metadata JSON files)

out/
└── crawler_report.json  # Comprehensive crawl report
```

### Feature JSON Format

Each extracted feature file contains **non-PII layout information**:

```json
{
  "file_name": "ally_statement_sample.pdf",
  "num_pages": 3,
  "page_features": [
    {
      "page_num": 1,
      "page_width": 612.0,
      "page_height": 792.0,
      "header_tokens": ["account", "statement", "period", "online", "savings"],
      "footer_tokens": ["member", "fdic", "page", "privacy"],
      "table_header_candidates": [
        ["Date", "Description", "Withdrawals", "Deposits", "Balance"]
      ],
      "date_format_hints": ["MM/DD/YYYY", "Mon DD, YYYY"],
      "amount_format_hints": ["$#,###.##", "-$#,###.##"],
      "geometry_bands": [...],
      "text_density_grid": [...]
    }
  ]
}
```

### Crawl Report

`out/crawler_report.json` contains:

```json
{
  "timestamp": "2025-10-30T02:33:17Z",
  "config": {...},
  "summary": {
    "total_domains": 12,
    "html_pages_visited": 1523,
    "pdfs_discovered": 15,
    "pdfs_downloaded": 15,
    "features_extracted": 15,
    "errors": 0
  },
  "by_domain": {
    "ally.com": {
      "pdfs_found": 3,
      "pdfs_downloaded": 3,
      "features_extracted": 3,
      "seed_urls_used": 2
    }
  },
  "discovered_urls": [...],
  "errors": []
}
```

---

## 🔧 Advanced Configuration

### Custom Crawler Config

Create a custom config for specific use cases:

```yaml
# configs/custom_investment_crawler.yaml

allow_domains:
  - schwab.com
  - fidelity.com
  - vanguard.com
  - etrade.com
  - tdameritrade.com

seed_urls:
  - https://www.schwab.com/resource-center/insights/content/how-read-your-statement
  - https://www.fidelity.com/learning-center/personal-finance/understanding-statements

keyword_allow:
  - brokerage statement
  - investment statement
  - account statement
  - monthly statement
  - quarterly statement
  - trade confirmation

pdf_max_mb: 15  # Investment statements can be larger
max_pdfs_per_domain: 30
max_total_pdfs: 100
```

Use it:

```bash
python3 -m scripts.crawler.cli crawl \
  --config configs/custom_investment_crawler.yaml \
  --verbose
```

---

## 🛡️ Safety & Compliance

### Built-in Safety Features

1. **robots.txt Compliance**: Always respects site robots.txt
2. **Politeness**: 1.5s delay between requests (configurable)
3. **Domain Allowlist**: Only crawls pre-approved domains
4. **PII Redaction**: Automatically redacts PII before storage
5. **No PDF Storage**: PDFs deleted after feature extraction (configurable)
6. **Size Limits**: 10MB max per PDF, respects HTML page limits
7. **Timeouts**: 10s connect, 10s read with automatic retries

### What Gets Stored

✅ **Stored:**
- Layout geometry (header/footer positions, table locations)
- Non-PII text tokens (generic headers like "Date", "Amount")
- Format hints (date patterns, number formats)
- Page dimensions and structure

❌ **NOT Stored:**
- Actual PDF files (deleted after extraction)
- PII (emails, phones, SSNs, account numbers)
- Transaction details
- Customer names or addresses
- Proprietary bank logos or branding

---

## 📊 Monitoring & Reports

### View Last Crawl Report

```bash
# Pretty-print the crawl report
python3 -c "
import json
with open('out/crawler_report.json') as f:
    report = json.load(f)
    print(f'Crawled: {report[\"summary\"][\"total_domains\"]} domains')
    print(f'Pages visited: {report[\"summary\"][\"html_pages_visited\"]}')
    print(f'PDFs found: {report[\"summary\"][\"pdfs_discovered\"]}')
    print(f'Features extracted: {report[\"summary\"][\"features_extracted\"]}')
"
```

### Check Feature Extraction Success

```bash
# Count extracted features
find tests/fixtures/pdf/features/crawled -name "*.json" | wc -l

# List all extracted features
ls -lh tests/fixtures/pdf/features/crawled/
```

---

## 🚨 Troubleshooting

### Problem: No PDFs Found

**Likely Causes:**
1. Sample PDFs are behind login walls (most common)
2. Bank doesn't publish public samples
3. Seed URLs are outdated or moved

**Solutions:**
```bash
# Try a different seed URL manually
python3 -m scripts.crawler.cli crawl \
  --domain ally.com \
  --verbose  # Look for discovered URLs in logs

# Or add direct PDF URL to seed_urls in config if you find one
```

### Problem: Crawler Timing Out

**Solution:**
```bash
# Increase timeouts in config
timeout_connect_s: 30
timeout_read_s: 30
```

### Problem: Rate Limited (429 errors)

**Solution:**
```bash
# Increase politeness delay in config
polite_delay_ms: 3000  # 3 seconds instead of 1.5
```

### Problem: Feature Extraction Failed

**Solution:**
```bash
# Check logs for specific errors
tail -f logs/crawler.log

# Manually test feature extraction on a PDF
python3 -c "
from app.ingestion.tools.sample_feature_extractor import extract_features_from_pdf
from pathlib import Path
features = extract_features_from_pdf(Path('test.pdf'))
print(features)
"
```

---

## 🎨 Integration with Template System

### After Crawling

The extracted features feed into the template matching system:

1. **Features Extracted** → `tests/fixtures/pdf/features/crawled/*.json`
2. **Template Builder** → Analyzes features to create bank-specific templates
3. **Template Registry** → Stores templates in `app/ingestion/templates/banks/*.yaml`
4. **Ingestion Pipeline** → Uses templates to parse user-uploaded statements

### Manual Template Creation

You can manually inspect features and create templates:

```bash
# View extracted features
cat tests/fixtures/pdf/features/crawled/ally_statement_001.json | jq '.page_features[0].header_tokens'

# Create template based on features
vim app/ingestion/templates/banks/ally.yaml
```

---

## 📚 Adding New Institutions

### Step 1: Add to Config

Edit `configs/crawler_config.yaml`:

```yaml
allow_domains:
  - newbank.com  # Add domain

seed_urls:
  - https://www.newbank.com/help/statements  # Add seed URL
```

### Step 2: Test Crawl

```bash
python3 -m scripts.crawler.cli crawl \
  --domain newbank.com \
  --max-pdfs 3 \
  --verbose
```

### Step 3: Review Results

```bash
# Check if any PDFs were found
cat out/crawler_report.json | jq '.by_domain["newbank.com"]'

# View extracted features
ls tests/fixtures/pdf/features/crawled/newbank*
```

---

## 🔄 Scheduled Crawling

### Cron Job for Weekly Crawls

```bash
# Add to crontab
crontab -e

# Run every Sunday at 2 AM
0 2 * * 0 cd /path/to/ai-bookkeeper && python3 -m scripts.crawler.cli crawl --max-pdfs 5 >> logs/weekly_crawl.log 2>&1
```

### CI/CD Integration

See `.github/workflows/crawler.yml` for automated scheduled crawls with artifact uploads.

---

## 📞 Support & Contribution

### Report Issues

- Missing institution? Open an issue with the bank name and seed URL
- Found a PDF but features not extracted? Include the URL and error log

### Contribute

To add support for international banks or additional US institutions:
1. Add domains to `allow_domains`
2. Add seed URLs to `seed_urls`
3. Test with `--verbose` flag
4. Submit PR with crawl report

---

## ✅ Summary

The crawler now supports **100+ financial institutions** across:
- Traditional banks
- Credit unions
- Online/digital banks
- Investment platforms
- Business banking
- Payment processors

**Key Commands:**
```bash
# Single institution
python3 -m scripts.crawler.cli crawl --domain ally.com --max-pdfs 5

# All institutions
python3 -m scripts.crawler.cli crawl

# Verbose mode
python3 -m scripts.crawler.cli crawl --verbose
```

**Output:** Non-PII layout features stored in `tests/fixtures/pdf/features/crawled/`

**Next Steps:** Use extracted features to build templates for the ingestion pipeline!



