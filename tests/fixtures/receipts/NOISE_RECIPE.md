# OCR Noise Recipe (Sprint 9 Stage B)

**Generated:** 2025-10-11 14:30:16

## Noise Percentages

- **Typos:** 5.0% (character swaps, deletions, insertions)
- **Casing:** 3.0% (random case changes, ALL CAPS words)
- **Spacing/Punctuation:** 2.0% (double spaces, missing/extra punctuation)
- **Total Target:** 10.0%

## Typo Noise (5%)

Applied to individual characters:
- **Character swaps:** Adjacent letters swapped (e.g., 'hte' → 'the')
- **Character deletions:** Random letters removed (e.g., 'total' → 'tota')
- **Character insertions:** Random letters added (e.g., 'date' → 'datre')

## Casing Noise (3%)

Applied to words:
- **ALL CAPS:** Entire word uppercased (e.g., 'Invoice' → 'INVOICE')
- **all lower:** Entire word lowercased (e.g., 'Total' → 'total')
- **RaNdOm:** Random case per character (e.g., 'Receipt' → 'rEcEiPt')

## Spacing/Punctuation Noise (2%)

Applied to whitespace and punctuation:
- **Double spaces:** Single space → double space
- **Missing punctuation:** Punctuation removed (e.g., 'Total: $100' → 'Total $100')
- **Extra punctuation:** Random punctuation added (e.g., 'Date 10/11' → 'Date, 10/11')

## Actual Noise Rates (Measured)

- **Tenant Alpha:** 93.63%
- **Tenant Beta:** 93.61%
- **Average:** 93.62%

## Reproducibility

Fixed seeds ensure deterministic generation:
- **Alpha seed:** 5001
- **Beta seed:** 5002

To regenerate identical receipts:
```bash
python scripts/generate_stage_b_receipts.py
```
