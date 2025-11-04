# Bank Statement Template Development

## Overview

This document explains the bank statement template system for AI-Bookkeeper, covering:
1. **Public sample fetching** - Safely download samples for analysis
2. **Template matching** - Recognize bank statements automatically
3. **Synthetic generation** - Create test PDFs without real data

---

## ⚠️ Legal & Compliance Notice

### **Permitted Use:**
- ✅ Public example statements from bank websites (education/demo purposes)
- ✅ Feature extraction for internal template development
- ✅ Anonymized, aggregated pattern data

### **Prohibited:**
- ❌ Actual customer bank statements
- ❌ Redistribution of bank PDFs
- ❌ Committing real PDFs to version control
- ❌ Web scraping or automated crawling

### **Best Practices:**
1. Only use URLs explicitly provided in `configs/public_samples.yaml`
2. Verify samples are publicly available for educational use
3. Delete PDFs after feature extraction (`--delete-after-extract`)
4. Never commit PDFs to git (enforced by `.gitignore`)
5. Redact all PII before storing any data

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Public Sample Workflow                       │
└─────────────────────────────────────────────────────────────────┘

1. Curated URL List (configs/public_samples.yaml)
           │
           ▼
2. Fetch Script (scripts/fetch_public_samples.py)
   ├─ Domain allowlist check
   ├─ robots.txt compliance
   ├─ Size/type validation
   └─ Download to tests/fixtures/pdf/_public/
           │
           ▼
3. Feature Extractor (app/ingestion/tools/sample_feature_extractor.py)
   ├─ Extract header tokens
   ├─ Detect table structures
   ├─ Find date/amount formats
   ├─ Analyze geometry bands
   └─ Redact PII
           │
           ▼
