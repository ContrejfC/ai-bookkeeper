# 🕷️ Bank Statement Crawler

## Overview

The Bank Statement Crawler is a compliant, domain-restricted system for discovering public sample bank statements from major US bank websites. It extracts **layout features only** (no full content, no PII) for use in template building.

## Features

- ✅ **Robots.txt Compliance** - Respects robots.txt per domain
- ✅ **Domain Allowlist** - Only crawls pre-approved bank domains
- ✅ **Keyword Filtering** - Finds relevant sample/guide PDFs
- ✅ **PII-Safe** - Redacts all PII before storing features
- ✅ **Rate Limiting** - Polite crawling with delays
- ✅ **BFS Discovery** - Efficient link discovery from seed URLs
- ✅ **Safety First** - Never stores full content or redistributes PDFs

## Installation

```bash
# Install dependencies
pip install httpx pdfplumber beautifulsoup4 pyyaml

# Or use requirements
pip install -r requirements.txt
```

## Quick Start

### **Run the Crawler**

```bash
# Crawl all configured banks
python -m scripts.crawler.cli crawl

# Crawl specific domain
python -m scripts.crawler.cli crawl --domain chase.com

# Keep PDFs (default: delete after extraction)
python -m scripts.crawler.cli crawl --keep-pdfs

# Limit PDFs
python -m scripts.crawler.cli crawl --max-pdfs 10

# Custom config
python -m scripts.crawler.cli crawl --config my_config.yaml
```

### **Test Components**

```bash
# Test robots.txt, fetch, etc.
python -m scripts.crawler.cli test
```

## Configuration

Configuration is in `configs/crawler_config.yaml`:

```yaml
# Domain allowlist (only these domains will be crawled)
allow_domains:
  - chase.com
  - bankofamerica.com
  - wellsfargo.com
  # ... 17 more

# Seed URLs (starting points)
seed_urls:
  - https://www.chase.com/personal/online-banking/statements-documents
  - https://www.bankofamerica.com/online-banking/paperless-estatements.go
  # ... more

# Keyword filtering
keyword_allow:
  - sample statement
  - estatement
  - how to read your statement
  
keyword_deny:
  - privacy policy
  - terms and conditions

# Limits
pdf_max_mb: 10
max_pdfs_per_domain: 25
max_total_pdfs: 200

# Politeness
polite_delay_ms: 1500  # 1.5s between requests
respect_robots: true

# Storage
save_pdfs: false           # Delete PDFs after feature extraction
output_features_dir: "tests/fixtures/pdf/features/crawled"
```

## How It Works

### **1. Discovery Phase (BFS)**

```
Seed URLs → Parse HTML → Extract Links → Filter by:
  - Domain allowlist
  - Keyword match
  - Depth limit
  - robots.txt
  
Found PDFs added to queue
```

### **2. Fetch Phase**

```
For each PDF:
  1. Check robots.txt (skip if disallowed)
  2. Rate limit (polite delay per domain)
  3. HEAD request (check size/type)
  4. GET request (download PDF)
  5. Verify magic bytes (%PDF-)
```

### **3. Feature Extraction**

```
For each PDF:
  1. Open with pdfplumber
  2. Analyze first 3 pages
  3. Extract:
     - Header/footer tokens
     - Table structure (headers only)
     - Geometry hints
     - Page dimensions
  4. Redact ALL PII:
     - Emails → ***EMAIL***
     - Phones → ***PHONE***
     - SSN → ***SSN***
     - Account numbers → ***ACCOUNT***
  5. Save features to JSON
  6. Delete PDF (unless --keep-pdfs)
```

## Output

### **Features Directory**

```
tests/fixtures/pdf/features/crawled/
├── chase.com/
│   ├── a1b2c3d4e5f6g7h8.json
│   ├── i9j0k1l2m3n4o5p6.json
│   └── ...
├── bankofamerica.com/
│   ├── q7r8s9t0u1v2w3x4.json
│   └── ...
└── ...
```

### **Feature JSON Format**

```json
{
  "file_name": "sample-statement.pdf",
  "file_hash": "a1b2c3d4...",
  "file_size_bytes": 245678,
  "page_count": 3,
  "source_url": "https://chase.com/sample.pdf",
  "matched_keywords": ["sample statement"],
  "pages": [
    {
      "page_num": 1,
      "page_width": 612.0,
      "page_height": 792.0,
      "header_tokens": ["chase", "statement", "period"],
      "footer_tokens": ["member", "fdic", "questions"],
      "table_count": 1,
      "tables": [
        {
          "row_count": 15,
          "column_count": 4,
          "headers": ["Date", "Description", "Amount", "Balance"]
        }
      ],
      "geometry": {
        "header_band": [0.0, 0.20],
        "table_band": [0.25, 0.80]
      }
    }
  ]
}
```

### **Crawl Report**

```json
{
  "start_time": "2025-10-30T10:00:00",
  "end_time": "2025-10-30T10:45:23",
  "duration_seconds": 2723.5,
  "summary": {
    "domains_crawled": 18,
    "html_pages_visited": 847,
    "pdfs_discovered": 142,
    "pdfs_downloaded": 89,
    "features_extracted": 89,
    "robots_disallows": 23,
    "success_rate": 62.7
  },
  "successes": [...],
  "errors": [...],
  "skips": [...]
}
```

## Safety & Compliance

