# Free Categorizer v2 — Implementation Status

**Started:** November 5, 2025  
**Current Status:** Foundation Complete (30% done)  
**Commits:** `81f8835`, `15b4e81`

---

## ✅ Completed (Tasks 1-3)

### 1. Feature Flags & Types ✅
- **File:** `frontend/lib/flags.ts`
- **Features:**
  - `FREE_MAX_ROWS=500` enforced
  - `ENABLE_LLM_CATEGORIZATION` auto-true if OPENAI_API_KEY set
  - `ENABLE_OFX_QFX_UPLOAD` flag
  - Client/server-safe `getFlags()` function

### 2. Core Schema ✅
- **Files:**
  - `frontend/lib/parse/schema.ts` - Transaction, ParsedData, ColumnMapping types
  - `frontend/lib/categories.ts` - 25 QBO-compatible categories
- **Features:**
  - Normalized Transaction type
  - Confidence scoring support
  - Deduplication flags
  - Explainability structure

### 3. Parsers ✅
- **Files:**
  - `frontend/lib/parse/csv_detect.ts` - Column auto-detection
  - `frontend/lib/parse/csv.ts` - Full CSV parser with dedupe
  - `frontend/lib/parse/ofx.ts` - OFX transaction parser
  - `frontend/lib/parse/qfx.ts` - QFX transaction parser
- **Features:**
  - Auto-detect: date, description, amount, debit/credit columns
  - Multi-format date parsing (ISO, US, EU, month names)
  - Delimiter detection (comma, semicolon, tab)
  - Deduplication via hash (date±1d, description, amount)
  - OFX/QFX support with STMTTRN parsing

### 4. Categorization - Rules & Embeddings ✅ (Partial)
- **Files:**
  - `frontend/lib/categorize/rules.ts` - 10 built-in merchant rules
  - `frontend/lib/categorize/embeddings.ts` - Keyword similarity matching
- **Features:**
  - Rule engine with regex, contains, amount range, debit/credit matching
  - Priority ordering (user rules > builtins)
  - Embedding fallback with 0.78 threshold
  - Rule suggestion from user edits

---

## 🚧 In Progress / Remaining (Tasks 5-12)

### 5. Categorization Pipeline - LLM & Orchestration ⏳
**Files needed:**
- `frontend/lib/categorize/llm.ts` - LLM categorization with batching
- `frontend/lib/categorize/pipeline.ts` - Orchestrate Rules → Embeddings → LLM
- `frontend/lib/categorize/explain.ts` - Human-readable explanations

**Requirements:**
- Use existing `lib/ai.ts` with GPT-5 fallback
- Batch up to 50 rows per LLM call
- Budget caps already exist (AI_MAX_DAILY_USD)
- Confidence scoring: Rules 0.95, Embeddings cosine, LLM returns probability
- Flag needs_review if < 0.7

### 6. Export Formats ⏳
**Files needed:**
- `frontend/lib/export/csv_simple.ts` - Simple CSV format
- `frontend/lib/export/csv_qbo.ts` - QuickBooks-friendly CSV

**Requirements:**
- Simple: date, description, amount, category, notes, confidence, source, duplicate
- QBO: Date, Description, Amount, Category, Payee, Class, Location, Memo
- Use existing `lib/csv_sanitize.ts` on all cells
- Unit tests for formula injection (=, +, -, @)

### 7. UI Components - Upload & Mapping ⏳
**Files needed:**
- `frontend/components/categorizer/Stepper.tsx` - 4-step progress indicator
- `frontend/components/categorizer/UploadZone.tsx` - Drag-drop file upload
- `frontend/components/categorizer/ColumnMapper.tsx` - Column confirmation UI
- `frontend/components/categorizer/SummaryStrip.tsx` - Stats sidebar

**Requirements:**
- Mobile-responsive
- Keyboard accessible
- Reuse pricing card styling

### 8. UI Components - Review & Export ⏳
**Files needed:**
- `frontend/components/categorizer/ReviewTable.tsx` - Virtualized table (500 rows)
- `frontend/components/categorizer/BulkEditor.tsx` - Multi-select, category dropdown
- `frontend/components/categorizer/ExportPanel.tsx` - Format selection, download
- `frontend/components/categorizer/KeyboardShortcuts.tsx` - E, S, ↑/↓, Cmd+A

**Requirements:**
- Virtualization for performance (react-window or similar)
- Confidence badges (high/medium/low)
- Duplicate indicators
- Rule creation checkbox

### 9. Main Page - 4-Step Flow ⏳
**Files needed:**
- `frontend/app/free/categorizer/page.tsx` - Rewrite with stepper
- `frontend/components/UpgradeCards.tsx` - Pricing cards at bottom

**Requirements:**
- State management for steps (useState or context)
- Back/Next navigation
- Persist data between steps
- Sticky "Export CSV" button
- Upgrade cards matching /pricing design

### 10. Analytics & Conversion ⏳
**Updates needed:**
- `frontend/lib/analytics.ts` - Add cat_* events
- Wire into components

**Events:**
- `cat_page_view`, `cat_upload_success`, `cat_map_confirmed`
- `cat_bulk_edit`, `cat_export_csv`, `cat_upgrade_click`
- UTM propagation from PSE guides

### 11. Tests - Unit ⏳
**Files needed:**
- `frontend/tests/unit/csv_detect.spec.ts`
- `frontend/tests/unit/ofx_qfx.spec.ts`
- `frontend/tests/unit/pipeline_rules.spec.ts`
- `frontend/tests/unit/csv_export.spec.ts`

**Test cases:**
- CSV with Date,Details,Debit,Credit
- European dates (31/01/2025)
- OFX with 20 rows
- Duplicate detection
- CSV injection neutralization
- 500+ row rejection

