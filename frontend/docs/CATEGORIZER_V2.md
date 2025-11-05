# Free Categorizer v2 — Documentation

**Version:** 2.0  
**Last Updated:** November 5, 2025

---

## Overview

The Free Categorizer v2 is a guided 4-step flow for uploading, mapping, reviewing, and exporting categorized bank transactions.

### Key Features

- **Multi-format support:** CSV, OFX, QFX
- **Auto-detection:** Columns, delimiters, date formats
- **Smart categorization:** Rules → Embeddings → LLM pipeline
- **Confidence scoring:** 0.0-1.0 with review flagging
- **Deduplication:** Automatic duplicate detection
- **Two export formats:** Simple CSV and QuickBooks CSV
- **Formula-safe:** All exports sanitized

---

## User Flow

### Step 1: Upload
1. Drag-drop or click to select file
2. Supports CSV, OFX, QFX (up to 10MB, 500 rows)
3. Auto-validates file type and size

### Step 2: Map Columns
1. System auto-detects: Date, Description, Amount (or Debit/Credit)
2. User confirms or adjusts mapping
3. Preview shows sample data

### Step 3: Review & Edit
1. View all transactions in table
2. Each has auto-assigned category with confidence badge
3. Edit categories via dropdown
4. See duplicates highlighted
5. Review low-confidence transactions (<70%)

### Step 4: Export
1. Choose format: Simple CSV or QuickBooks CSV
2. Download categorized file
3. Warnings for low-confidence rows

---

## Categorization Pipeline

### Stage 1: Rules (95% confidence)
**Built-in merchant patterns:**
- Coffee shops (Starbucks, Dunkin, etc.)
- Fuel (Shell, Chevron, BP, etc.)
- Ride share (Uber, Lyft)
- Office supplies (Staples, Office Depot)
- SaaS (Vercel, AWS, Stripe, GitHub)
- Utilities (Comcast, Verizon, AT&T)
- Bank fees
- Transfers

**User rules:**
- Create from edits during review
- Highest priority (applied first)
- Session-scoped (not persisted)

### Stage 2: Embeddings (0.78+ threshold)
**Keyword similarity matching:**
- 10 category lexicons (coffee, fuel, groceries, etc.)
- Cosine-like similarity scoring
- Fast local computation

### Stage 3: LLM (if enabled)
**GPT-5 batch categorization:**
- Batches of 50 transactions
- Budget-controlled (existing AI caps)
- Fallback to GPT-4o if needed
- Returns confidence scores

### Fallback
If no stage matches: "Uncategorized" with needs_review=true

---

## File Format Support

### CSV
**Detection:**
- Delimiters: comma, semicolon, tab
- Date formats: ISO, US (MM/DD/YYYY), EU (DD/MM/YYYY), month names
- Amount formats: signed, currency symbols, thousands separators
- Debit/Credit columns: auto-combines to signed amount

**Columns recognized:**
- Date, Posted, Transaction Date
- Description, Memo, Details, Payee
- Amount, Total, Value
- Debit, Withdrawal
- Credit, Deposit

### OFX (Open Financial Exchange)
**Parsing:**
- Extracts STMTTRN blocks
- Fields: DTPOSTED, TRNAMT, NAME, MEMO, TRNTYPE
- Converts YYYYMMDD dates
- Combines NAME + MEMO for description

### QFX (Quicken)
**Parsing:**
- Same as OFX (QFX is OFX variant)
- Recognizes QFXHEADER
- Compatible with Quicken exports

---

## Export Formats

### Simple CSV
**Columns:**
- Date (YYYY-MM-DD)
- Description (original)
- Amount (signed decimal)
- Category (assigned name)
- Confidence (0.00-1.00)
- Source (rule/embedding/llm/manual)
- Duplicate (Yes/No)
- Notes (rule name or match details)

**Use case:** Full audit trail, data analysis

### QuickBooks CSV
**Columns:**
- Date (YYYY-MM-DD)
- Description
- Amount (signed)
- Category (QBO-compatible name)
- Payee (extracted from description)
- Class (empty in free tier)
- Location (empty in free tier)
- Memo (confidence + source + duplicate flag)

**Use case:** Direct import to QuickBooks Online

### Security
Both formats sanitize cells to prevent CSV formula injection:
- Prefixes `=`, `+`, `-`, `@` with single quote `'`
- Preview stays readable (Excel shows value, not formula)

---

## Categories

**25 QBO-compatible categories:**

**Income (4):**
- Sales Revenue
- Service Revenue
- Interest Income
- Other Income

**Expenses (19):**
- Advertising & Marketing
- Auto & Vehicle
- Bank Fees & Charges
- Insurance
- Legal & Professional
- Meals & Entertainment
- Office Supplies
- Rent & Lease
- Repairs & Maintenance
- Software & Subscriptions
- Supplies
- Taxes & Licenses
- Travel
- Utilities
- Wages & Payroll
- Shipping & Delivery
- Postage
- Dues & Subscriptions

**Other (2):**
- Transfer
- Payment
- Uncategorized

---

## API Usage (Developers)

