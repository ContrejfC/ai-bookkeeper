# PSE Bank Export Guides - Seed List

## Overview

This document lists all 60 seeded banks in the programmatic SEO system, organized by tier and status.

**Total:** 60 banks  
**Active (indexed):** 52 banks  
**Noindex (not indexed):** 8 banks  

## Active Banks (52)

### Tier 1: Retail SMB Banks (25)

| Bank Name | Slug | Status | Priority |
|-----------|------|--------|----------|
| Chase | `chase-export-csv` | active | 0.9 |
| Bank of America | `bank-of-america-export-csv` | active | 0.9 |
| Wells Fargo | `wells-fargo-export-csv` | active | 0.9 |
| Citi | `citi-export-csv` | active | 0.9 |
| Capital One | `capital-one-export-csv` | active | 0.9 |
| U.S. Bank | `us-bank-export-csv` | active | 0.8 |
| PNC Bank | `pnc-export-csv` | active | 0.8 |
| Truist | `truist-export-csv` | active | 0.8 |
| TD Bank | `td-bank-export-csv` | active | 0.8 |
| Regions Bank | `regions-export-csv` | active | 0.8 |
| Fifth Third Bank | `fifth-third-export-csv` | active | 0.8 |
| KeyBank | `keybank-export-csv` | active | 0.8 |
| Huntington Bank | `huntington-export-csv` | active | 0.8 |
| Citizens Bank | `citizens-bank-export-csv` | active | 0.8 |
| M&T Bank | `m-and-t-export-csv` | active | 0.8 |
| BMO (Bank of Montreal) | `bmo-export-csv` | active | 0.8 |
| Santander Bank | `santander-export-csv` | active | 0.7 |
| Comerica Bank | `comerica-export-csv` | active | 0.7 |
| First Citizens Bank | `first-citizens-export-csv` | active | 0.7 |
| Zions Bank | `zions-export-csv` | active | 0.7 |
| Frost Bank | `frost-export-csv` | active | 0.7 |
| Synovus Bank | `synovus-export-csv` | active | 0.7 |
| Valley National Bank | `valley-export-csv` | active | 0.7 |
| Webster Bank | `webster-export-csv` | active | 0.7 |
| East West Bank | `east-west-bank-export-csv` | active | 0.7 |

### Tier 2: Cards & Fintech SMB (13)

| Bank Name | Slug | Status | Priority |
|-----------|------|--------|----------|
| American Express Business | `american-express-business-export-csv` | active | 0.9 |
| PayPal | `paypal-export-csv` | active | 0.8 |
| Stripe | `stripe-export-csv` | active | 0.8 |
| Square | `square-export-csv` | active | 0.8 |
| Brex | `brex-export-csv` | active | 0.8 |
| Mercury | `mercury-export-csv` | active | 0.8 |
| Wise Business | `wise-business-export-csv` | active | 0.7 |
| Payoneer | `payoneer-export-csv` | active | 0.7 |
| Novo | `novo-export-csv` | active | 0.7 |
| BlueVine | `bluevine-export-csv` | active | 0.7 |
| Relay | `relayfi-export-csv` | active | 0.7 |
| NorthOne | `northone-export-csv` | active | 0.7 |
| Axos Business | `axos-business-export-csv` | active | 0.7 |

### Tier 3: Regional with SMB Share (14)

| Bank Name | Slug | Status | Priority |
|-----------|------|--------|----------|
| First Horizon Bank | `first-horizon-export-csv` | active | 0.7 |
| Banner Bank | `banner-export-csv` | active | 0.7 |
| Old National Bank | `old-national-export-csv` | active | 0.7 |
| First Hawaiian Bank | `first-hawaiian-export-csv` | active | 0.7 |
| Independence Bank | `independence-bank-export-csv` | active | 0.6 |
| Pinnacle Financial Partners | `pinnacle-export-csv` | active | 0.7 |
| Associated Bank | `associated-bank-export-csv` | active | 0.7 |
| Texas Capital Bank | `texas-capital-export-csv` | active | 0.7 |
| Western Alliance Bank | `western-alliance-export-csv` | active | 0.7 |
| Umpqua Bank | `umpqua-export-csv` | active | 0.7 |
| Columbia Bank | `columbia-bank-export-csv` | active | 0.7 |
| NBKC Bank | `nbkc-export-csv` | active | 0.7 |
| Live Oak Bank | `live-oak-bank-export-csv` | active | 0.7 |
| IncrediBank | `incredibank-export-csv` | active | 0.6 |

## Noindex Banks (8)

These banks are defunct, merged, or rolled up into other institutions. Pages exist for direct links but are excluded from search engines and sitemap.

