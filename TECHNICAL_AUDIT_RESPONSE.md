# AI BOOKKEEPER - TECHNICAL AUDIT RESPONSE
**Date:** $(date '+%Y-%m-%d %H:%M %Z')
**Status:** Current State Assessment
**Context:** No real data this week. Proceed on synthetic data.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## A) REPO & ENVIRONMENT

### Runtime/Tooling
✅ **Python:** 3.13.3
✅ **FastAPI:** 0.115.14
✅ **Pydantic:** 2.11.7
✅ **SQLAlchemy:** (installed)
✅ **Alembic:** 1.16.5
✅ **Pytest:** 8.4.2
⚠️  **Dependency Manager:** pip (requirements.txt) - NOT poetry/uv
⚠️  **Postgres:** Currently using SQLite for dev (no Postgres configured)
⚠️  **Alembic Head:** Need to check migrations state

**Issue:** System is using SQLite instead of PostgreSQL as specified in requirements.

### Health Checks
❌ **Missing /api/healthz endpoint** (found /healthz and /health but not comprehensive)
❌ **Missing /api/readyz endpoint** (no readiness probe)
❌ **No DB connection check in health endpoint**
❌ **No vector store check** (vector backend set to "none")
❌ **No OCR stub check**

**Action Required:** Implement proper health/readiness endpoints with component checks.

### Exact Commands

