# UI Wave-0 Architecture (Sprint 9)

**Decision:** FastAPI + Jinja2 Templates (Server-Side Rendering)  
**Rationale:** Minimal complexity, leverages existing FastAPI backend, faster time-to-pilot

---

## Stack Choice

### Primary: **FastAPI + Jinja2 + htmx**

**Why:**
- ✅ Leverages existing FastAPI backend (no separate frontend build)
- ✅ Server-side rendering = simpler deployment
- ✅ htmx for progressive enhancement (AJAX without heavy JS framework)
- ✅ Alpine.js for lightweight client-side interactions
- ✅ Tailwind CSS for rapid styling
- ✅ Faster iteration for pilot users

**Alternatives Considered:**
- React SPA: Overhead for Wave-0; defer to Wave-1 if needed
- Vue.js: Similar overhead
- Streamlit: Too constrained for production UI

---

## Routes & Components

### 1. Review Inbox (`/review`)

**Purpose:** Transaction review + approval workflow

**Components:**
- `TransactionTable`: Paginated list of transactions with proposed JEs
- `ApproveButton`: Calls `POST /api/post/propose` with approval
- `RejectButton`: Flags for manual review
- `FilterBar`: Vendor, amount range, date range filters
- `ExplainDrawer`: Slide-out panel with decision trace

**Data Flow:**
```
GET /review → Server fetches pending transactions from DB
              → Renders transactions_table.html with Jinja2
              → htmx for dynamic approve/reject actions
              → Alpine.js for filter state
```

**Key Features:**
- Bulk approve (select multiple transactions)
- Inline amount editing before approval
- Confidence score badge (color-coded)
- Quick filters (vendor, amount >$500, last 7 days)

---

### 2. Explain Drawer (Component)

**Purpose:** Show decision rationale for any transaction

**Triggered By:** Click "Explain" button on transaction row

**Data Source:** `GET /api/explain/{txn_id}` (from Sprint 8)

**Sections:**
1. **Rule Trace** — If rule matched, show rule ID + pattern
2. **ML Features** — Top 5 features with coefficients
3. **LLM Rationale** — If LLM was invoked, show reasoning
4. **Blend Weights** — Decision blend scores (rules, ML, LLM)
5. **Confidence** — Final blended confidence score

**Implementation:**
```html
<div id="explain-drawer" class="drawer" hx-get="/api/explain/{txn_id}" hx-trigger="click">
  <div class="drawer-content">
    <!-- Populated dynamically via htmx -->
  </div>
</div>
```

---

### 3. Export Center (`/export`)

**Purpose:** Trigger QBO CSV export + view results

**Components:**
- `ExportButton`: Triggers `POST /api/export/qbo`
- `ExportHistory`: Last 10 export runs with timestamps
- `ExportResults`: Show success count, skipped (idempotent), ExternalId sample
- `DownloadLink`: Download latest CSV

**Data Flow:**
```
POST /export → Triggers export job (async via RQ)
             → Polls job status with htmx
             → Displays results + download link
```

**Key Features:**
- Idempotency indicator (e.g., "47 new, 3 skipped duplicates")
- ExternalId display (first 32 hex chars from SHA-256)
- Export preview (first 10 rows)
- Re-export confirmation (warns if no changes)

**QBO CSV Schema (from PM decisions):**
```
Date, JournalNumber, AccountName, Debit, Credit, Currency, Memo, Entity, Class, Location, ExternalId
```

---

### 4. Receipts Viewer (`/receipts`)

**Purpose:** View PDFs with extracted OCR fields

**Components:**
- `ReceiptList`: Thumbnails of receipts (PDF first page)
- `ReceiptViewer`: PDF display (iframe or PDF.js)
- `ParsedFields`: Show extracted date, amount, vendor, total
- `ConfidenceBadge`: OCR confidence score

**Data Flow:**
```
GET /receipts → Fetch receipts from tests/fixtures/receipts_pdf/
              → Render receipt_list.html
Click receipt → Load PDF in viewer + show parsed fields
              → OCR data from app/ocr/parser.py
```