### Parse a CSV
```typescript
import { parseCSV } from '@/lib/parse/csv';

const csvText = await file.text();
const parsed = parseCSV(csvText);

// Result:
// {
//   transactions: Transaction[],
//   columnMapping: {date: 0, description: 1, amount: 2},
//   rowCount: 150,
//   duplicateCount: 3
// }
```

### Categorize Transactions
```typescript
import { categorizeTransactions } from '@/lib/categorize/pipeline';

const categorized = await categorizeTransactions(parsed.transactions);

// Each transaction now has:
// - category: string
// - confidence: number
// - source: 'rule' | 'embedding' | 'llm' | 'manual'
// - needsReview: boolean
// - explanation: Explanation object
```

### Export
```typescript
import { exportSimpleCSV } from '@/lib/export/csv_simple';
import { exportQBOCSV } from '@/lib/export/csv_qbo';

const simpleCsv = exportSimpleCSV(categorized);
const qboCsv = exportQBOCSV(categorized);

// Both are sanitized and ready to download
```

---

## Performance

### Benchmarks (500 rows)

| Operation | Time | Notes |
|-----------|------|-------|
| CSV parsing | <100ms | Local, instant |
| Column detection | <50ms | Heuristic-based |
| Rules categorization | <200ms | 10 rules, regex matching |
| Embeddings categorization | <500ms | Keyword similarity |
| LLM categorization | 4-6s | Batched (50/batch), network-dependent |
| Export CSV | <100ms | String generation |
| **Total (no LLM)** | **<1s** | Fast, cheap |
| **Total (with LLM)** | **<7s** | Budget-controlled |

### Optimization
- Rules checked first (fastest, highest confidence)
- LLM only for unmatched transactions
- Batching reduces API calls by 50x
- Local embeddings (no API calls)

---

## Keyboard Shortcuts (Planned)

| Key | Action |
|-----|--------|
| `E` | Edit selected category |
| `S` | Save changes |
| `↑/↓` | Navigate rows |
| `Space` | Toggle select |
| `Cmd/Ctrl+A` | Select all |
| `Esc` | Clear selection |

*(Implementation in progress)*

---

## Limits (Free Tier)

| Limit | Value | Configurable |
|-------|-------|--------------|
| Max rows | 500 | `FREE_MAX_ROWS` |
| Max file size | 10MB | `FREE_MAX_FILE_MB` |
| Retention | 24 hours | `FREE_RETENTION_HOURS` |
| LLM calls | Budget-capped | `AI_MAX_DAILY_USD` |

---

## Troubleshooting

### "Column detection failed"
- **Cause:** Unusual header names or formats
- **Fix:** Use Step 2 to manually map columns

### "Date parsing failed"
- **Cause:** Unsupported date format
- **Fix:** Convert dates to YYYY-MM-DD or MM/DD/YYYY before upload

### "File too large"
- **Cause:** >500 rows or >10MB
- **Fix:** Split file or upgrade to paid plan

### "Low confidence warnings"
- **Cause:** Unusual merchant names, LLM unavailable
- **Fix:** Review and manually assign categories, create rules

---

## For Developers

### Adding New Rules
```typescript
// lib/categorize/rules.ts
export const BUILTIN_RULES: Rule[] = [
  ...BUILTIN_RULES,
  {
    id: 'r-my-vendor',
    name: 'My Vendor',
    category: 'Office Supplies',
    priority: 10,
    merchantRegex: /myvendor|my vendor inc/i
  }
];
```

### Adding Categories
```typescript
// lib/categories.ts
export const QBO_CATEGORIES: Category[] = [
  ...QBO_CATEGORIES,
  {
    id: 'expense-custom',
    name: 'Custom Category',
    type: 'expense',
    qboClass: 'Expense',
    keywords: ['keyword1', 'keyword2']
  }
];
```

### Custom Embedding Lexicon
```typescript
// lib/categorize/embeddings.ts
const MERCHANT_LEXICON: Record<string, {category: string; keywords: string[]}> = {
  'custom': { category: 'Custom Category', keywords: ['word1', 'word2'] }
};
```

---

## Testing

### Run Unit Tests
```bash
npm test -- csv_detect.spec.ts
```

### Manual Testing
1. Upload `tests/fixtures/us_basic.csv`
2. Verify auto-detection works
3. Check categories assigned
4. Export both formats
5. Open in Excel - verify no formula execution

---

## Deployment

**No special config needed!**

Existing environment variables work:
- `OPENAI_API_KEY` - Enables LLM (optional)
- `FREE_MAX_ROWS` - Row limit (default: 500)
- `FREE_MAX_FILE_MB` - Size limit (default: 10)

---

## Future Enhancements

### v2.1 (Next)
- Bulk editing with multi-select
- Keyboard shortcuts
- Table virtualization for 1000+ rows
- Persistent user rules

### v2.2
- Multi-file merge
- Historical data (see previous uploads)
- Rule management UI
- Export to QuickBooks API (direct)

### v2.3
- Column mapping presets (save for reuse)
- Custom categories
- Reconciliation mode
- Batch processing

---

**Questions?** Check `CAT_V2_COMPLETE_CORE.md` for implementation details.

