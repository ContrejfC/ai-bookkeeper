# Reader Evaluation Harness

## Overview

The Reader Evaluation Harness runs test datasets through the ingestion pipeline and produces a scored report validating:

- ✅ **Reconciliation**: Opening + transactions ≈ closing balance
- ✅ **Date Parsing**: All dates successfully parsed
- ✅ **Currency Detection**: Correct currency identified
- ✅ **Confidence Scoring**: Median confidence ≥ 0.85
- ✅ **Deduplication**: Duplicates correctly identified

## Quick Start

```bash
# Run evaluation
python ops/reader_eval/run_eval.py \
  --config ops/reader_eval/config.yaml \
  --out out/reader_eval

# View results
cat out/reader_eval/*/report.json | python -m json.tool
```

## Configuration

Edit `config.yaml` to add/remove datasets:

```yaml
datasets:
  - name: camt053_min
    kind: camt
    path: tests/fixtures/standards/camt053_min.xml
    expected_rows: 5
    expected_currency: USD
    reconciliation_tolerance_cents: 1
```

## Output

Report structure:
```json
{
  "timestamp": "2025-10-30T12:00:00",
  "summary": {
    "datasets": 8,
    "pass": 7,
    "fail": 1,
    "skip": 0
  },
  "metrics": {
    "reconcile_pass_rate": 0.95,
    "date_parse_rate": 1.00,
    "currency_detect_rate": 1.00,
    "low_conf_fraction": 0.12,
    "dedup_rate": 0.98
  },
  "datasets": [...]
}
```

## Validation Thresholds

Adjust in `config.yaml`:
- `min_date_parse_rate: 1.00` - 100% dates must parse
- `min_reconciliation_pass_rate: 0.95` - 95% must reconcile  
- `min_confidence_threshold: 0.85` - Confidence cutoff
- `max_low_confidence_fraction: 0.15` - Max 15% low confidence
- `max_duplicate_rate: 0.05` - Max 5% duplicates

## Scoring

Per-dataset score (0.0-1.0):
```
score = (reconcile + dates + currency + confidence + dedup) / 5
```

**Pass threshold**: ≥ 0.80 (4/5 checks)

## Integration

### With Launch Checks

Add to `ops/launch_checks/config.yaml`:
```yaml
checks:
  reader_eval:
    enabled: true
    min_pass_rate: 0.95
```

### With CI/CD

See `.github/workflows/reader-eval.yml` for automated runs.

## Troubleshooting

### All datasets fail

**Cause**: Parsers not importable

**Solution**: Ensure `app/ingestion/standards/` is in Python path

### Reconciliation fails

**Cause**: Sign conventions or balance calculation

**Solution**: Check parser logic for credit/debit handling

### Currency detection fails

**Cause**: Missing currency in fixture

**Solution**: Add `<Ccy>` tags in XML or currency fields in other formats