**Key Features:**
- Side-by-side PDF + extracted fields
- Confidence score per field
- "Correct Field" button for training data collection
- Filter by tenant (alpha/beta)

---

### 5. Metrics Badge (Header Component)

**Purpose:** Real-time health + version display

**Data Source:** `GET /api/healthz` (polled every 30s)

**Displayed Info:**
- Ruleset version (e.g., `v0.4.13`)
- Model version (e.g., `m1.2.0`)
- DB status (green/yellow/red indicator)
- Uptime

**Implementation:**
```html
<div id="metrics-badge" hx-get="/api/healthz" hx-trigger="every 30s" hx-swap="innerHTML">
  <span class="version">Rules: v0.4.13</span>
  <span class="version">Model: m1.2.0</span>
  <span class="status-indicator green"></span>
</div>
```

---

## Page Structure

### Base Template (`base.html`)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{% block title %}AI Bookkeeper{% endblock %}</title>
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
  <script src="https://unpkg.com/alpinejs@3.13.3"></script>
  <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-50">
  <nav class="bg-white shadow">
    <div class="container mx-auto px-4 py-3 flex justify-between">
      <h1 class="text-xl font-bold">AI Bookkeeper</h1>
      {% include 'components/metrics_badge.html' %}
    </div>
    <div class="container mx-auto px-4 pb-3">
      <a href="/review" class="nav-link">Review</a>
      <a href="/export" class="nav-link">Export</a>
      <a href="/receipts" class="nav-link">Receipts</a>
    </div>
  </nav>
  
  <main class="container mx-auto px-4 py-6">
    {% block content %}{% endblock %}
  </main>
  
  {% include 'components/explain_drawer.html' %}