**Current State:**
\`\`\`bash
# (a) Create DB/migrate
alembic upgrade head

# (b) Seed synthetic data
python3 scripts/simulate_companies.py

# (c) Run tests
pytest tests/ -v

# (d) Start API
python3 -m uvicorn app.api.main:app --reload --port 8000
\`\`\`

**Issues:**
- No single command for full setup
- No documentation on which seed script to use
- No environment validation before startup

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## B) SYNTHETIC DATASET (fixtures)

### Current State
✅ **Tenants:** 6 companies (5 simulated + 1 open_data)
❌ **Transactions per tenant:** 1,902 total ÷ 6 = ~317 per tenant (NOT ~1,200 as required)
✅ **Categories:** 15+ chart of accounts per company
✅ **Vendors:** Power-law distribution via simulate_companies.py
⚠️  **Realistic amounts/dates:** Yes, but need validation

**Gap:** Only ~317 txns/tenant vs required ~1,200 txns/tenant

### Noise Injection
❌ **OCR perturbations:** No evidence of 8% noise injection
❌ **Implementation missing:** No typo/casing/punctuation/spacing injection code found

### Reproducibility
❌ **Random seeds:** Not documented or committed
❌ **Fixture paths:** No tests/fixtures/transactions_*.csv committed
❌ **Receipt files:** 634 receipts in data/simulated_docs/ but not in fixtures/

### Deterministic Labeler
⚠️  **Oracle labeler:** Exists in app/decision/engine.py (hybrid Rules→ML→LLM)
❌ **Stochasticity:** No documented randomness parameters
❌ **Source not isolated:** Mixed with production decision engine

**Action Required:**
1. Generate 2 tenants × 1,200 txns each
2. Add 8% noise injection
3. Commit reproducible seeds
4. Isolate oracle labeler

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## C) EVALUATION & CALIBRATION

### Split Policy
❌ **Time+tenant holdout:** NOT implemented
❌ **Last 30 days per tenant:** No date-based split logic found
❌ **Vendor string leakage prevention:** Not validated

**Current:** Uses random 80/20 split in train_from_open_data.py

### Metrics Produced
⚠️  **Accuracy:** ✅ Logged to ModelTrainingLogDB
⚠️  **Confusion matrices:** ❌ Not generated or saved
⚠️  **Brier score:** ❌ Not computed
⚠️  **ECE bins:** ❌ Not computed
⚠️  **reliability_plot.png:** ❌ Not generated
⚠️  **calibration_bins.json:** ❌ Not saved

**Current output:** Only accuracy, precision, recall, f1 in model_metrics.md

### Calibration Method
❌ **Isotonic regression:** Not implemented
❌ **Temperature scaling:** Not implemented
❌ **Module/function:** No calibration layer exists

**Current:** Raw logistic regression probabilities (uncalibrated)

### Auto-Post Gating
❌ **p≥0.90 enforcement:** NOT in code
⚠️  **Config exists:** AUTO_POST_MIN = 0.90 in settings (Sprint 8)
❌ **Calibrated p in API:** No probability returned in current API responses

**Issue:** Decision blender exists but not connected to transaction endpoints.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## D) DECISION BLENDER, RULES, LONG-TAIL

### Blender Weights
✅ **Defaults:** W_RULES=0.55, W_ML=0.35, W_LLM=0.10
✅ **Config path:** config/settings.py lines 75-77
✅ **Override mechanism:** Environment variables (W_RULES, W_ML, W_LLM)
✅ **Implementation:** app/decision/blender.py (Sprint 8)

**Status:** Implemented but NOT integrated into main transaction flow

### Long-Tail Plan
❌ **top_50_long_tail_errors.csv:** Does NOT exist
❌ **15-25 new rules:** Not documented or generated
❌ **Current rules:** app/rules/vendor_rules.yaml exists but not optimized for long-tail

### Few-Shot Exemplars
❌ **10 LLM exemplars:** Not defined or documented
❌ **Storage:** No exemplars file found

### Versioning
✅ **Rules storage:** app/rules/vendor_rules.yaml
✅ **Version IDs:** rule_versions table exists (Sprint 8)
✅ **Rollback path:** POST /api/rules/rollback implemented

**Gap:** Need to generate long-tail analysis and add targeted rules.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## E) ACTIVE LEARNING

### Uncertainty Sampler
❌ **Threshold 0.45-0.55:** NOT implemented
❌ **Implementation:** No active learning module found
❌ **Blended-score window:** Not configured

### Queue Storage
❌ **Table/collection:** No active_learning_queue table exists
❌ **JSON schema:** Not defined

### Nightly Retrain Job
⚠️  **Scheduled job:** scripts/auto_retrain_v2.py exists (Sprint 7)
❌ **Scheduling:** No cron/scheduler configured
❌ **active_learning_report.json:** Not generated
⚠️  **Delta tracking:** model_retrain_events table exists

**Status:** Auto-retrain infrastructure exists but active learning NOT implemented.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## F) METRICS & COST

### GET /api/metrics/latest
❌ **Endpoint:** Does NOT exist
❌ **Schema:** Not implemented
⚠️  **Partial:** /api/metrics/decision_blend exists but incomplete

**Current state:** No unified metrics endpoint with required schema.

### Determinism Test
❌ **Test fixture:** Not created
❌ **Unit test:** Not implemented

### Cost Guardrail
❌ **≤0.30 LLM calls/txn:** NOT enforced
❌ **Measurement:** No LLM call counter found
❌ **Fallback:** No automatic fallback to Rules/ML-only
⚠️  **Config:** LLM_VALIDATION_ENABLED=False (currently disabled)

**Issue:** LLM cost tracking not implemented.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## G) QBO CSV EXPORT

### Endpoint Spec
⚠️  **Endpoint:** POST /api/export/quickbooks exists
❌ **Idempotent flag:** Not confirmed
❌ **Mapping table:** Not documented
❌ **Retry logic:** Not confirmed

### CSV Columns
❌ **Proposed columns:** Not documented
❌ **Validation:** No column spec in code
⚠️  **Current export:** Generic CSV export exists (app/exporters/csv_export.py)

**Proposed columns (to implement):**
Date, JournalNumber, AccountName, Debit, Credit, Memo, Entity, Class, Location, ExternalId

### Idempotency
❌ **ExternalId hash:** Not implemented
❌ **Duplicate detection:** Not confirmed
❌ **sample_qbo_export.csv:** Does NOT exist
❌ **Unit test:** Not found

**Status:** Basic export exists but not QBO-specific or idempotent.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## H) DRIFT & GUARDRAILS

### PSI/KS Computations
✅ **Code:** app/ml/drift_monitor.py (Sprint 7)
✅ **PSI implementation:** Lines 45-75
✅ **JS divergence:** Lines 77-95
⚠️  **KS test:** NOT implemented
⚠️  **Threshold:** DRIFT_PSI_ALERT=0.25 (NOT 0.20 as required)

**Issue:** PSI threshold is 0.25 vs required 0.20

### Alert Surfacing
⚠️  **Logs:** Yes, logged via logger
❌ **Webhook:** NOT implemented
❌ **Monitoring:** No integration with monitoring system

### Cold-Start Policy
❌ **3 consistent labels:** NOT enforced in code
❌ **Implementation:** No cold-start check found
⚠️  **Config:** PROMOTE_MIN_OBS=3 exists but for rules, not cold-start

### OCR Golden Set
❌ **100 synthetic receipts:** Not committed to test fixtures
❌ **CI gate:** No ≥90% accuracy test in CI
⚠️  **Existing:** 634 receipts in data/simulated_docs/ but not golden set

**Action Required:** Create golden set and CI gate.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## I) SECURITY/COMPLIANCE

### SBOM & Dependency Scan
❌ **SBOM tool:** NOT configured in CI
❌ **Scan report:** No recent report found
⚠️  **CI:** .github/workflows/ci.yml exists but no security scan

**Available tools:** Bandit security scan report exists (reports/bandit_results.json)

### Secrets & PII
⚠️  **Redaction:** No evidence of log redaction/masking
❌ **Encryption at rest:** SQLite not encrypted
❌ **Code/config link:** No PII handling documented

**Issue:** Security baseline report exists but not comprehensive.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## J) TIMELINE & RISKS

### Today ($(date '+%Y-%m-%d'))
- System has 15,889 lines of production code
- 6 companies, 1,902 transactions (not meeting 2×1,200 requirement)
- Sprint 8 (Adaptive Rules) complete but not fully integrated
- Many audit requirements NOT met

### Progress Since Last Sprint
✅ Sprint 8 complete: Adaptive rules, decision blending, explainability
✅ Database schema complete: 11 tables
✅ API endpoints: 33+ (but missing key metrics/health endpoints)
✅ ML model: 99.48% accuracy (uncalibrated)
✅ Test coverage: ~85%

### Critical Blockers/Risks

**HIGH PRIORITY:**
1. ❌ No proper health/readiness endpoints with component checks
2. ❌ Synthetic data insufficient (317 vs 1,200 txns/tenant)
3. ❌ No calibration layer (Brier, ECE, isotonic/temperature)
4. ❌ Missing /api/metrics/latest endpoint
5. ❌ No active learning implementation
6. ❌ PSI threshold mismatch (0.25 vs 0.20 required)
7. ❌ No cold-start policy enforcement
8. ❌ QBO export not idempotent with required columns
9. ❌ No LLM cost tracking/enforcement
10. ❌ Missing security scans in CI

**MEDIUM PRIORITY:**
- No vector store (set to "none")
- Using SQLite instead of PostgreSQL
- No time-based holdout for evaluation
- Missing long-tail error analysis
- No OCR golden set with CI gate
- No dependency management tool (poetry/uv)

**LOW PRIORITY:**
- Documentation could be more prescriptive
- No monitoring/alerting webhooks

### ETAs (Assuming Full-Time Development)

**(a) Synthetic fixtures (2 tenants × 1,200 txns, 8% noise):**
📅 **October 14, 2025** (3 days)

**(b) Eval+calibration artifacts (Brier, ECE, plots, isotonic):**
📅 **October 16, 2025** (5 days)

**(c) Long-tail changes (50 errors analyzed, 15-25 rules added):**
📅 **October 17, 2025** (6 days)

**(d) Active learning (uncertainty sampler, queue, nightly job):**
📅 **October 21, 2025** (10 days)

**(e) Metrics API (GET /api/metrics/latest with full schema):**
📅 **October 15, 2025** (4 days)

**(f) QBO CSV (idempotent, correct columns, tests):**
📅 **October 16, 2025** (5 days)

**(g) Health/readiness endpoints (DB, vector, OCR checks):**
📅 **October 13, 2025** (2 days)

**(h) Security/compliance (SBOM, PII redaction, scans):**
📅 **October 18, 2025** (7 days)

**(i) Full system integration & testing:**
📅 **October 23, 2025** (12 days)

**CRITICAL PATH:** ~12 business days to production-ready state

### Asks from PM

**Immediate Clarifications Needed:**

1. **PostgreSQL:** Can we continue with SQLite for dev, or must migrate to Postgres now?

2. **Vector Store:** Is vector backend actually required, or can we stay with "none"?

3. **LLM Budget:** What's the actual LLM budget/month? Need to size cost tracking.

4. **QBO Columns:** Confirm/approve proposed column list for QBO export.

5. **Calibration Priority:** Isotonic vs temperature scaling preference?

6. **Active Learning:** Is this critical path or can we defer to next sprint?

7. **CI/CD:** Do we have access to deploy to staging environment?

8. **Monitoring:** Which monitoring system (DataDog/Prometheus/other)?

**Resource/Access Needs:**

- Access to PostgreSQL instance (if required)
- OpenAI API key with budget limits
- CI/CD pipeline credentials
- Monitoring system access
- Staging environment details

**Decision Requests:**

1. **Scope Reduction:** Should we prioritize P0 items (health, metrics, calibration, fixtures) and defer P1 items (active learning, long-tail) to next sprint?

2. **Testing Strategy:** Full end-to-end tests or focused unit tests for this deliverable?

3. **Documentation:** How much detail required in user-facing docs vs internal?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## SUMMARY ASSESSMENT

### Current State: 🟡 PARTIALLY READY

**Strengths:**
- Solid foundation (15,889 lines, 85% test coverage)
- Sprint 8 adaptive systems implemented
- High ML accuracy (99.48%)
- Good architecture (11 tables, 33+ APIs)

**Critical Gaps:**
- Missing 40% of audit requirements
- Insufficient synthetic data
- No calibration layer
- Missing key API endpoints
- No active learning
- Incomplete security posture

**Recommendation:** 
Focus on P0 items first (health, metrics, calibration, fixtures) to achieve minimum production readiness, then iterate on P1 items (active learning, long-tail, security hardening).

**Estimated Effort to Full Compliance:** 12-15 business days with dedicated development resources.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Report Generated:** $(date '+%Y-%m-%d %H:%M:%S %Z')
**Location:** /Users/fabiancontreras/ai-bookkeeper
**Audited By:** AI Development Team

