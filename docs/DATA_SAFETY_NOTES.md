# Data Safety & Privacy Guidelines

## Overview

AI-Bookkeeper handles sensitive financial data. This document outlines strict guidelines for training assets, test fixtures, and data handling to ensure **zero real user data** is ever committed to version control or shared externally.

---

## Golden Rules

### 🚫 **NEVER Commit**

1. **Real bank statements** (PDF, CSV, OFX, or any format)
2. **Real account numbers** (even partially masked)
3. **Real transaction descriptions** (actual merchant names, payee details)
4. **Real names** or personal information
5. **Real balances** or amounts from user accounts
6. **Crawler-downloaded PDFs** (even if from public domains)
7. **Screenshots** containing real data

### ✅ **ALWAYS Use**

1. **Synthetic data** generated programmatically
2. **Standards-based minimal examples** from public specifications
3. **Redacted features** (layout geometry, column types, hashed tokens)
4. **Placeholder values** (John Doe, Account #1234567890, $123.45)
5. **Generated test data** with clear fake patterns

---

## Fixture Categories

### 1. Standards Fixtures (SAFE)

**Location:** `tests/fixtures/standards/`

**Content:** Minimal examples based on public format specifications (ISO 20022, SWIFT MT940, BAI2, OFX).

**Example:**
```xml
<!-- camt053_min.xml -->
<Ntry>
  <Amt Ccy="USD">100.00</Amt>
  <Dbtr><Nm>ACME Corp</Nm></Dbtr>
  <AddtlNtryInf>Payment for Invoice #12345</AddtlNtryInf>
</Ntry>
```

**Safety:** Uses generic company names, round amounts, and public format structures. No real financial data.

**Source:** Public ISO 20022, SWIFT, and OFX documentation.

### 2. CSV Templates (SAFE)

**Location:** `app/ingestion/csv_templates/`

**Content:** Synthetic CSV files with generated transactions.

**Example:**
```csv
Date,Description,Amount
01/01/2024,Coffee Shop Purchase,-4.50
01/02/2024,Salary Deposit,2500.00
01/03/2024,Utility Bill,-85.00
```

**Safety:** Generic descriptions, round or patterned amounts, no real merchant names.

**Generation:** Created manually or via faker libraries with clearly synthetic data.

### 3. Synthetic PDFs (SAFE)

**Location:** `tests/fixtures/pdf_synth/` (generated at test-time, not committed)

**Content:** Programmatically generated bank statement PDFs using ReportLab.

**Example:**
```python
generate_statement(
    account_number="****1234",  # Masked placeholder
    transactions=[
        {"date": "01/01/2024", "desc": "Online Purchase", "amount": -25.00},
        {"date": "01/02/2024", "desc": "Direct Deposit", "amount": 1500.00}
    ]
)
```

**Safety:** All data generated in-memory with placeholders. PDFs created during tests and deleted after.

**Generation:** `scripts/synth_statements/generator.py` using YAML style definitions.

### 4. Crawler Features (SAFE with redaction)

**Location:** `tests/fixtures/pdf/features/crawled/`

**Content:** Layout features extracted from public PDFs (if any are found), with **strict PII redaction**.

**Example:**
```json
{
  "file_name": "sample_abc123.pdf",
  "header_tokens": ["Statement Period", "Account Number", "***REDACTED***"],
  "table_headers": ["Date", "Description", "Amount"],
  "geometry_bands": {"header": [0.0, 0.15], "table": [0.15, 0.85]},
  "sample_rows": [
    {"date": "01/01/2024", "desc": "***HASHED_f4a3b2***", "amount": "-XX.XX"}
  ]
}
```

**Safety:**
- **No raw PDFs stored**
- Account numbers → `***REDACTED***`
- Descriptions → hashed (`sha1(text)[:12]`)
- Amounts → rounded or masked
- Only layout features retained

**Source:** Public "how to read your statement" samples from bank domains (if found).

---

## PII Redaction Rules

### What is PII?

**Personally Identifiable Information (PII)** includes any data that can identify a specific individual:

- Full names (except generic placeholders like "John Doe")
- Account numbers (full or partial)
- Email addresses
- Phone numbers
- Social Security Numbers (SSN)
- Credit card numbers
- Transaction descriptions with identifiable details
- Exact dollar amounts from real accounts
- Dates combined with specific transactions (can fingerprint individuals)

### Redaction Strategies

#### 1. Masking

Replace with placeholder characters:

```
Original: Account #4532-1098-7654-3210
Redacted: Account #****-****-****-3210
```

#### 2. Hashing

One-way hash for non-reversible redaction:

```python
import hashlib

def hash_description(desc: str) -> str:
    return "***HASH_" + hashlib.sha1(desc.encode()).hexdigest()[:8] + "***"

# Original: "Starbucks #1234 Seattle WA"
# Redacted: "***HASH_a3f4b2c1***"
```

#### 3. Rounding

Remove precision that could fingerprint users:

```
Original: $1,234.67
Redacted: $1,235.00  (round to nearest $5 or $10)
```

#### 4. Generalization

Replace specific with generic:

```
Original: "Amazon.com Purchase - Order #123-4567890-1234567"
Redacted: "Online Retailer Purchase"
```

### Automated Redaction

**File:** `app/ingestion/utils/pii.py`

```python
import re

PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    "credit_card": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
    "account": r'\b\d{8,17}\b'  # 8-17 digit numbers
}

def redact_pii(text: str) -> str:
    for pii_type, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f"***{pii_type.upper()}_REDACTED***", text)
    return text
```

**Usage:**
- Applied to all crawler outputs before storage
- Applied to any logs or error messages
- Applied to sample rows in feature JSONs

---

## .gitignore Configuration

Ensure these patterns are in `.gitignore`:

```gitignore
# Real user data (never commit)
tests/fixtures/pdf/_real/
tests/fixtures/pdf/_public/*.pdf
tests/fixtures/csv/_real/
uploads/

# Generated assets (safe, but large)
tests/fixtures/pdf_synth/*.pdf
tests/fixtures/csv/locale_variants/*.csv
out/reader_eval/

# Temporary files
*.tmp
*.temp
/tmp/

# Environment files (may contain API keys)
.env
.env.local
.env.*.local

# User-specific IDE files
.vscode/
.idea/
*.swp
```

---

## Safe Test Data Generation

### Using Faker Library

```python
from faker import Faker

fake = Faker()

# Generate synthetic transactions
transactions = []
for _ in range(10):
    transactions.append({
        "date": fake.date_between(start_date='-30d', end_date='today'),
        "description": fake.company() + " Purchase",
        "amount": round(fake.random.uniform(-500, 500), 2)
    })
```

### Using Templates

Create templates with placeholders:

```
Account Number: {{ACCT_NUM}}
Period: {{START_DATE}} to {{END_DATE}}
Balance: ${{BALANCE}}
```

Then populate with generated values during tests.

### Using Public Standards

ISO 20022 and SWIFT provide example messages in their documentation. These are safe to use as they're public and synthetic.

**Source:** https://www.iso20022.org/catalogue-messages
**Source:** https://www.swift.com/standards/mt-standards

---

## Developer Checklist

Before committing any code:

- [ ] No real account numbers
- [ ] No real names (except "John Doe" type placeholders)
- [ ] No real transaction descriptions
- [ ] No real dollar amounts from user data
- [ ] PDF fixtures are synthetic or excluded via `.gitignore`
- [ ] Crawler outputs contain only redacted features
- [ ] Test data uses `faker` or programmatic generation
- [ ] `.gitignore` patterns cover all sensitive directories
- [ ] PII redaction is applied to any logged or stored text
- [ ] Code review includes data safety check

---

## Incident Response

### If Real Data is Accidentally Committed

**IMMEDIATE ACTIONS:**

1. **DO NOT** force push or rebase to remove from history (creates more issues)
2. **Rotate any API keys or secrets** in the exposed data
3. **Contact repository admin** to purge commits (GitHub support)
4. **Create a new commit** removing the sensitive file(s)
5. **Verify** via `git log --all -- <file>` that file is gone from working tree
6. **Notify affected users** if applicable (per GDPR/CCPA)
7. **Document** in an incident report

**PREVENTION:**

- Use pre-commit hooks to scan for PII patterns
- Require code review for any new fixtures
- Regular audits of `tests/fixtures/` directory
- Training for new developers on data safety

### Pre-Commit Hook (Optional)

**File:** `.git/hooks/pre-commit`

```bash
#!/bin/bash

# Scan staged files for potential PII
if git diff --cached --name-only | grep -E '\.(csv|pdf|json)$'; then
    echo "⚠️  WARNING: You are committing a CSV, PDF, or JSON file."
    echo "   Ensure it contains NO real user data."
    read -p "   Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for obvious PII patterns in staged content
if git diff --cached | grep -E '\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b'; then
    echo "❌ ERROR: Potential SSN detected in staged changes!"
    exit 1
fi

if git diff --cached | grep -E '\b[0-9]{4}[\s-][0-9]{4}[\s-][0-9]{4}[\s-][0-9]{4}\b'; then
    echo "❌ ERROR: Potential credit card detected in staged changes!"
    exit 1
fi
```

---

## Third-Party Data Sources

### Public Bank Statement Samples

Some banks publish "how to read your statement" PDFs on their websites. These are safe to **extract features from** but should **NOT be committed as PDFs**.

**Process:**
1. Crawler downloads PDF temporarily
2. Extract layout features (header positions, column types)
3. Redact any text tokens via PII patterns
4. Store only features JSON
5. Delete original PDF

**Example domains where samples might exist:**
- https://www.swift.com/standards/mt-standards (MT940 examples)
- https://www.iso20022.org/sample-messages (CAMT examples)
- OFX.net (OFX format samples)

### Synthetic Data Providers

These are safe to use:

- **Mockaroo** (https://mockaroo.com): Generate realistic CSV data
- **Faker** (Python library): Generate names, addresses, amounts
- **ReportLab** (Python library): Generate PDFs programmatically

---

## Compliance Notes

### GDPR (General Data Protection Regulation)

- **Right to erasure**: Never commit real data that would require deletion later
- **Data minimization**: Use only synthetic data for development
- **Purpose limitation**: Training data must not contain real user transactions

### CCPA (California Consumer Privacy Act)

- **No sale of data**: Test fixtures must not be based on real user data
- **Transparency**: Document all data sources clearly

### SOC 2

- **Access controls**: Limit who can add fixtures to repository
- **Audit logging**: Code review process for all fixture additions
- **Encryption**: Any temporary real data must be encrypted at rest

---

## Summary

✅ **DO:**
- Use synthetic data generated programmatically
- Extract redacted features from public samples
- Use standards-based minimal examples
- Apply PII redaction to all stored text
- Generate PDFs at test-time and delete after
- Document data sources clearly

❌ **DON'T:**
- Commit real bank statements
- Store real account numbers or names
- Share raw PDFs downloaded by crawler
- Use production data in tests
- Store unredacted transaction descriptions
- Bypass `.gitignore` patterns

**When in doubt, ask:** "Would I be comfortable if this data was public on GitHub?"

If the answer is no, it doesn't belong in the repository.

---

**Last Updated:** 2025-10-30  
**Owner:** Engineering Team  
**Review Cadence:** Quarterly