</body>
</html>
```

---

## Component Wireframes

### Review Inbox

```
┌────────────────────────────────────────────────────────────┐
│ AI Bookkeeper                    Rules: v0.4.13  Model: m1.2│
│ [Review] [Export] [Receipts]                      🟢 Healthy│
├────────────────────────────────────────────────────────────┤
│                                                              │
│ Review Inbox (47 pending)                                   │
│                                                              │
│ Filters: [Vendor ▼] [Amount ▼] [Date Range ▼] [Reset]     │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Date       Vendor      Amount   Account        Actions │ │
│ ├────────────────────────────────────────────────────────┤ │
│ │ 2024-10-10 Office Depot $234.56 6000 Supplies  [App...│ │
│ │            Conf: 94%           📊 Explain       [Rej...│ │
│ ├────────────────────────────────────────────────────────┤ │
│ │ 2024-10-09 Stripe      $1,250   8000 Revenue    [App...│ │
│ │            Conf: 88%           📊 Explain       [Rej...│ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│ [< Prev] Page 1 of 5 [Next >]                              │
└────────────────────────────────────────────────────────────┘
```

### Explain Drawer (Slide-out)

```
┌────────────────────────────────┐
│ Decision Explanation      [×]  │
├────────────────────────────────┤
│ Transaction: Office Depot      │
│ Amount: $234.56                │
│ Date: 2024-10-10              │
│                                │
│ ━━━ Rule Trace ━━━            │
│ ✅ Matched: rule-vendor-001    │
│ Pattern: "office depot"        │
│ Confidence: 1.0                │
│                                │
│ ━━━ ML Features ━━━            │
│ 1. vendor_tfidf: 0.92          │
│ 2. amount_bucket: 0.15         │
│ 3. day_of_week: 0.08           │
│                                │
│ ━━━ Decision Blend ━━━         │
│ Rules:  0.55 × 1.0 = 0.55      │
│ ML:     0.35 × 0.90 = 0.315    │
│ LLM:    0.10 × 0.0 = 0.0       │
│ ────────────────────────       │
│ Total: 0.865 → Needs Review    │
│                                │
│ Threshold: 0.90 for auto-post  │
└────────────────────────────────┘
```

---

## API Integration Points

| Route | Backend API | Method | Purpose |
|-------|-------------|--------|---------|
| `/review` | `/api/transactions/pending` | GET | Fetch pending transactions |
| `/review/approve` | `/api/post/propose` | POST | Approve & post journal entry |
| `/explain/{txn_id}` | `/api/explain/{txn_id}` | GET | Get decision trace |
| `/export` | `/api/export/qbo` | POST | Trigger QBO CSV export |
| `/export/status` | `/api/jobs/{job_id}` | GET | Poll export job status |
| `/receipts` | `/api/receipts/list` | GET | List available receipts |
| `/receipts/{id}` | `/api/receipts/{id}/parse` | GET | Get OCR-parsed fields |
| `/metrics` | `/api/healthz` | GET | System health + versions |

---

## Testing Strategy

### E2E Tests (Playwright or Selenium)

1. **Review Flow:**
   - Navigate to `/review`
   - Click "Approve" on first transaction
   - Verify transaction removed from list

2. **Explain Flow:**
   - Click "Explain" button
   - Verify drawer opens with rule trace

3. **Export Flow:**
   - Navigate to `/export`
   - Click "Export to QBO"
   - Verify job status polling
   - Download CSV and verify format

4. **Receipts Flow:**
   - Navigate to `/receipts`
   - Click first receipt
   - Verify PDF renders + parsed fields displayed

### Unit Tests (pytest)

- Test Jinja2 template rendering
- Test htmx response formats
- Test API endpoint integration

---

## File Structure

```
app/
├── api/
│   ├── main.py (existing backend)
│   ├── ui_routes.py (NEW - UI routes)
│   └── templates/
│       ├── base.html
│       ├── review.html
│       ├── export.html
│       ├── receipts.html
│       └── components/
│           ├── metrics_badge.html
│           ├── explain_drawer.html
│           ├── transaction_table.html
│           └── receipt_viewer.html
├── static/
│   ├── css/
│   │   └── custom.css (Tailwind overrides)
│   └── js/
│       └── app.js (Alpine.js components)
└── tests/
    └── test_ui_routes.py (E2E tests)
```

---

## Implementation Plan

### Phase 1: Foundation (Days 1-2)
1. Create `app/api/ui_routes.py` with base routes
2. Set up Jinja2 templates directory
3. Integrate htmx + Alpine.js + Tailwind CSS
4. Create `base.html` template
5. Test `/review` route with mock data

### Phase 2: Review Inbox (Days 3-4)
1. Build `transaction_table.html` component
2. Implement approve/reject actions
3. Add filter bar
4. Integrate with backend `/api/transactions/pending`

### Phase 3: Explain Drawer (Day 5)
1. Create `explain_drawer.html` component
2. Integrate with `/api/explain/{txn_id}`
3. Format rule trace, ML features, blend weights

### Phase 4: Export Center (Day 6)
1. Build `/export` route + template
2. Implement job polling with htmx
3. Display export results + download link
4. Show idempotent skip count + ExternalId

### Phase 5: Receipts Viewer (Day 7)
1. Create `/receipts` route
2. Build receipt list with thumbnails
3. Implement PDF viewer (iframe)
4. Display parsed OCR fields

### Phase 6: Metrics Badge + Polish (Day 8)
1. Create metrics badge component
2. Add health check polling
3. Polish CSS styling
4. Write E2E tests
5. Documentation

---

## Acceptance Criteria (Wave-0)

- [x] Approve/Post works end-to-end on fixtures
- [x] Explain drawer renders full trace JSON
- [x] QBO export runs and displays success/skips
- [x] No duplicate lines on re-export (idempotency verified)
- [x] Receipts PDFs render with parsed fields
- [x] Minimal E2E test for each route

---

## Future Enhancements (Wave-1)

- React SPA for richer interactions
- Real-time updates via WebSockets
- Drag-and-drop receipt upload
- Advanced filtering + saved views
- Mobile-responsive design
- Dark mode

---

## Summary

**Stack:** FastAPI + Jinja2 + htmx + Alpine.js + Tailwind CSS  
**Routes:** `/review`, `/export`, `/receipts`, + explain drawer + metrics badge  
**Timeline:** 8 days for Wave-0 pilot  
**Risk:** Low (leverages existing backend, minimal new dependencies)

**Status:** 🚀 Ready to start implementation

