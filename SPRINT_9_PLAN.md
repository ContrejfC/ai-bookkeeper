# SPRINT 9: P0 AUDIT COMPLIANCE
**Timeline:** 8 Business Days (Mon Oct 14 - Wed Oct 23, 2025)  
**Deliverables:** 10 Critical Items  
**Goal:** Production-Ready System

## 📅 TODAY'S PLAN (Day 0 - Saturday Oct 11)

- ✅ Create detailed implementation plan
- ✅ Set up TODO tracking (10 tasks)
- ✅ Review PM decisions
- ✅ Design schema changes
- ✅ Document execution timeline
- ⏳ Ready to begin D1 on Monday

## 📊 PROGRESS TO DATE

**✅ Complete (Sprint 8):**
- Decision blender (0.55/0.35/0.10)
- Drift detection (PSI, JS divergence)
- Rule versioning + rollback
- 11 database tables
- 33+ API endpoints
- ML model 99.48% accuracy

**⚠️ Partial:**
- 1,902 txns (need 2,400+)
- /healthz exists (need /readyz)
- Generic CSV (need QBO)
- Bandit scan (need full security suite)

**❌ Missing:**
- No calibration
- No /api/metrics/latest
- No cold-start enforcement
- No LLM cost tracking
- SQLite (need PostgreSQL)
- PSI=0.25 (need 0.20)

## 🚧 BLOCKERS/RISKS + MITIGATIONS

**HIGH (4):**
1. **Postgres migration breaks flows**
   - ✓ Keep SQLite parallel during D1-2
   - ✓ Comprehensive migration tests
   - ✓ Docker health checks

2. **Calibration degrades accuracy**
   - ✓ Test isotonic vs temperature
   - ✓ Fall back to raw probabilities
   - ✓ A/B test framework

3. **8-10% noise unrealistic**
   - ✓ Gradual (typos 5%, case 3%, space 2%)
   - ✓ Validate oracle labels noisy data
   - ✓ Compare accuracy before/after

4. **LLM fallback accuracy drops**
   - ✓ Graceful degradation (last ML prediction)
   - ✓ Alert but don't block
   - ✓ Log all fallback events

**MEDIUM (3):**
5. QBO hash collisions → SHA-256 space sufficient
6. /api/metrics/latest slow → 5-min cache + indexes
7. SBOM fails non-PyPI → cyclonedx-python-lib

**LOW (1):**
8. Cold-start too restrictive → Configurable ENV var

## 📅 DETAILED ETAS

**D1 (Mon Oct 14, 6pm ET):**
- PostgreSQL docker-compose
- Alembic migrations
- Settings.py DB switching
- 2×1,200 txns synthetic data

**D2 (Tue Oct 15, 6pm ET):**
- 600+ receipts (8-10% noise)
- Commit fixtures to tests/
- PSI threshold 0.25→0.20
- /api/healthz + /api/readyz

**D3 (Wed Oct 16, 8pm ET):**
- app/ml/calibrator.py
- Brier + ECE computation
- Isotonic + temperature
- reliability_plot.png + JSON

**D4 (Thu Oct 17, 7pm ET):**
- Integrate calibration
- Enforce p≥0.90 gating
- Cold-start tracker
- 3-label enforcement

**D5 (Fri Oct 18, 6pm ET):**
- /api/metrics/latest
- All 15+ fields
- PSI/KS/Brier/ECE
- Deterministic tests

**D6 (Mon Oct 21, 7pm ET):**
- app/exporters/qbo_exporter.py
- SHA-256 ExternalId
- 11-column CSV
- sample_qbo_export.csv

**D7 (Tue Oct 22, 6pm ET):**
- app/llm/cost_tracker.py
- $50/tenant, $1K global
- Auto-fallback >0.30 calls/txn
- llm_call_logs table

**D8 (Wed Oct 23, 8pm ET):**
- CycloneDX SBOM
- pip-audit + Trivy
- CI fails on HIGH
- SPRINT_9_COMPLETE.md

**CRITICAL PATH:** D3→D4→D5 (Calibration→Gating→Metrics)  
**PARALLEL:** D1-2 (Infra), D6 (QBO), D7 (LLM), D8 (Security)

## 📋 SCHEMA CHANGES

### /api/metrics/latest (NEW)
```json
{
  "automation_rate": 0.884,
  "reconciliation_rate": 0.923,
  "je_imbalance_count": 0,
  "brier_score": 0.012,
  "ece_bins": [{"bin":"0.9-1.0","pred_mean":0.95,"obs_freq":0.94,"count":450}],
  "psi_vendor": 0.08,
  "psi_amount": 0.12,
  "ks_vendor": 0.15,
  "ks_amount": 0.09,
  "llm_calls_per_txn": 0.12,
  "unit_cost_per_txn": 0.0023,
  "llm_budget_status": {
    "global_used": 247.50,
    "global_limit": 1000.00,
    "tenant_used": 23.10,
    "tenant_limit": 50.00,
    "fallback_active": false
  },
  "ruleset_version_id": "v0.4.13",
  "model_version_id": "m1.2.0",
  "calibration_method": "isotonic",
  "timestamp": "2025-10-14T18:23:45-04:00"
}
```

**Additions vs spec:**
- `llm_budget_status` object (budget breakdown)
- `calibration_method` (transparency)
- `count` in ece_bins (significance)

### QBO CSV Export (11 columns)
```csv
Date,JournalNumber,AccountName,Debit,Credit,Currency,Memo,Entity,Class,Location,ExternalId
```

**ExternalId:** SHA-256(je_id|date|sorted_lines)[:16]

### New Database Tables (4)

**llm_call_logs:**
- tenant_id, transaction_id, call_type, model
- prompt_tokens, completion_tokens, cost_usd
- timestamp, indexes

**calibration_metadata:**
- model_version, method (isotonic|temperature)
- params_json, brier_score, ece
- train_samples, created_at

**cold_start_tracking:**
- vendor_normalized, suggested_account
- label_count, consistent, last_seen

**qbo_export_log:**
- external_id (UNIQUE), je_id
- export_date, line_count, status

## 🎯 ACCEPTANCE CRITERIA

1. ✓ PostgreSQL in docker-compose
2. ✓ 2,400+ txns, 600+ receipts, 8-10% noise
3. ✓ PSI threshold = 0.20
4. ✓ Brier < 0.05, reliability_plot.png
5. ✓ Auto-post gated at p≥0.90
6. ✓ Cold-start: 3 labels enforced
7. ✓ /api/metrics/latest: all fields + tests
8. ✓ QBO CSV: idempotent, 11 cols, tests
9. ✓ LLM budgets enforced, fallback working
10. ✓ SBOM + pip-audit + Bandit + Trivy in CI

## 📊 SPRINT METRICS

- **Estimated LOC:** ~3,500 lines
- **New APIs:** 3 (/metrics/latest, /export/qbo, /readyz)
- **New Tables:** 4
- **New Modules:** 6
- **Test Coverage:** Maintain ~85%
- **Docs:** SPRINT_9_COMPLETE.md

## 🚀 STATUS

**READY TO EXECUTE**

All requirements clear, risks mitigated, schema designed.  
Proceeding with D1 (PostgreSQL + fixtures) Monday 9am ET.

