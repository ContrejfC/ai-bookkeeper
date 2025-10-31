# Sample Files

## sample.csv
Example bank statement CSV with 10 transactions.
Format: date, description, amount

## sample.pdf
Example bank statement PDF (1 page).

**Note**: To generate sample.pdf, use the synthetic statement generator:

```bash
python -m scripts.synth_statements.generator \
  --style scripts/synth_statements/styles/checking.yaml \
  --output frontend/public/samples/sample.pdf \
  --rows 10 \
  --pages 1
```

Or download a sample from:
- https://templates.office.com/bank-statement
- https://www.vertex42.com/ExcelTemplates/bank-statement.html

**Privacy**: Ensure any sample files contain NO real account data or PII.
