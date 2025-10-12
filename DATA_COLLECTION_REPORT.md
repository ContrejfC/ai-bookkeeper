# AI BOOKKEEPER - DATA COLLECTION & TRAINING DATA REPORT
**Generated:** $(date)
**Location:** /Users/fabiancontreras/ai-bookkeeper

## 📊 TOTAL TRAINING DATA COLLECTED

- **Total Transactions:** 1,902 transactions
- **Total Receipts:** 634 receipt documents  
- **Training CSV Export:** 1,703 rows (292 KB)
- **Unique Vendors:** 57 distinct counterparties
- **Date Range:** Oct 2024 - Oct 2025 (12 months)
- **Average Amount:** $1,128.94 per transaction

## 🔍 DATA SOURCES

### 1. SIMULATED DATA (PRIMARY SOURCE - 89.5%)

**Location:** `scripts/simulate_companies.py`  
**Method:** Deterministic synthetic generation  
**Seed:** Random seed = 42 (reproducible)  
**Total:** 1,702 transactions

**Companies Generated (5 businesses):**

| Company | Transactions | Date Range |
|---------|--------------|------------|
| Midwest Accounting Advisors | 289 | Oct 10, 2024 - Sep 29, 2025 |
| Hamilton Coffee Co. | 330 | Oct 9, 2024 - Oct 1, 2025 |
| Cincy Web Builders LLC | 357 | Oct 9, 2024 - Sep 30, 2025 |
| Contreras Real Estate Group | 358 | Oct 10, 2024 - Oct 1, 2025 |
| Liberty Childcare Center | 368 | Oct 9, 2024 - Oct 1, 2025 |

**Receipt Documents:** 634 files in `data/simulated_docs/`

### 2. OPEN DATA (SECONDARY SOURCE - 10.5%)

**Location:** `scripts/internet_data_sync.py`  
**Method:** Kaggle-style sample datasets  
**Cleaning:** `app/utils/open_data_cleaner.py`  
**Total:** 200 transactions (Jan 1, 2023 - Dec 31, 2024)

## 🎯 ML MODEL TRAINING

**Training Script:** `scripts/train_from_open_data.py`

**Dataset Split:**
- Total: 1,902 transactions
- Training: 1,521 (80%)
- Test: 381 (20%)

**Features:** 322 dimensions
- TF-IDF (description): 200
- TF-IDF (vendor): 50  
- MCC codes: 50
- Amount buckets: 10
- Date features: 12

**Model Performance:**
- Training Accuracy: 99.93%
- **Test Accuracy: 99.48%** ✅
- Precision: 99.52%
- Recall: 99.48%
- F1-Score: 99.49%

## ⚠️ GAPS & LIMITATIONS

1. **Volume Insufficient:** ~317 txns/tenant vs 1,200 required
2. **No Noise Injection:** Missing 8% OCR perturbations
3. **No Committed Fixtures:** Data in DB only, not in repo
4. **Open Data Limited:** Only 200 transactions (10.5%)
5. **No Real Data:** All synthetic (OK for dev, need real for prod)

## 🎯 SUMMARY

- **Data Collection:** Synthetic generation + Open datasets
- **Total Collected:** 1,902 transactions + 634 receipts
- **Quality:** High (deterministic, realistic patterns)
- **ML Success:** 99.48% accuracy (exceeds 85% target by 14.48pp)

**Status:** ✅ Sufficient for MVP development  
**Production:** ⚠️ Needs 3.8× more data per tenant