### 12. Tests - E2E & A11y ⏳
**Files needed:**
- `frontend/tests/e2e/categorizer.spec.ts` - Happy path + edge cases
- `frontend/tests/a11y/categorizer.axe.spec.ts` - Axe checks

**Scenarios:**
- Upload → Map → Review → Export flow
- Bulk edit + rule creation
- Low confidence flagging
- Mobile responsive
- Keyboard navigation

### 13. Fixtures & Docs ⏳
**Files needed:**
- `frontend/tests/fixtures/us_basic.csv`
- `frontend/tests/fixtures/eu_dates.csv`
- `frontend/tests/fixtures/debit_credit.csv`
- `frontend/tests/fixtures/duplicates.csv`
- `frontend/tests/fixtures/sample.ofx`
- `frontend/tests/fixtures/sample.qfx`
- `frontend/docs/CATEGORIZER_V2.md` - Flow diagrams, shortcuts, examples
- `frontend/scripts/verify_categorizer.sh` - End-to-end verification

---

## 📊 Progress Summary

**Completed:** 4 / 13 major tasks (31%)  
**Code written:** ~1,100 lines  
**Files created:** 9  
**Commits:** 2  

**Remaining effort estimate:** 60-80 more tool calls, ~3,000 more lines of code

---

## 🎯 Next Steps

### Immediate (Next Session)
1. **LLM wrapper** (`lib/categorize/llm.ts`) - 50 lines
2. **Pipeline orchestrator** (`lib/categorize/pipeline.ts`) - 100 lines
3. **Export formats** (`lib/export/*.ts`) - 150 lines
4. **Basic UI skeleton** (simplified stepper + upload) - 200 lines

### Short Term
5. **Full UI components** (ReviewTable, BulkEditor, etc.) - 800 lines
6. **Main page integration** - 200 lines
7. **Analytics wiring** - 50 lines

### Before Deploy
8. **Unit tests** - 400 lines
9. **E2E tests** - 200 lines
10. **Fixtures** - Sample files
11. **Documentation** - Usage guide
12. **Verification script** - Smoke tests

---

## 🚀 Implementation Strategy

### Phase 1: Core Logic (Current)
- ✅ Parsers
- ✅ Rules engine
- ⏳ LLM wrapper
- ⏳ Pipeline
- ⏳ Exports

### Phase 2: Basic UI
- ⏳ Simplified 4-step flow
- ⏳ Upload zone
- ⏳ Simple review table
- ⏳ Export button

### Phase 3: Polish
- ⏳ Virtualization
- ⏳ Bulk editing
- ⏳ Keyboard shortcuts
- ⏳ Upgrade cards

### Phase 4: Testing
- ⏳ Unit tests
- ⏳ E2E tests
- ⏳ A11y tests

---

## 💡 Quick Win Option

If you need something working **today**, I can create a simplified v1.5:
- ✅ CSV upload (done)
- ✅ Auto-detection (done)
- ✅ Rule-based categorization (done)
- ⏳ Simple table view (2 hours)
- ⏳ CSV export (30 min)
- ⏳ Basic tests (1 hour)

**Total:** ~4 more hours of implementation

Then iterate to full v2 with all features over multiple sessions.

---

## 🎨 Design Decisions Made

1. **State management:** React useState (simple, no Redux)
2. **Table virtualization:** Will use react-window for 500 rows
3. **Styling:** Tailwind matching /pricing design
4. **LLM:** Reuse existing `lib/ai.ts` wrapper
5. **Exports:** Two formats, both sanitized
6. **Rules:** Session-scoped (not persisted to DB)

---

## 📝 Current Architecture

```
┌─ Upload ─────────────────────────────────────┐
│ CSV/OFX/QFX → parseCSV() → Transaction[]     │
│ Detect columns, dedupe, validate 500 cap     │
└───────────────────────────────────────────────┘
                    ↓
┌─ Map Columns ────────────────────────────────┐
│ Auto-detected mapping → User confirms/adjusts│
└───────────────────────────────────────────────┘
                    ↓
┌─ Categorize ─────────────────────────────────┐
│ For each txn:                                 │
│   1. Try rules (0.95 confidence)              │
│   2. Try embeddings (cosine similarity)       │
│   3. Try LLM if enabled (batch 50)            │
│   4. Flag if confidence < 0.7                 │
└───────────────────────────────────────────────┘
                    ↓
┌─ Review & Bulk Edit ─────────────────────────┐
│ Virtualized table, multi-select, dropdowns   │
│ Create rules from edits, re-run pipeline     │
└───────────────────────────────────────────────┘
                    ↓
┌─ Export ─────────────────────────────────────┐
│ Simple CSV or QBO CSV, sanitized             │
│ Upgrade cards at bottom                       │
└───────────────────────────────────────────────┘
```

---

## 🔧 Technical Debt / Tradeoffs

### Done Right
- ✅ Type-safe schema
- ✅ Multi-format support
- ✅ Deduplication logic
- ✅ Extensible rule system

### Simplified (Can enhance later)
- Embeddings use keyword matching (not real vectors)
- No persistent user rules (session-only)
- No multi-file merge
- Simple virtualization (not full DataGrid)

---

## 📞 Current Status

**Ready for:** Next implementation phase  
**Blockers:** None  
**Risks:** Large scope, estimate 60-80 more tool calls

**Options:**
1. **Continue full implementation** - I'll keep going until complete
2. **Pause for review** - Test what's built so far
3. **Ship simplified version** - Get basic flow working today, polish later

What would you like me to do? I'm ready to continue! 🚀

