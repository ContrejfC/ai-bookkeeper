# Stage A Fixtures - Seeds and Parameters

**Generated:** 2025-10-11 14:14:31

## Tenant Alpha

- **Seed:** 1001
- **Company ID:** fixture_alpha
- **Company Name:** Alpha Manufacturing Inc.
- **Business Type:** manufacturing
- **Target Transactions:** ≥1200
- **Date Range:** 365 days
- **Monthly Revenue:** $80,000 - $150,000

## Tenant Beta

- **Seed:** 2002
- **Company ID:** fixture_beta
- **Company Name:** Beta Services LLC
- **Business Type:** professional_services
- **Target Transactions:** ≥1200
- **Date Range:** 365 days
- **Monthly Revenue:** $50,000 - $90,000

## Reproducibility

To regenerate identical fixtures:

```bash
python scripts/generate_stage_a_fixtures.py
```

Seeds are fixed, so output will be deterministic.

## Vendor Distribution

- Power-law frequency (realistic vendor patterns)
- Revenue sources: ~15% weight
- Expense vendors: ~85% weight
- Date distribution: Triangular (weighted toward recent)

## Account Categories

- Revenue: 8000-8200 series
- COGS: 5000-5200 series
- Expenses: 6000-6900 series