| Bank Name | Slug | Status | Priority | Notes |
|-----------|------|--------|----------|-------|
| BBVA USA | `bbva-us-export-csv` | noindex | 0.5 | Acquired by PNC (2021) |
| People's United Bank | `peoples-united-export-csv` | noindex | 0.5 | Merged with M&T (2022) |
| Signature Bank | `signature-bank-export-csv` | noindex | 0.5 | Closed by regulators (2023) |
| PacWest Bank | `pacwest-export-csv` | noindex | 0.5 | Merged with Banc of California (2023) |
| Silicon Valley Bank (SVB) | `silicon-valley-bank-export-csv` | noindex | 0.5 | Failed, acquired by First Citizens (2023) |
| First Republic Bank | `first-republic-export-csv` | noindex | 0.5 | Failed, acquired by Chase (2023) |
| SunTrust Bank | `suntrust-export-csv` | noindex | 0.5 | Merged to form Truist (2019) |
| BB&T (Branch Banking and Trust) | `bbt-export-csv` | noindex | 0.5 | Merged to form Truist (2019) |

## Format Support

**Current:** Only CSV slugs are generated (`<bank>-export-csv`)

**Supported formats by bank:**
- Most banks: CSV, OFX, QFX
- Fintech (PayPal, Stripe, Square, etc.): CSV only
- Some regional banks: CSV, OFX, QFX

**To enable OFX/QFX:** See `PSE_README.md` for instructions on generating format-specific slugs.

## Priority Explanation

- **0.9:** Top-tier national banks, major cards/fintech
- **0.8:** Large regional banks, popular SMB fintech
- **0.7:** Regional banks with SMB presence, smaller fintech
- **0.6:** Smaller regional banks
- **0.5:** Noindex (defunct/merged)

## Maintenance Schedule

### Quarterly Review (every 3 months)
- Check for bank mergers, acquisitions, closures
- Update noindex list
- Verify export process accuracy
- Review search performance in GSC

### Annual Refresh (once per year)
- Expand to 100+ banks
- Add OFX/QFX format variants
- Update FAQ content based on user feedback
- Refresh screenshots (if added)

## Adding New Banks

### Selection Criteria
1. **SMB focus:** Business checking/cards
2. **CPA relevance:** Used by accounting professionals
3. **Search volume:** Decent query volume for "<bank> export CSV"
4. **Export capability:** Bank supports CSV/OFX/QFX exports

### Priority Guidelines
- National retail: 0.9
- Top-10 fintech: 0.9
- Regional with SMB: 0.7-0.8
- Smaller regional: 0.6-0.7
- Credit unions: 0.5-0.6 (consider case-by-case)

### Process
1. Add record to `data/pse/banks.json`
2. Run `npm run build` to generate page
3. Run `npm run check:pse` for trademark safety
4. Test manually at `/guides/<slug>`
5. Verify in sitemap
6. Update this seed list

## URL Structure

All guides follow this pattern:
```
https://ai-bookkeeper.app/guides/<bank-slug>
```

Examples:
- `https://ai-bookkeeper.app/guides/chase-export-csv`
- `https://ai-bookkeeper.app/guides/american-express-business-export-csv`
- `https://ai-bookkeeper.app/guides/stripe-export-csv`

## Internal Links

Each guide includes CTAs to:
- **Primary:** `/free/categorizer` (above fold, multiple placements)
- **Secondary:** `/pricing` (above fold)
- **Footer:** `/privacy`, `/security`

## Analytics Tracking

Events fired:
- `pse_page_view` - On page load
- `pse_cta_clicked` - On CTA click

Use these to track:
- Most viewed banks
- Conversion rate by bank
- CTA effectiveness

## SEO Performance Targets

### Goals (per guide page)
- **Impressions:** 100+/month (tier 1), 50+/month (tier 2/3)
- **CTR:** 3-5% average
- **Conversions:** 2-3% of visitors → free tool users

### Monitor in GSC
- Query rankings for "<bank> export CSV"
- Click-through rates
- Position trends
- Core Web Vitals

## Future Enhancements

### Phase 2
- Add OFX/QFX format variants (120 more pages)
- Expand to 100+ banks
- Add regional credit unions (select few)

### Phase 3
- Screenshot guides (blurred/redacted)
- Video tutorials (voiceover, text-based)
- Bank-specific troubleshooting sections
- User-generated tips/comments

### Phase 4
- International banks (Canada, UK, Australia)
- Localized versions (es, fr, de)
- API-based export guides

## Last Updated

**Date:** November 5, 2025  
**Version:** 1.0  
**Total Banks:** 60 (52 active, 8 noindex)