### **Legal Compliance**

1. ✅ **Robots.txt** - Always respected
2. ✅ **Rate Limiting** - 1.5s delay between requests
3. ✅ **Domain Allowlist** - Only crawls pre-approved banks
4. ✅ **No Redistribution** - PDFs never committed to git
5. ✅ **Fair Use** - Only extracts layout features for template building

### **PII Protection**

All PII is redacted before storage:
- Emails: `john@example.com` → `***EMAIL***`
- Phones: `(555) 123-4567` → `***PHONE***`
- SSN: `123-45-6789` → `***SSN***`
- Accounts: `1234567890` → `***ACCOUNT***`
- Credit Cards: `1234 5678 9012 3456` → `***CARD***`

### **What's Stored vs. What's NOT**

**✅ Stored (Features):**
- Header/footer keywords
- Table structure (column names)
- Page dimensions
- Geometry hints (percentages)

**❌ NOT Stored:**
- Full PDF content
- Account numbers
- Names
- Addresses
- Balances
- Transaction details

## Using Extracted Features

### **Feed to Template System**

```python
from pathlib import Path
import json

# Load extracted features
features_dir = Path("tests/fixtures/pdf/features/crawled/chase.com")

for feature_file in features_dir.glob("*.json"):
    with open(feature_file) as f:
        features = json.load(f)
    
    # Analyze features
    print(f"Bank: {feature_file.parent.name}")
    print(f"Pages: {features['page_count']}")
    
    for page in features['pages']:
        print(f"  Page {page['page_num']}: {page['table_count']} tables")
        if page['tables']:
            print(f"    Headers: {page['tables'][0]['headers']}")
```

### **Create Templates**

Once you have features from multiple banks:

```bash
# Review features
ls tests/fixtures/pdf/features/crawled/

# Create templates (manual or automated)
# Use header_tokens, table structures, geometry hints
```

## Adding More Banks

### **1. Add Domain to Allowlist**

Edit `configs/crawler_config.yaml`:

```yaml
allow_domains:
  - chase.com
  - your-new-bank.com  # Add here
```

### **2. Add Seed URL**

```yaml
seed_urls:
  - https://www.your-new-bank.com/help/statements
```

### **3. Run Crawler**

```bash
python -m scripts.crawler.cli crawl --domain your-new-bank.com
```

## Troubleshooting

### **No PDFs Found**

- Check seed URLs are accessible
- Verify keywords match PDF URLs
- Check robots.txt isn't blocking

### **PII Detected in Features**

- Review PII redaction patterns in `pdf_features.py`
- Add custom patterns if needed
- Run tests: `pytest tests/crawler/test_pdf_features_safety.py`

### **Crawl Too Slow**

- Reduce `polite_delay_ms` (but stay polite!)
- Reduce `max_depth`
- Limit `max_pdfs_per_domain`

### **Robots.txt Blocking Everything**

- Check if user agent is blocked
- Review robots.txt manually: `https://domain.com/robots.txt`
- Some banks may require special permission

## Development

### **Run Tests**

```bash
# All tests
pytest tests/crawler/ -v

# Specific test
pytest tests/crawler/test_robots_and_allowlist.py -v

# With coverage
pytest tests/crawler/ --cov=scripts.crawler --cov-report=html
```

### **Test Individual Components**

```python
# Test robots.txt
python scripts/crawler/robots.py

# Test PDF fetching
python scripts/crawler/fetch.py https://example.com/sample.pdf

# Test feature extraction
python scripts/crawler/pdf_features.py sample.pdf
```

## CI/CD

The crawler can run on a schedule via GitHub Actions:

```bash
# Manual trigger
.github/workflows/crawl-samples.yml

# Runs weekly, uploads features as artifacts
```

## Architecture

```
┌─────────────────┐
│  Seed URLs      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Discovery      │  BFS crawler
│  (BFS)          │  ├─ HTML parsing
└────────┬────────┘  ├─ Link extraction
         │            └─ Filtering
         ▼
┌─────────────────┐
│  Robots Check   │  Per-domain
└────────┬────────┘  ├─ Fetch robots.txt
         │            └─ Check allowance
         ▼
┌─────────────────┐
│  PDF Fetch      │  Safe download
└────────┬────────┘  ├─ HEAD check
         │            ├─ Size limit
         │            └─ Retries
         ▼
┌─────────────────┐
│  Feature Extract│  PII-safe
└────────┬────────┘  ├─ pdfplumber
         │            ├─ PII redaction
         │            └─ JSON output
         ▼
┌─────────────────┐
│  Features JSON  │  No PDFs stored
└─────────────────┘
```

## FAQ

**Q: Is this legal?**  
A: Yes, when used responsibly:
- We respect robots.txt
- We only visit public help pages
- We don't redistribute content
- We only extract layout features
- We rate limit to be polite

**Q: Can I crawl more banks?**  
A: Yes! Add domains to `allow_domains` and seed URLs to `seed_urls`.

**Q: What if a bank blocks the crawler?**  
A: Respect their decision. robots.txt compliance is mandatory.

**Q: Can I use this for other document types?**  
A: Yes, but modify keyword filters and feature extraction as needed.

**Q: How do I contribute?**  
A: Submit PRs with new bank domains, improved PII redaction, or bug fixes.

## License

See main project LICENSE file.

## Support

For issues or questions, open a GitHub issue with the `crawler` label.



