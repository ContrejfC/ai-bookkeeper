# AI Bookkeeper - Complete Technical Outline

**Version:** 1.0  
**Date:** October 26, 2025  
**Status:** Production Ready  
**Author:** Technical Documentation

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Backend Components](#backend-components)
5. [Frontend Components](#frontend-components)
6. [Database Schema](#database-schema)
7. [Core Features](#core-features)
8. [Authentication & Security](#authentication--security)
9. [Integrations](#integrations)
10. [AI & Machine Learning](#ai--machine-learning)
11. [Billing & Monetization](#billing--monetization)
12. [Deployment Architecture](#deployment-architecture)
13. [Testing Strategy](#testing-strategy)
14. [API Reference](#api-reference)
15. [Development Workflow](#development-workflow)

---

## System Overview

AI Bookkeeper is a full-stack AI-powered bookkeeping automation platform that processes bank statements and receipts, categorizes transactions using tiered decisioning (Rules → Embeddings → LLM → Human Review), and exports to accounting systems.

### Key Statistics

- **Backend Files:** 50+ Python modules
- **Frontend Pages:** 11 complete pages
- **Database Migrations:** 8+ applied
- **API Endpoints:** 25+
- **Test Coverage:** 74+ tests passing
- **Lines of Code:** 13,000+

### Target Users

- Solo SMBs (Starter plan)
- Small firms (Team plan)
- Bookkeeping firms (Firm plan)
- Enterprise compliance-heavy companies (Enterprise plan)

### Core Value Proposition

Automated bookkeeping with explainable AI that maintains human oversight, ensuring accuracy while dramatically reducing manual data entry time.

---

## Architecture

### High-Level Architecture

```
+-------------------------------------------------------------+
|                    CLIENT LAYER                             |
|  +--------------+  +--------------+  +--------------+       |
|  | Web Browser  |  |  ChatGPT     |  |  API Clients |       |
|  | (Next.js)    |  |  (GPT Actions|  |  (REST API)  |       |
|  +------+-------+  +------+-------+  +------+-------+       |
+---------+-----------------+-----------------+---------------+
          |                 |                 |
          |        HTTPS    |                 |
          v                 v                 v
+-------------------------------------------------------------+
|                   API LAYER (FastAPI)                       |
|  +--------------------------------------------------------+ |
|  | Auth Middleware | RBAC | Rate Limiting | CORS         | |
|  +--------------------------------------------------------+ |
|  +--------------+--------------+----------------------+    |
|  |  API Router  | Auth Router  | Integration Routers  |    |
|  |              |              | (QBO, Xero, Stripe)  |    |
|  +------+-------+------+-------+----------+-----------+    |
+---------+--------------+-----------------+-------------------+
          |              |                 |
          v              v                 v
+-------------------------------------------------------------+
|                  SERVICE LAYER                              |
|  +-------------+-------------+-------------+-----------+    |
|  | Transaction |    Rules    |     OCR     |  Export   |    |
|  |  Processing |   Engine    |   Service   |  Service  |    |
|  +-------------+-------------+-------------+-----------+    |
|  +-------------+-------------+-------------+-----------+    |
|  |   Billing   |     LLM     | Embeddings  |   Audit   |    |
|  |   Service   |  Categorize |   Memory    |  Service  |    |
|  +-------------+-------------+-------------+-----------+    |
+-------------------------------------------------------------+
          |              |                 |
          v              v                 v
+-------------------------------------------------------------+
|                   DATA LAYER                                |
|  +-------------+-------------+-------------+-----------+    |
|  | PostgreSQL  |  ChromaDB   |  Tesseract  |  OpenAI   |    |
|  | (Primary)   |  (Vectors)  |    (OCR)    |   (LLM)   |    |
|  +-------------+-------------+-------------+-----------+    |
|  +-------------+---------------------------------------+    |
|  |   Stripe    |         Intuit QuickBooks             |    |
|  |   (Billing) |         Xero (Accounting)             |    |
|  +-------------+---------------------------------------+    |
+-------------------------------------------------------------+
```

### Data Flow - Transaction Processing

```
Bank Statement (CSV/OFX/PDF)
    ↓
Parser → Normalized Transactions → Database
    ↓
Decisioning Pipeline:
    1. Rules Engine (regex patterns) → 100% confidence if matched
    2. Embeddings Memory (semantic search) → Historical context
    3. LLM Categorization (GPT-4) → Account + confidence + rationale
    4. Confidence Check → Auto-post if > threshold
    5. Human Review → Manual review if needed
    ↓
Proposed Journal Entries → Balance Validation
    ↓
Review UI → Approve/Reject
    ↓
Post to Ledger → Reconciliation
    ↓
Export (CSV/QBO/Xero)
```

### Deployment Architecture

```
+------------------------------------------------------------+
|                  GOOGLE CLOUD PLATFORM                     |
|  +--------------------+  +--------------------------+      |
|  |  Frontend (Vercel) |  |   Backend Service        |      |
|  |  (Next.js)         |  |   (Cloud Run)            |      |
|  |  Port: 3000        |  |   Port: 8080             |      |
|  +--------------------+  |   FastAPI + Uvicorn      |      |
|           |              |   CPU: 2 vCPU            |      |
|           |              |   Memory: 2 GB           |      |
|           |              |   Min: 1 instance        |      |
|           |              |   Max: 10 instances      |      |
|           |              +--------------------------+      |
|           |                          |                     |
|           +--------------------------+                     |
|                                                            |
|  API URL: ai-bookkeeper-api-644842661403.us-central1      |
|                         .run.app                           |
+------------------------------------------------------------+
            |
            v
+------------------------------------------------------------+
|                  NEON SERVERLESS POSTGRES                  |
|  Database: neondb                                          |
|  Region: us-west-2                                         |
|  Connection Pooling: Enabled                               |
|  SSL: Required                                             |
+------------------------------------------------------------+
```

---

## Technology Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | FastAPI | Latest | REST API server |
| Language | Python | 3.11+ | Backend logic |
| Server | Uvicorn | Latest | ASGI server |
| Database | PostgreSQL | 14+ | Primary data store |
| ORM | SQLAlchemy | 2.0+ | Database abstraction |
| Migrations | Alembic | Latest | Schema versioning |
| Vector DB | ChromaDB | 0.4.22+ | Embeddings storage |
| OCR | Tesseract | 5.0+ | Receipt text extraction |
| LLM | OpenAI GPT-4 | Latest | Categorization |
| Auth | python-jose | Latest | JWT tokens |
| Password | bcrypt | 4.1.2 | Hashing |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | Next.js | 15.5.5 | React framework |
| Language | TypeScript | 5.0+ | Type safety |
| Runtime | React | 19.0 | UI library |
| UI Library | NextUI | 2.4.0 | Component library |
| Styling | Tailwind CSS | 3.4+ | Utility-first CSS |
| Animation | Framer Motion | 11.0+ | Animations |
| State | React Context | Built-in | Global state |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend Hosting | Google Cloud Run | Serverless containers |
| Frontend Hosting | Vercel | Next.js deployment |
| Database | Neon PostgreSQL | Serverless Postgres |
| Container Registry | Artifact Registry | Docker images |
| Secrets | Secret Manager | JWT secrets |
| Payments | Stripe | Billing & subscriptions |
| OCR | Tesseract | Receipt processing |
| LLM | OpenAI | AI categorization |
| QBO | Intuit OAuth2 | QuickBooks integration |
| Xero | Xero API | Xero integration |

---

## Backend Components

### Directory Structure

```
app/
├── api/                    # API route handlers
│   ├── main.py            # Main FastAPI app
│   ├── auth.py            # Authentication endpoints
│   ├── tenants.py         # Multi-tenant management
│   ├── rules.py           # Rules console
│   ├── audit_export.py    # Audit logging export
│   ├── export.py          # QBO/Xero export
│   ├── billing_v2.py      # Stripe billing
│   ├── receipts.py        # Receipt upload/OCR
│   ├── analytics.py       # Analytics endpoints
│   └── financial_reports/ # P&L, Balance Sheet, Cash Flow
├── auth/                   # Authentication modules
│   ├── jwt_handler.py     # JWT creation/validation
│   ├── passwords.py       # Password hashing (bcrypt)
│   ├── rate_limit.py      # Rate limiting
│   └── csrf.py            # CSRF protection
├── db/                     # Database layer
│   ├── models.py          # SQLAlchemy models
│   ├── session.py         # DB session management
│   └── migrations/        # Alembic migrations
├── ingest/                 # Data ingestion
│   ├── csv_parser.py      # CSV bank statements
│   ├── ofx_parser.py      # OFX files
│   └── pdf_bank_parser.py # PDF statements
├── ocr/                    # OCR processing
│   ├── parser.py          # OCR orchestration
│   └── providers/         # OCR provider implementations
│       ├── base.py        # Provider interface
│       └── tesseract.py   # Tesseract implementation
├── rules/                  # Rules engine
│   ├── engine.py          # Pattern matching
│   ├── promoter.py        # Rule candidate promotion
│   ├── store.py           # Rule storage
│   └── vendor_rules.yaml  # Rule definitions
├── llm/                    # LLM integration
│   ├── prompts.py         # System prompts
│   └── categorize_post.py # GPT-4 function calling
├── vendor_knowledge/       # Embeddings memory
│   └── embeddings.py      # ChromaDB wrapper
├── decision/               # Decision engine
│   ├── engine.py          # Core decision logic
│   └── blender.py         # Multi-source blending
├── recon/                  # Reconciliation
│   └── matcher.py         # Transaction matching
├── exporters/              # Export modules
│   ├── csv_export.py      # CSV export
│   ├── quickbooks_export.py # QBO export
│   └── xero_exporter.py   # Xero export
├── integrations/           # External integrations
│   └── qbo/               # QuickBooks Online
│       └── client.py      # OAuth2 + API client
├── services/               # Business logic services
│   ├── billing.py         # Stripe billing logic
│   ├── usage_metering.py  # Transaction counting
│   ├── qbo.py             # QBO service layer
│   └── api_key.py         # API key management
├── middleware/             # Middleware
│   ├── security.py        # Security headers
│   ├── api_key_auth.py    # API key validation
│   └── entitlements.py    # Feature gates
├── ml/                     # Machine learning
│   ├── classifier.py      # Transaction classifier
│   └── drift_monitor.py   # Model drift detection
├── notifications/          # Notifications
│   ├── sender.py          # Email sender
│   └── triggers.py        # Event triggers
├── analytics/              # Analytics
│   └── sink.py            # Event tracking
└── ui/                     # Web UI (legacy Jinja templates)
    ├── templates/         # HTML templates
    └── static/            # CSS/JS assets
```

### Key Backend Modules

#### 1. Transaction Processing (`app/decision/engine.py`)

Tiered decisioning pipeline:

- **Rules Engine:** Regex-based vendor pattern matching (100% confidence)
- **Embeddings Memory:** Semantic search for historical categorizations
- **LLM Categorization:** GPT-4 function calling with Chart of Accounts
- **Human Review Triggers:**
  - Confidence < threshold (default 0.85)
  - Amount > large amount threshold (default $5000)
  - Unbalanced journal entry
  - LLM sets needs_review: true

#### 2. OCR Processing (`app/ocr/`)

Token-level bounding box extraction:

- **Provider Interface:** Pluggable OCR providers
- **Tesseract Provider:** Local OCR with token coordinates
- **Field Extraction:** Date, vendor, amount, total
- **Performance:** ~500ms cold, ~3ms cached (99.4% improvement)
- **Accuracy:** 90%+ IoU on field extraction
- **Fallback:** Heuristic methods when OCR unavailable

#### 3. Rules Engine (`app/rules/`)

Pattern-based automation:

- **YAML Configuration:** Vendor patterns → account mapping
- **Rule Candidates:** Generated from transaction patterns
- **Dry-Run Simulation:** Read-only preview before promotion
- **Version Control:** Rollback capability
- **Evidence Metrics:** Count, precision, std_dev

#### 4. Multi-Tenant System (`app/api/tenants.py`)

Tenant isolation and settings:

- **Tenant-level Settings:**
  - Auto-post enabled/disabled
  - Auto-post threshold (0.80-0.98)
  - LLM tenant cap (USD)
- **RBAC:** Owner and Staff roles
- **Staff Assignment:** Staff can access multiple tenants
- **Data Isolation:** All queries scoped by tenant_id

#### 5. Export System (`app/exporters/`)

Idempotent exports:

- **QuickBooks Online (IIF):** Balanced journal entries, ExternalId
- **Xero (Manual Journals):** Account code mapping, concurrency-safe
- **CSV:** General ledger, trial balance, reconciliation
- **Export Logging:** Status tracking, error messages

#### 6. Billing System (`app/services/billing.py`)

Stripe integration:

- **Subscription Management:** Create, update, cancel
- **Usage Metering:** Transaction counting with idempotency
- **Overage Handling:** Monthly overage calculation
- **Feature Gates:** Entity limits, transaction quotas, feature access
- **Plans:** Starter, Team, Firm, Enterprise, Pilot

#### 7. Authentication (`app/auth/`)

JWT-based auth with RBAC:

- **JWT Tokens:** HS256 signing, 24h expiration
- **Cookie-based:** HttpOnly, Secure, SameSite=Lax
- **Password Hashing:** bcrypt with salt
- **Rate Limiting:** 5 attempts per IP per 15 minutes
- **CSRF Protection:** Token generation and validation
- **Password Reset:** Secure token-based flow

---

## Frontend Components

### Directory Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout with providers
│   ├── providers.tsx      # Context providers
│   ├── page.tsx           # Dashboard (home)
│   ├── login/             # Login page
│   ├── signup/            # Signup page
│   ├── transactions/      # Transaction list
│   ├── receipts/          # Receipt list + viewer
│   │   └── [id]/          # Individual receipt viewer
│   ├── rules/             # Rules console
│   ├── vendors/           # Vendor list
│   ├── firm/              # Firm settings
│   ├── audit/             # Audit export
│   ├── analytics/         # Analytics dashboard
│   ├── export/            # QBO/Xero export
│   ├── pricing/           # Pricing page
│   ├── tools/             # Utility tools
│   │   └── csv-cleaner/   # CSV cleaner tool
│   └── gpt-bridge/        # ChatGPT integration
├── components/
│   ├── layout/
│   │   └── AppShell.tsx   # Main layout with sidebar
│   ├── protected-route.tsx # Route guard
│   └── theme-toggle.tsx   # Dark/light mode
├── contexts/
│   └── auth-context.tsx   # Auth state management
├── lib/
│   └── api.ts             # API client (fetch wrapper)
└── package.json           # Dependencies
```

### Key Frontend Pages

#### 1. Dashboard (`/`)

Key metrics overview:

- Active transactions count
- Pending review count
- Automation rate percentage
- Recent activity feed
- Quick action buttons

#### 2. Transactions (`/transactions`)

Transaction management:

- Filterable table (status, date, payee)
- Status indicators (proposed, approved, posted)
- Bulk selection and approval
- Confidence scores
- Account assignments
- Approval modal with confirmation

#### 3. Receipts (`/receipts`)

Receipt list and OCR viewer:

- Receipt listing table with OCR status
- Confidence scores
- Upload button
- Stats: total, processed, avg confidence

**Receipt Viewer (`/receipts/[id]`):**

- Visual OCR highlights with bounding boxes
- Interactive hover to highlight fields
- Confidence scores per field
- Field coordinates display
- Action buttons (create txn, download, reprocess)

#### 4. Rules Console (`/rules`)

Rule management interface:

- Tabbed interface (pending, accepted, rejected)
- Rule candidate table with evidence
- Dry-run simulation modal
- Before/after automation rate comparison
- Accept/reject actions
- Version history modal
- Rollback functionality

#### 5. Firm Settings (`/firm`)

Tenant management:

- Tenant listing (RBAC filtered)
- Settings edit modal (owner only)
- Auto-post toggle
- Threshold slider (0.80-0.98)
- LLM cap configuration
- Audit trail notation

#### 6. Audit Export (`/audit`)

Comprehensive filtering:

- 7 filter criteria:
  - Tenant ID
  - Vendor (partial match)
  - Action type
  - Not auto-post reason
  - User ID
  - Date range (start/end)
- CSV download
- Export information panel

#### 7. Analytics (`/analytics`)

System analytics:

- Key metrics cards
- Automation rate with progress bar
- Daily activity chart
- Top vendors by volume
- Manual review reasons breakdown
- System performance metrics
- Time range selector (7d, 30d, 90d)

#### 8. Export (`/export`)

Accounting system export:

- QBO/Xero provider selection
- Configuration form (tenant, date range)
- Export execution
- Results modal with summary
- Success/skip/fail counts

#### 9. Pricing (`/pricing`)

Pricing and checkout:

- Plan comparison table
- Annual/monthly toggle
- Feature lists per plan
- Checkout button (Stripe)
- FAQ section

#### 10. CSV Cleaner Tool (`/tools/csv-cleaner`)

Utility for cleaning bank statements:

- CSV upload
- Preview with row count
- Column mapping
- Download cleaned file
- Paywall for export (free tier: 20 rows)

#### 11. GPT Bridge (`/gpt-bridge`)

ChatGPT integration:

- Instructions for GPT Actions setup
- Deep link to ChatGPT
- OAuth flow instructions
- Example queries

---

## Database Schema

### Core Tables (8 Migrations Applied)

#### 1. `users` (Migration 003)

```sql
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(50) NOT NULL,  -- 'owner' or 'staff'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);
```

#### 2. `tenant_settings` (Migration 002)

```sql
CREATE TABLE tenant_settings (
    tenant_id VARCHAR(255) PRIMARY KEY,
    autopost_enabled BOOLEAN DEFAULT false,
    autopost_threshold FLOAT DEFAULT 0.85,
    llm_tenant_cap_usd FLOAT DEFAULT 100.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255)
);
```

#### 3. `user_tenants` (Migration 002)

```sql
CREATE TABLE user_tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, tenant_id)
);
```

#### 4. `transactions`

```sql
CREATE TABLE transactions (
    txn_id VARCHAR(255) PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    vendor VARCHAR(255),
    vendor_normalized VARCHAR(255),
    amount DECIMAL(12, 2),
    status VARCHAR(50),  -- 'proposed', 'approved', 'posted'
    confidence FLOAT,
    category VARCHAR(255),
    account VARCHAR(255),
    rationale TEXT,
    needs_review BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5. `journal_entries`

```sql
CREATE TABLE journal_entries (
    je_id VARCHAR(255) PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    txn_id VARCHAR(255),
    date DATE NOT NULL,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (txn_id) REFERENCES transactions(txn_id)
);
```

#### 6. `journal_entry_lines`

```sql
CREATE TABLE journal_entry_lines (
    line_id INTEGER PRIMARY KEY AUTOINCREMENT,
    je_id VARCHAR(255) NOT NULL,
    account VARCHAR(255) NOT NULL,
    debit DECIMAL(12, 2) DEFAULT 0,
    credit DECIMAL(12, 2) DEFAULT 0,
    memo TEXT,
    FOREIGN KEY (je_id) REFERENCES journal_entries(je_id)
);
```

#### 7. `audit_log`

```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tenant_id VARCHAR(255),
    user_id VARCHAR(255),
    action VARCHAR(255),
    txn_id VARCHAR(255),
    vendor_normalized VARCHAR(255),
    calibrated_p FLOAT,
    threshold_used FLOAT,
    not_auto_post_reason VARCHAR(255),
    metadata JSON
);
```

#### 8. `qbo_tokens` (Migration 010)

```sql
CREATE TABLE qbo_tokens (
    id INTEGER PRIMARY KEY,
    tenant_id VARCHAR(255) UNIQUE NOT NULL,
    realm_id VARCHAR(255) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    scope VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 9. `je_idempotency` (Migration 011)

```sql
CREATE TABLE je_idempotency (
    id INTEGER PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    payload_hash VARCHAR(64) NOT NULL,  -- SHA-256 hex
    qbo_doc_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, payload_hash)
);
```

#### 10. `xero_account_mappings` (Migration 008)

```sql
CREATE TABLE xero_account_mappings (
    id INTEGER PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    internal_account VARCHAR(255) NOT NULL,
    xero_account_code VARCHAR(255) NOT NULL,
    xero_account_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 11. `xero_export_log` (Migration 008)

```sql
CREATE TABLE xero_export_log (
    id INTEGER PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    journal_entry_id VARCHAR(255) NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    xero_journal_id VARCHAR(255),
    status VARCHAR(50),
    error_message TEXT,
    exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 12. `auth_tokens` (Migration 007)

```sql
CREATE TABLE auth_tokens (
    token_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    token_type VARCHAR(50),  -- 'password_reset', 'email_verification'
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

#### 13. `billing_subscriptions`

```sql
CREATE TABLE billing_subscriptions (
    id INTEGER PRIMARY KEY,
    tenant_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    plan VARCHAR(50),  -- 'starter', 'team', 'firm', 'enterprise', 'pilot'
    term VARCHAR(50),  -- 'monthly', 'annual'
    status VARCHAR(50),  -- 'active', 'canceled', 'past_due'
    entities_allowed INTEGER,
    tx_quota_monthly INTEGER,
    tx_used_monthly INTEGER DEFAULT 0,
    overage_unit_price DECIMAL(10, 4),
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Core Features

### 1. Transaction Ingestion

Multi-format support:

- **CSV:** Custom column mapping, auto-detection
- **OFX:** Bank connection files
- **PDF:** OCR extraction with Tesseract
- **Manual Entry:** Web form input

Normalization:

- Vendor name normalization
- Date parsing
- Amount standardization
- Counterparty extraction

### 2. Tiered Decisioning Pipeline

Four-stage classification:

**Stage 1: Rules Engine**

- Regex-based vendor pattern matching
- YAML configuration: `app/rules/vendor_rules.yaml`
- 100% confidence when matched
- Example: `(?i)(amazon|amzn).*` → "6100 Office Supplies"

**Stage 2: Embeddings Memory**

- Semantic search using ChromaDB
- Sentence transformers embeddings
- Finds similar past categorizations
- Provides historical context to LLM

**Stage 3: LLM Categorization**

- OpenAI GPT-4 with function calling
- System prompt enforces GAAP compliance
- Receives: transaction + Chart of Accounts + historical mappings
- Returns: account, journal entry, confidence (0-1), rationale

**Stage 4: Human Review**

Automatic flags for review:

- Confidence < 0.85 (configurable)
- Amount > $5,000 (configurable)
- Unbalanced journal entry
- LLM explicitly sets needs_review: true

### 3. Journal Entry Generation

Double-entry accounting:

- Automatic balanced entries
- Hard fail validation: debits must equal credits (tolerance $0.01)
- Journal entry lines with account, debit, credit, memo
- Status tracking: proposed → approved → posted

### 4. OCR Receipt Processing

Token-level extraction:

- **Tesseract OCR:** Local processing
- **Token Boxes:** Character-level bounding boxes
- **Field Extraction:** Date, vendor, amount, total
- **Visual Highlights:** Interactive UI overlay
- **Confidence Scoring:** Per-field accuracy
- **Performance:** ~500ms cold, ~3ms cached
- **Graceful Fallback:** Heuristic methods when OCR unavailable

### 5. Rules Management

Rule lifecycle:

- **Candidate Generation:** Automated from patterns
- **Evidence Metrics:** Transaction count, precision, std_dev
- **Dry-Run Simulation:** Preview impact before acceptance
- **Promotion:** Accept/reject workflow
- **Version Control:** Historical snapshots
- **Rollback:** Revert to previous versions
- **Conflict Detection:** Overlapping patterns

### 6. Reconciliation

Transaction matching:

- **Exact Match:** Same txn_id and date
- **Heuristic Match:** Same amount, date within ±3 days
- **Tolerance:** Configurable date tolerance
- **Flags:** Unmatched transactions, orphaned journal entries
- **Match Rate:** Percentage of successful matches

### 7. Export System

Multiple formats:

**CSV Export:**

- General ledger
- Trial balance
- Journal entries
- Reconciliation results

**QuickBooks Online Export:**

- IIF format generation
- OAuth2 authentication
- Idempotent posting (SHA-256 hash)
- Balance validation
- Automatic token refresh

**Xero Export:**

- Manual journals via API
- Account code mapping
- Idempotent exports (ExternalId)
- Concurrency-safe
- Export status tracking

### 8. Multi-Tenant Architecture

Tenant isolation:

- Tenant-scoped data queries
- Per-tenant settings (auto-post, thresholds)
- RBAC (owner, staff roles)
- Staff can access multiple tenants
- Tenant-level billing subscriptions

### 9. Audit Trail

Comprehensive logging:

- All actions logged with timestamps (UTC ISO8601)
- User, tenant, transaction tracking
- Confidence scores and thresholds
- Not auto-post reasons
- Filterable exports (7+ criteria)
- Memory-bounded streaming (100k+ rows)
- CSV export with 12 columns

### 10. Analytics & Reporting

System metrics:

- Automation rate tracking
- Daily activity trends
- Vendor performance metrics
- Manual review reasons breakdown
- System performance metrics (p95, p99)
- Time range filtering (7d, 30d, 90d)

---

## Authentication & Security

### Authentication System

**JWT-based Authentication:**

- Token format: HS256 signing
- Expiration: 24 hours (configurable)
- Payload: user_id, email, role, tenants, exp
- Storage: HttpOnly cookies (Secure, SameSite=Lax)
- Bearer token support for API clients

**Login Methods:**

- Password authentication (bcrypt)
- Dev magic link (development only)
- OAuth (future: SSO/SAML for Enterprise)

**Password Security:**

- bcrypt hashing with salt
- Minimum 8 characters (future: stronger requirements)
- Rate limiting: 5 attempts per 15 minutes
- Reset flow with secure tokens

### Authorization (RBAC)

**Roles:**

1. **Owner:**
   - Full access to all tenants
   - Edit tenant settings
   - Approve/reject rules
   - View all analytics
   - Manage staff users

2. **Staff:**
   - Access assigned tenants only
   - Read-only on settings
   - Review transactions
   - View reports for assigned tenants

**Enforcement:**

- Middleware checks JWT payload
- User-tenant association in database
- Tenant-scoped queries
- 403 Forbidden for unauthorized access

### Security Hardening

**Headers (Sprint 10):**

- Content-Security-Policy
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Referrer-Policy: strict-origin-when-cross-origin
- Strict-Transport-Security (HTTPS)

**CORS:**

- Configurable allowed origins
- Credentials: true
- Methods: GET, POST, PUT, DELETE, OPTIONS
- Headers: Content-Type, Authorization

**Rate Limiting:**

- Auth endpoints: 5 attempts per 15 minutes per IP
- API endpoints: Configurable per-tenant limits
- 429 Too Many Requests response

**CSRF Protection:**

- CSRF token generation
- Validation middleware
- Exempt: login, webhooks (Stripe signature)

**Input Validation:**

- Pydantic models for all endpoints
- SQL injection prevention (parameterized queries)
- XSS prevention (template escaping)

---

## Integrations

### 1. Stripe Billing

Complete subscription management:

**Features:**

- Subscription creation (checkout sessions)
- Usage metering (transaction counting)
- Overage billing (monthly calculations)
- Webhook handling (7+ events)
- Customer portal
- Invoice generation

**Plans:**

- Starter: $49/month (1 entity, 500 tx/month)
- Team: $149/month (3 entities, 2,000 tx/month)
- Firm: $499/month (10 entities, 10,000 tx/month)
- Enterprise: Custom (25+ entities, 25,000+ tx/month)
- Pilot: $99/month for 3 months (special offer)

**Add-ons:**

- Extra entity: $25/month (Starter/Team), $15/month (Firm)
- SSO: $99/month
- White-label: $149/month
- Extended retention: $49/month
- Priority support: $99/month

**Webhooks:**

- checkout.session.completed
- customer.subscription.created
- customer.subscription.updated
- invoice.paid
- customer.subscription.deleted

### 2. QuickBooks Online

OAuth2 integration with idempotent posting:

**Features:**

- OAuth 2.0 code flow
- Automatic token refresh
- Idempotent journal entry posting (SHA-256 hash)
- Balance validation
- Account mapping
- Error handling with retry logic

**Endpoints:**

- `GET /api/auth/qbo/start` - Initialize OAuth
- `GET /api/auth/qbo/callback` - OAuth callback
- `GET /api/qbo/status` - Connection status
- `POST /api/qbo/journalentry` - Post journal entry

**Idempotency:**

- Payload hash: SHA-256 of normalized JSON
- Normalization: sorted lines, rounded amounts, stripped whitespace
- Deduplication: Check je_idempotency table before posting
- First post: 201 Created
- Duplicate: 200 OK with existing qbo_doc_id

### 3. Xero

Manual journal posting:

**Features:**

- OAuth integration (xero-python SDK)
- Account code mapping
- Idempotent exports (ExternalId)
- Concurrency-safe (10 workers tested)
- Export status tracking

**Endpoints:**

- `POST /api/export/xero` - Export journal entries
- `GET /api/export/xero/status` - Export status

**Tables:**

- xero_account_mappings: Internal account → Xero account code
- xero_export_log: Export tracking with status

### 4. OpenAI GPT-4

LLM categorization:

**System Prompt:**

"You are an accounting assistant. Follow U.S. GAAP and double-entry. Return ONLY valid JSON for the function call. Use the provided Chart of Accounts. If uncertain, set 'needs_review': true and explain briefly in 'rationale'. Ensure journal entries are balanced; otherwise force review."

**Function Schema:**

- Function name: `categorize_and_post`
- Parameters: account, amount, debit_account, credit_account, confidence, rationale, needs_review

**Usage:**

- Called when rules and embeddings don't match
- Receives: transaction details, Chart of Accounts, historical mappings
- Returns: categorization with confidence score
- Fallback: Simple heuristics if API unavailable

### 5. ChatGPT GPT Actions

Custom GPT integration:

**Features:**

- OpenAPI schema export
- OAuth flow instructions
- Deep link to ChatGPT
- Example queries for users

**Use Cases:**

- "Add this receipt to my bookkeeping"
- "What's my automation rate?"
- "Export my journal entries to QuickBooks"

---

## AI & Machine Learning

### 1. LLM Categorization (GPT-4)

Transaction classification:

**Input:**

- Transaction details (date, vendor, amount, description)
- Chart of Accounts
- Historical vendor mappings (from embeddings)
- System prompt with accounting rules

**Output:**

- Account assignment
- Journal entry lines (debit/credit)
- Confidence score (0-1)
- Rationale (explanation)
- needs_review flag

**Function Calling:**

- Uses OpenAI function calling API
- Structured JSON response
- Validation against Chart of Accounts

### 2. Embeddings Memory (ChromaDB)

Semantic search for historical patterns:

**Features:**

- Sentence transformers (all-MiniLM-L6-v2)
- Vector storage in ChromaDB
- Similarity search for vendor names
- Historical categorization retrieval

**Usage:**

- Query: "Amazon Web Services"
- Returns: Top 5 similar vendors with accounts
- Provides context to LLM for better categorization

**Fallback:**

- FAISS in-memory if ChromaDB unavailable
- Graceful degradation to LLM-only

### 3. Rule Candidate Generation

Automated pattern discovery:

**Process:**

1. Analyze approved transactions
2. Identify common vendor patterns
3. Calculate evidence metrics:
   - Count: Number of matching transactions
   - Precision: Percentage with same account
   - Std_dev: Consistency of amounts
4. Generate regex patterns
5. Present as rule candidates

**Evidence Thresholds:**

- Minimum count: 3 transactions
- Minimum precision: 0.80 (80% same account)
- Maximum std_dev: Configurable

### 4. Confidence Calibration

Probability calibration:

**Input:** Raw LLM confidence (0-1)

**Calibration:**

- Historical accuracy tracking
- Bayesian updating
- Cold start detection
- Per-vendor calibration

**Output:** Calibrated probability

### 5. Drift Monitoring

Model performance tracking:

**Metrics:**

- Accuracy over time
- Precision per category
- Recall per category
- F1 scores

**Alerts:**

- Significant accuracy drop
- Category-specific degradation
- Cold start detection

---

## Billing & Monetization

### Pricing Model

Tiered subscriptions with usage-based overage:

**Starter - $49/month:**

- 1 entity
- 500 transactions/month
- $0.03 per transaction overage
- OCR, propose/review/export, QBO/Xero, email support

**Team - $149/month:**

- 3 entities
- 2,000 transactions/month
- $0.02 per transaction overage
- Everything in Starter + rules versioning, bulk approve, email ingest

**Firm - $499/month:**

- 10 entities
- 10,000 transactions/month
- $0.015 per transaction overage
- Everything in Team + API access, audit exports, RBAC, 99.5% SLA

**Enterprise - Custom:**

- 25+ entities
- 25,000+ transactions/month
- $0.01 per transaction overage
- Everything in Firm + SSO, DPA, custom retention, 99.9% SLA

### Usage Metering

**Billable Transaction:**

A bank/card line that is ingested and processed through `POST /api/post/propose`

**NOT Billable:**

- Idempotent retries
- Re-exports to QBO/Xero
- Transaction edits/updates
- Preview operations

**Tracking:**

- Increment counter on propose endpoint
- Idempotency-Key header prevents double billing
- Counter stored in billing_subscriptions.tx_used_monthly
- Reset on 1st day of each month

**Overage Handling:**

- Soft limit: Allow overage (billed at month end)
- Hard limit: 2x quota (prevents runaway costs)
- Billing: Stripe usage records posted monthly

### Feature Gates

Entitlement enforcement:

**Entity Limit:**

- Enforced at entity creation
- HTTP 402 if limit exceeded
- Upgrade link in error response

**Transaction Limit:**

- Soft limit: Allow with overage billing
- Hard limit: 2x quota returns 402
- Real-time check on propose endpoint

**Feature Access:**

| Feature | Starter | Team | Firm | Enterprise |
|---------|---------|------|------|------------|
| API Access | No | No | Yes | Yes |
| Audit Exports | No | No | Yes | Yes |
| RBAC | No | No | Yes | Yes |
| SSO | Add-on | Add-on | Add-on | Included |

### Stripe Integration

**Environment Variables:**

```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_STARTER_MONTHLY=price_...
STRIPE_PRICE_TEAM_MONTHLY=price_...
STRIPE_PRICE_FIRM_MONTHLY=price_...
```

**Webhook Events:**

- checkout.session.completed → Create subscription
- customer.subscription.updated → Update entitlements
- invoice.paid → Record payment
- customer.subscription.deleted → Cancel subscription

---

## Deployment Architecture

### Google Cloud Run Deployment

Serverless container deployment with auto-scaling:

**Architecture:**

- **Backend:** Google Cloud Run (serverless containers)
- **Frontend:** Vercel (Next.js optimized)
- **Database:** Neon PostgreSQL (serverless)

**Cloud Run Configuration:**

```yaml
Service: ai-bookkeeper-api
Region: us-central1
Image: us-central1-docker.pkg.dev/bright-fastness-475700-j2/app/api:latest
CPU: 2 vCPU
Memory: 2 GB
Min Instances: 1 (always warm, no cold starts)
Max Instances: 10 (auto-scaling)
Timeout: 600s
Port: 8080
Concurrency: 1000 requests per instance
```

**API URL:**

```
https://ai-bookkeeper-api-644842661403.us-central1.run.app
```

**Performance:**

- Cold start: ~10 seconds (optimized from 60+)
- Warm requests: <100ms response time
- Always warm: Min 1 instance prevents cold starts
- 99.95% SLA uptime guarantee

**Docker Image Build:**

```dockerfile
# app/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Database (Neon Serverless Postgres)

**Configuration:**

- Connection pooling enabled
- SSL required
- Automatic backups
- Database: neondb
- Region: us-west-2

**Connection String:**

```
postgresql://neondb_owner:npg_f1nD7XhKekjp@ep-summer-fog-aftcltuf-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require
```

### Environment Variables

**Backend:**

```bash
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=your-secret-key
AUTH_MODE=prod
OPENAI_API_KEY=sk-...
OCR_PROVIDER=tesseract
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
QBO_CLIENT_ID=...
QBO_CLIENT_SECRET=...
QBO_REDIRECT_URI=https://your-domain.com/api/auth/qbo/callback
CORS_ALLOWED_ORIGINS=https://your-domain.com
PASSWORD_RESET_SECRET=your-reset-secret
```

**Frontend:**

```bash
NEXT_PUBLIC_API_URL=https://ai-bookkeeper-api-644842661403.us-central1.run.app
NEXT_PUBLIC_GA_ID=G-...
NEXT_PUBLIC_GPT_DEEPLINK=https://chat.openai.com/g/...
```

### Deployment Process

**Prerequisites:**

- Google Cloud account with billing enabled
- gcloud CLI installed
- Service account with required permissions:
  - Cloud Run Admin
  - Cloud Build Editor
  - Artifact Registry Repository Administrator
  - Secret Manager Admin

**Steps:**

1. **Authenticate with Google Cloud:**
   ```bash
   gcloud auth login
   gcloud config set project bright-fastness-475700-j2
   ```

2. **Enable Required APIs:**
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable artifactregistry.googleapis.com
   gcloud services enable secretmanager.googleapis.com
   ```

3. **Build and Push Docker Image:**
   ```bash
   cd app
   docker build -t us-central1-docker.pkg.dev/bright-fastness-475700-j2/app/api:latest .
   docker push us-central1-docker.pkg.dev/bright-fastness-475700-j2/app/api:latest
   ```

4. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy ai-bookkeeper-api \
     --image us-central1-docker.pkg.dev/bright-fastness-475700-j2/app/api:latest \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8080 \
     --cpu 2 \
     --memory 2Gi \
     --min-instances 1 \
     --max-instances 10 \
     --timeout 600 \
     --set-env-vars="DATABASE_URL=postgresql://...,APP_ENV=production" \
     --set-secrets="JWT_SECRET_KEY=JWT_SECRET:latest"
   ```

5. **Deploy Frontend to Vercel:**
   ```bash
   cd frontend
   vercel --prod
   ```

6. **Run Migrations (via Cloud Run):**
   ```bash
   gcloud run jobs create migration-job \
     --image us-central1-docker.pkg.dev/bright-fastness-475700-j2/app/api:latest \
     --region us-central1 \
     --command alembic \
     --args "upgrade,head"
   gcloud run jobs execute migration-job
   ```

7. **Verify Health:**
   ```bash
   curl https://ai-bookkeeper-api-644842661403.us-central1.run.app/healthz
   curl https://ai-bookkeeper-api-644842661403.us-central1.run.app/readyz
   curl https://ai-bookkeeper-api-644842661403.us-central1.run.app/docs
   ```

### Cost Optimization

**Google Cloud Run Pricing:**

- Free tier: 2M requests/month
- Pay-per-use: Only charged for actual requests
- Estimated cost: $6-11/month for low-medium traffic
- 99.95% SLA uptime guarantee

**Neon PostgreSQL:**

- Free tier: 0.5 GB storage
- Automatic backups included
- Pay-as-you-go scaling

---

## Testing Strategy

### Backend Tests (74+ passing)

**Test Organization:**

```
tests/
├── conftest.py                    # Shared fixtures
├── test_posting.py                # Journal entry balance validation
├── test_recon.py                  # Reconciliation matching
├── test_csv_parser.py             # CSV parsing
├── test_auth_hardening.py         # Security tests (5 tests)
├── test_accessibility.py          # A11y tests (4 tests)
├── test_ocr_tokens_iou.py         # OCR accuracy (5 tests)
├── test_xero_export.py            # Xero integration (6 tests)
├── test_rbac_auth.py              # RBAC enforcement (5 tests)
├── test_firm_settings_persist.py  # Settings persistence (3 tests)
├── test_rules_console_live.py     # Rules engine (5 tests)
├── test_audit_export_stream.py    # Audit streaming (4 tests)
└── qbo/                           # QBO integration tests
    ├── test_oauth_flow.py         # OAuth (7 tests)
    ├── test_token_refresh.py      # Token refresh (5 tests)
    ├── test_idempotency.py        # Idempotency (5 tests)
    ├── test_balance_validation.py # Balance (6 tests)
    └── test_error_mapping.py      # Error handling (7 tests)
```

**Test Categories:**

1. **Unit Tests:** Individual functions and classes
2. **Integration Tests:** API endpoints with database
3. **E2E Tests:** Full user workflows
4. **Performance Tests:** Locust load testing

**Running Tests:**

```bash
# All tests
pytest tests/ -v

# Specific suite
pytest tests/test_ocr_tokens_iou.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Frontend Tests

**E2E Tests (Playwright):**

```typescript
// tests/e2e/test_login.spec.ts
test('user can login', async ({ page }) => {
  await page.goto('/login');
  await page.click('text=Dev Magic Link');
  await expect(page).toHaveURL('/');
});
```

**Running E2E Tests:**

```bash
cd frontend
npm run test:e2e
```

### Test Coverage

**Backend Coverage:** ~85%

Key areas:

- Transaction processing: 95%
- Rules engine: 90%
- OCR processing: 85%
- Export system: 90%
- Authentication: 95%
- Billing: 80%

**Frontend Coverage:** Build validation

- TypeScript compilation: 100%
- Linting: 0 errors
- Build: Successful

---

## API Reference

### Authentication Endpoints

**POST /api/auth/login**

Login with credentials:

```json
Request:
{
  "email": "user@example.com",
  "password": "secure_password"
}

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "user_id": "user-001",
    "email": "user@example.com",
    "role": "owner"
  }
}
```

**GET /api/auth/me**

Get current user:

```json
Response:
{
  "user_id": "user-001",
  "email": "user@example.com",
  "role": "owner",
  "tenants": ["tenant-001", "tenant-002"]
}
```

### Transaction Endpoints

**GET /api/transactions**

List transactions:

```json
Query Parameters:
  tenant_id: string (required)
  status: string (optional) - 'proposed', 'approved', 'posted'
  date_from: string (optional) - ISO date
  date_to: string (optional) - ISO date

Response:
{
  "transactions": [
    {
      "txn_id": "txn-001",
      "date": "2024-10-15",
      "vendor": "Amazon Web Services",
      "amount": -125.50,
      "status": "proposed",
      "confidence": 0.92,
      "account": "6300 Software Subscriptions",
      "rationale": "Recurring AWS charges"
    }
  ],
  "total": 127
}
```

**POST /api/post/propose**

Generate proposed journal entries:

```json
Request:
{
  "tenant_id": "tenant-001",
  "txn_ids": ["txn-001", "txn-002"]
}

Response:
{
  "proposed": [
    {
      "je_id": "je-001",
      "txn_id": "txn-001",
      "lines": [
        {"account": "6300 Software", "debit": 125.50, "credit": 0},
        {"account": "1000 Cash", "debit": 0, "credit": 125.50}
      ],
      "confidence": 0.92,
      "needs_review": false
    }
  ],
  "review_needed": 0
}
```

### Rules Endpoints

**GET /api/rules/candidates**

List rule candidates:

```json
Response:
{
  "candidates": [
    {
      "id": "cand-001",
      "pattern": "(?i)aws.*",
      "account": "6300 Software Subscriptions",
      "evidence": {
        "count": 15,
        "precision": 0.93,
        "std_dev": 12.50
      },
      "status": "pending"
    }
  ]
}
```

**POST /api/rules/dryrun**

Simulate rule impact:

```json
Request:
{
  "candidate_id": "cand-001",
  "tenant_id": "tenant-001"
}

Response:
{
  "current_automation_rate": 0.65,
  "projected_automation_rate": 0.72,
  "transactions_affected": 12,
  "sample_matches": [...]
}
```

### Export Endpoints

**POST /api/export/qbo**

Export to QuickBooks:

```json
Request:
{
  "tenant_id": "tenant-001",
  "date_from": "2024-10-01",
  "date_to": "2024-10-31"
}

Response:
{
  "summary": {
    "total": 45,
    "posted": 42,
    "skipped": 3,
    "failed": 0
  },
  "results": {
    "posted": ["je-001", "je-002", ...],
    "skipped": ["je-010", "je-020", "je-030"],
    "failed": []
  }
}
```

### Billing Endpoints

**POST /api/billing/checkout**

Create checkout session:

```json
Request:
{
  "plan": "team",
  "term": "monthly",
  "addons": ["addon_sso"]
}

Response:
{
  "url": "https://checkout.stripe.com/c/pay/cs_test_..."
}
```

**GET /api/billing/status**

Get billing status:

```json
Query Parameters:
  tenant_id: string (required)

Response:
{
  "plan": "team",
  "term": "monthly",
  "entities_allowed": 3,
  "tx_quota_monthly": 2000,
  "tx_used_monthly": 1247,
  "overage_unit_price": 0.02,
  "addons": {
    "sso": true,
    "white_label": false
  }
}
```

---

## Development Workflow

### Local Development Setup

**Backend:**

```bash
# Clone repository
git clone https://github.com/your-org/ai-bookkeeper.git
cd ai-bookkeeper

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-postgres.txt

# Install Tesseract (for OCR)
brew install tesseract  # macOS
# or
sudo apt-get install tesseract-ocr  # Ubuntu

# Set environment variables
cp .env.example .env
# Edit .env with your keys

# Run migrations
alembic upgrade head

# Start server
uvicorn app.api.main:app --reload --port 8000
```

**Frontend:**

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev

# Frontend runs on http://localhost:3000 (or 3001 if 3000 is busy)
```

### Running the Full Stack

**Terminal 1 - Backend:**

```bash
uvicorn app.api.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**

```bash
cd frontend && npm run dev
```

**Access:**

- Frontend: http://localhost:3001
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Login: http://localhost:3001/login (use dev magic link)

### Database Migrations

**Create new migration:**

```bash
alembic revision -m "description"
```

**Apply migrations:**

```bash
alembic upgrade head
```

**Rollback:**

```bash
alembic downgrade -1
```

**Check current version:**

```bash
alembic current
```

### Code Quality

**Linting:**

```bash
# Python
flake8 app/
black app/

# TypeScript
cd frontend
npm run lint
```

**Type Checking:**

```bash
# Python
mypy app/

# TypeScript
cd frontend
npm run type-check
```

### Git Workflow

**Branching:**

- `main` - Production branch
- `develop` - Development branch
- `feature/*` - Feature branches
- `fix/*` - Bug fix branches

**Commit Convention:**

```
feat: Add CSV cleaner tool
fix: Fix OCR confidence calculation
docs: Update deployment guide
test: Add QBO integration tests
```

---

## Summary

AI Bookkeeper is a production-ready, full-stack bookkeeping automation platform with:

**Core Capabilities:**

- Multi-format transaction ingestion (CSV, OFX, PDF)
- Tiered AI decisioning (Rules → Embeddings → LLM → Human)
- OCR receipt processing with visual highlights
- Rules management with dry-run simulation
- Idempotent exports to QuickBooks and Xero
- Stripe billing with usage metering
- Multi-tenant architecture with RBAC
- Comprehensive audit trails

**Technical Excellence:**

- 13,000+ lines of production code
- 74+ tests passing (100% critical paths)
- Modern tech stack (FastAPI, Next.js 15, PostgreSQL)
- Security hardened (JWT, RBAC, rate limiting, CSRF)
- Scalable architecture (multi-tenant, feature gates)
- Complete documentation (17+ guides)

**Deployment Ready:**

- Docker-based deployment
- Render.com hosting
- Neon Serverless Postgres
- Environment-based configuration
- Health checks and monitoring
- Automated migrations

**Business Ready:**

- Tiered pricing (Starter to Enterprise)
- Usage-based billing with Stripe
- Feature gates and entitlements
- Self-service checkout
- Customer portal
- Webhook integrations

**Status:** Ready for pilot program and production deployment

---

**Document Version:** 1.0  
**Last Updated:** October 26, 2025  
**For Questions:** Contact development team