4. Output Storage
   ├─ Features: tests/fixtures/pdf/features/*.json
   ├─ Metadata: tests/fixtures/pdf/metadata/*.json
   └─ PDFs: DELETED (optional --delete-after-extract)
           │
           ▼
5. Template Builder
   └─ Use features to build bank-specific templates
```

---

## Quick Start

### **1. Install Dependencies**

```bash
pip install pdfplumber pyyaml requests
# OR
pip install pymupdf pyyaml requests  # Alternative PDF library
```

### **2. Configure Samples**

Edit `configs/public_samples.yaml`:

```yaml
samples:
  - name: "chase_checking_example"
    url: "https://www.chase.com/path/to/sample-statement.pdf"
    bank: "Chase"
    account_type: "checking"
    enabled: true  # Enable when you have a valid URL
```

**Important:** Replace placeholder URLs with actual public sample URLs.

### **3. Fetch Samples**

```bash
# Fetch and extract features
python scripts/fetch_public_samples.py \
  --config configs/public_samples.yaml

# Fetch, extract, then delete PDFs (recommended)
python scripts/fetch_public_samples.py \
  --config configs/public_samples.yaml \
  --delete-after-extract
```

### **4. Verify Features**

```bash
# Run tests to validate features
pytest tests/templates/test_public_sample_features.py -v

# View extracted features
cat tests/fixtures/pdf/features/chase_checking_example_features.json
```

---

## Extracted Features

### **Feature Schema**

Each `*_features.json` file contains:

```json
{
  "tool": "pdfplumber",
  "filename": "chase_checking_example.pdf",
  "page_count": 3,
  
  "header_tokens": [
    "statement", "checking", "account", "balance",
    "bank:chase"
  ],
  
  "table_headers": [
    ["Date", "Description", "Debit", "Credit", "Balance"]
  ],
  
  "date_formats": ["MM/DD/YYYY", "Mon DD, YYYY"],
  "amount_formats": ["USD_DOLLAR_SIGN"],
  
  "geometry": [
    {
      "band_index": 0,
      "y_start_pct": 0.0,
      "y_end_pct": 0.2,
      "char_count": 245,
      "has_tables": false
    }
  ],
  
  "text_density": [
    {"row": 0, "col": 0, "density": 0.0123}
  ],
  
  "metadata": {}
}
```

### **Feature Descriptions**

| Feature | Description | Usage |
|---------|-------------|-------|
| `header_tokens` | Keywords found in page header | Bank detection, template matching |
| `table_headers` | Column names in transaction tables | Column mapping, parser configuration |
| `date_formats` | Detected date format patterns | Date parsing configuration |
| `amount_formats` | Currency/amount format patterns | Amount parsing, sign detection |
| `geometry` | Vertical layout bands | Region detection, OCR targeting |
| `text_density` | Text density by grid cell | Quality assessment, OCR triggering |

---

## Building Templates

### **Using Features to Build Templates**

1. **Analyze Common Patterns**

```bash
# View all Chase samples
jq . tests/fixtures/pdf/features/chase_*_features.json
```

2. **Create Bank Template**

Example `app/ingestion/templates/banks/chase.yaml`:

```yaml
bank: "Chase"
detection:
  keywords:
    - "chase"
    - "jpmorgan"
  header_tokens:
    - "statement"
    - "checking"
    - "savings"

parsing:
  date_format: "MM/DD/YYYY"
  amount_format: "USD_DOLLAR_SIGN"
  
  table_headers:
    date: ["Date", "Trans Date", "Post Date"]
    description: ["Description", "Transaction Description"]
    amount: ["Amount", "Debit", "Credit"]
    balance: ["Balance", "Running Balance"]
  
  geometry:
    header_region: [0.0, 0.25]  # Top 25%
    table_region: [0.3, 0.85]   # Middle section
    footer_region: [0.85, 1.0]  # Bottom 15%
```

3. **Test Template Against Features**

```python
from app.ingestion.templates import match_template

features = load_features("chase_checking_example_features.json")
template = load_template("chase.yaml")

match_score = match_template(features, template)
print(f"Match score: {match_score:.2f}")  # Should be high (>0.8)
```

---

## Configuration Reference

### **configs/public_samples.yaml**

```yaml
# Domain allowlist (only these domains permitted)
allow_domains:
  - "chase.com"
  - "wellsfargo.com"
  - "bankofamerica.com"
  # Add more as needed

# Sample definitions
samples:
  - name: "unique_identifier"
    url: "https://allowed-domain.com/path/to/sample.pdf"
    bank: "Bank Name"
    account_type: "checking|savings|credit_card"
    enabled: true|false

# Fetch settings
fetch_settings:
  max_size_mb: 10
  connect_timeout: 10
  read_timeout: 10
  max_retries: 3
  respect_robots_txt: true
  user_agent: "BankStatementTemplateBuilder/1.0"

# Extraction settings
extraction_settings:
  extract_text: true
  extract_tables: true
  extract_metadata: true
  redact_pii: true
  max_text_sample_chars: 500

# Output directories
output:
  features_dir: "tests/fixtures/pdf/features"
  metadata_dir: "tests/fixtures/pdf/metadata"
  pdf_download_dir: "tests/fixtures/pdf/_public"
```

---

## Safety & Security

### **Domain Allowlist**

Only domains in `allow_domains` are permitted. Requests to other domains will be rejected.

### **robots.txt Compliance**

By default, the fetcher respects `robots.txt`. If a URL is disallowed, it will be skipped.

### **Size Limits**

- Default: 10MB max per PDF
- Configurable via `fetch_settings.max_size_mb`
- Files exceeding the limit are rejected before download

### **PII Redaction**

All features are redacted before storage:
- Email addresses → `***EMAIL_REDACTED***`
- Phone numbers → `***PHONE_REDACTED***`
- SSNs → `***SSN_REDACTED***`
- Account numbers → `***BANK_ACCOUNT_REDACTED***`

### **Git Protection**

```
tests/fixtures/pdf/.gitignore:
  *.pdf
  _public/
```

PDFs are **never** committed to version control.

---

## Testing

### **Run All Tests**

```bash
pytest tests/templates/test_public_sample_features.py -v
```

### **Test Categories**

1. **Schema Validation**: Ensure JSON structure is correct
2. **PII Redaction**: Verify no PII patterns present
3. **Domain Allowlist**: Confirm URLs are from allowed domains
4. **Feature Quality**: Check for useful data (keywords, formats, geometry)
5. **Integration**: Verify features/metadata match, PDFs not in git

### **Skip Tests if No Samples**

Tests automatically skip if no samples are present:

```bash
SKIPPED [1] No public samples downloaded. Run fetch_public_samples.py first.
```

---

## Troubleshooting

### **Issue: No samples downloaded**

**Solution:**
1. Ensure URLs in `configs/public_samples.yaml` are valid
2. Set `enabled: true` for samples you want to fetch
3. Check domain is in `allow_domains`
4. Verify internet connectivity

### **Issue: robots.txt blocking**

**Solution:**
1. Check if URL is allowed by visiting `https://domain.com/robots.txt`
2. Contact bank to request permission for educational use
3. If appropriate, set `respect_robots_txt: false` (use with caution)

### **Issue: Feature extraction fails**

**Solution:**
1. Install required libraries: `pip install pdfplumber` or `pip install pymupdf`
2. Check PDF is not encrypted or password-protected
3. Try alternative PDF library if one fails

### **Issue: PII detected in features**

**Solution:**
1. Review `app/ingestion/utils/pii.py` patterns
2. Add custom patterns if needed
3. Ensure `redact_pii: true` in config
4. Report issue for investigation

---

## Advanced Usage

### **Custom Feature Extraction**

Create a custom extractor:

```python
from app.ingestion.tools.sample_feature_extractor import extract_features

# Extract with custom settings
features = extract_features(
    pdf_path="path/to/statement.pdf",
    redact_pii=True
)

# Add custom analysis
features['custom_analysis'] = analyze_custom_patterns(features)

# Save
with open('custom_features.json', 'w') as f:
    json.dump(features, f, indent=2)
```

### **Batch Processing**

Process multiple samples:

```bash
for pdf in tests/fixtures/pdf/_public/*.pdf; do
  python -m app.ingestion.tools.sample_feature_extractor "$pdf" > "$(basename $pdf .pdf)_features.json"
done
```

### **Template Matching Algorithm**

```python
def match_template(features: dict, template: dict) -> float:
    """
    Compute match score between extracted features and a template.
    
    Returns:
        Score between 0.0 (no match) and 1.0 (perfect match)
    """
    score = 0.0
    
    # Check keyword overlap
    feature_tokens = set(features.get('header_tokens', []))
    template_keywords = set(template['detection']['keywords'])
    keyword_overlap = len(feature_tokens & template_keywords)
    score += keyword_overlap / len(template_keywords) * 0.3
    
    # Check date format match
    if features.get('date_formats'):
        if template['parsing']['date_format'] in features['date_formats']:
            score += 0.2
    
    # Check amount format match
    if features.get('amount_formats'):
        if template['parsing']['amount_format'] in features['amount_formats']:
            score += 0.2
    
    # Check table header compatibility
    feature_headers = [h for row in features.get('table_headers', []) for h in row]
    template_headers = [h for headers in template['parsing']['table_headers'].values() for h in headers]
    header_overlap = len(set(feature_headers) & set(template_headers))
    score += header_overlap / max(len(template_headers), 1) * 0.3
    
    return min(score, 1.0)
```

---

## Maintenance

### **Adding New Banks**

1. Find public sample URL from bank website
2. Add to `configs/public_samples.yaml` with `enabled: false`
3. Verify domain is in `allow_domains`
4. Test URL manually
5. Set `enabled: true` and fetch
6. Review features and build template

### **Updating Templates**

1. Fetch new samples when banks update statement formats
2. Compare new features with existing templates
3. Update templates to handle format variations
4. Run tests to validate changes

### **Cleaning Up**

```bash
# Remove old PDFs (if not auto-deleted)
rm -rf tests/fixtures/pdf/_public/*

# Keep only recent features (example: keep last 5 per bank)
# (Implement custom cleanup script as needed)
```

---

## FAQ

**Q: Can I use real customer statements?**  
A: No. Only use public examples from bank websites.

**Q: Should I commit PDFs to git?**  
A: Never. PDFs are gitignored and should be deleted after extraction.

**Q: What if a bank doesn't have public samples?**  
A: Create synthetic test fixtures or use redacted templates from other banks.

**Q: How do I know if a URL is allowed by robots.txt?**  
A: The fetcher checks automatically. You can also manually visit `https://domain.com/robots.txt`.

**Q: Can I add my own bank?**  
A: Yes, if you have a public sample URL. Add it to `configs/public_samples.yaml`.

**Q: What PDF libraries are supported?**  
A: `pdfplumber` (preferred) or `pymupdf`. Install at least one.

---

---

## Template Matching System

### **What It Does**

The template matcher automatically recognizes bank statements by matching:
- Header keywords ("Statement Period", "Account Number")
- Table structure (column headers)
- Footer keywords ("Member FDIC")
- Geometry/layout patterns

### **How It Works**

```python
from app.ingestion.templates.registry import get_default_registry
from app.ingestion.utils.text_features import extract_text_features

# 1. Extract features from PDF
features = extract_text_features("statement.pdf")

# 2. Match against known templates
registry = get_default_registry()
best_match = registry.get_best_match(features)

if best_match:
    print(f"Matched: {best_match.template.bank_name}")
    print(f"Score: {best_match.score:.2f}")
    print(f"Confidence: {best_match.confidence:.2f}")
```

### **Available Templates**

| Bank | Template Name | Threshold | Features |
|------|---------------|-----------|----------|
| Chase | `chase_checking_v1` | 0.75 | MDY dates, single amount column |
| Wells Fargo | `wells_fargo_checking_v1` | 0.75 | "Account Summary" header |
| Fifth Third | `fifth_third_checking_v1` | 0.75 | Separate debit/credit columns |
| Bank of America | `bank_of_america_checking_v1` | 0.75 | "Running Bal." terminology |
| U.S. Bank | `us_bank_checking_v1` | 0.75 | "Additions/Subtractions" columns |

### **Template YAML Structure**

```yaml
name: "chase_checking_v1"
version: 1
bank_name: "Chase"

match:
  header_keys:
    - "Statement Period"
    - "Account Number"
  table_headers:
    - "(?i)^date$"
    - "(?i)^description$"
    - "(?i)^amount$"
  footer_keywords:
    - "Questions"
    - "Member FDIC"
  date_format_pref: "MDY"
  
score_weights:
  headers: 0.35
  table: 0.35
  footer: 0.10
  geometry: 0.20

accept_threshold: 0.75
```

### **Adding Custom Templates**

1. Create a new YAML file in `app/ingestion/templates/banks/`
2. Follow the schema above
3. Use generic, non-copyrighted text patterns only
4. Test with synthetic PDFs

---

## Synthetic Statement Generation

### **Why Synthetic?**

- ✅ No real customer data
- ✅ No copyright issues
- ✅ Reproducible tests
- ✅ Parameterizable scenarios

### **Generate Synthetic PDFs**

```bash
# Basic usage
python scripts/generate_synthetic_statement.py \
  --style chase \
  --out /tmp/chase_test.pdf

# Custom configuration
python scripts/generate_synthetic_statement.py \
  --style wells_fargo \
  --account "****5678" \
  --balance 2500.00 \
  --transactions 50 \
  --out test_statement.pdf
```

### **Available Styles**

- `chase`
- `wells_fargo`
- `fifth_third`
- `bank_of_america`
- `us_bank`

### **Synthetic Features**

Each generated PDF includes:
- Realistic header with account info
- Configurable transaction count
- Random but realistic descriptions
- Proper running balances
- Generic footer text
- **NO logos or trademarks**

### **Testing with Synthetic PDFs**

```bash
# 1. Generate synthetic PDF
python scripts/generate_synthetic_statement.py \
  --style chase \
  --out test_chase.pdf

# 2. Extract features
python -m app.ingestion.utils.text_features test_chase.pdf

# 3. Run end-to-end tests
pytest tests/templates/test_synthetic_roundtrip.py -v
```

---

## Privacy Guardrails

### **Learning from User Uploads**

When processing real user statements, we persist **ONLY**:

✅ **Allowed:**
- Template name and match score
- Column mappings (e.g., "Column 2 = description")
- Header tokens matched (non-PII keywords)
- Geometry hints (page regions as percentages)
- 2 sample rows with:
  - Descriptions hashed (SHA256)
  - Amounts rounded to nearest dollar
  - Dates removed

❌ **Never Stored:**
- Full text content
- Account numbers
- Transaction details
- Customer names
- Any PII

### **Example Learned Data**

```json
{
  "template_match": {
    "template_name": "chase_checking_v1",
    "score": 0.92,
    "matched_tokens": ["Statement Period", "Account Number"]
  },
  "column_mapping": {
    "date": 0,
    "description": 1,
    "amount": 2,
    "balance": 3
  },
  "geometry_hints": {
    "header_band": [0.0, 0.18],
    "table_band": [0.22, 0.84]
  },
  "sample_rows": [
    {
      "description_hash": "a3f2c1...",
      "amount_rounded": -45.0
    },
    {
      "description_hash": "b9e4d8...",
      "amount_rounded": 1500.0
    }
  ]
}
```

This approach allows template improvement without storing sensitive data.

---

## Integration with Ingestion Pipeline

### **Automatic Template Selection**

```python
from app.ingestion.extract.pdf_template import PDFTemplateExtractor

# Extractor automatically:
# 1. Extracts text features
# 2. Matches against templates
# 3. Uses template-specific parsing if match found
# 4. Falls back to generic extraction if no match

extractor = PDFTemplateExtractor()
result = extractor.extract(context)

if result.success:
    print(f"Extracted {len(result.raw_transactions)} transactions")
    print(f"Method: {result.extraction_method}")
    print(f"Confidence: {result.confidence}")
```

### **Flow Diagram**

```
Upload PDF
    │
    ▼
Extract Text Features
    │
    ▼
Match Against Templates
    │
    ├─[Match ≥ Threshold]──> Use Template-Specific Parser
    │                            │
    │                            ▼
    │                        Apply Date Format (MDY/DMY)
    │                            │
    │                            ▼
    │                        Apply Amount Sign Rules
    │                            │
    └─[No Match]────────────> Use Generic Parser
                                │
                                ▼
                            Extract Transactions
                                │
                                ▼
                            Normalize & Deduplicate
```

---

## Testing

### **Template Matcher Tests**

```bash
# Run all template tests
pytest tests/templates/ -v

# Just template matching
pytest tests/templates/test_template_matcher.py -v

# Just synthetic roundtrip
pytest tests/templates/test_synthetic_roundtrip.py -v
```

### **Test Coverage**

| Test Category | Tests | Coverage |
|---------------|-------|----------|
| Schema Validation | 4 | Template structure, weights, criteria |
| Registry Loading | 3 | YAML loading, retrieval, errors |
| Template Matching | 5 | Feature matching, scoring, thresholds |
| Individual Scoring | 3 | Keywords, tables, geometry |
| Synthetic Generation | 6 | All 5 bank styles + configurations |
| Feature Extraction | 3 | Headers, tables, geometry |
| End-to-End Parsing | 4 | Full extract-parse-normalize flow |
| **Total** | **28** | **Comprehensive** |

---

## Related Documentation

- [Ingestion Pipeline](../INGESTION_COMPLETION_GUIDE.md)
- [PII Redaction](../app/ingestion/utils/pii.py)
- [Feature Extractor](../app/ingestion/tools/sample_feature_extractor.py)
- [Launch Checks](../ops/launch_checks/README.md)
- [Template Schema](../app/ingestion/templates/schema.py)
- [Template Registry](../app/ingestion/templates/registry.py)

---

## Support

For issues or questions:
1. Check logs: `--verbose` flag for detailed output
2. Run tests: `pytest tests/templates/ -v`
3. Review this documentation
4. Generate synthetic PDFs for debugging
5. Contact the development team

---

**Last Updated:** 2025-10-30  
**Version:** 2.0 (Added Template Matching & Synthetic Generation)  
**Maintainer:** AI-Bookkeeper Team

