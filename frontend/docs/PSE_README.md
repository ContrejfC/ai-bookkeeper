# Programmatic SEO: Bank Export Guides

## Overview

This directory contains the programmatic SEO (PSE) system for generating bank export guide pages. The system creates 60+ SEO-optimized guide pages targeting high-intent queries like:

- `<bank> export CSV`
- `<bank> transactions to QuickBooks`
- `categorize <bank> transactions`

## Architecture

### Data Layer
- **Location:** `frontend/data/pse/banks.json`
- **Schema:** Bank records with slug, name, formats, FAQ, steps, notes, status
- **Count:** 60 banks (52 active, 8 noindex)

### Pages
- **Route:** `app/guides/[slug]/page.tsx`
- **Generation:** Static with `generateStaticParams()`
- **Rendering:** Server components for optimal SEO

### Components
- **NonAffiliation:** `components/NonAffiliation.tsx` - Trademark disclaimer
- **PSEAnalytics:** `components/PSEAnalytics.tsx` - Client-side tracking

### Assets
- **OG Images:** `app/api/og/pse/route.tsx` - Dynamic, text-only
- **Sitemap:** `app/sitemap.ts` - Includes all active banks

## Adding a New Bank

### 1. Add to banks.json

```json
{
  "id": "example-bank",
  "bankSlug": "example-bank-export-csv",
  "bankName": "Example Bank",
  "formats": ["csv", "ofx", "qfx"],
  "primaryFormat": "csv",
  "status": "active",
  "priority": 0.8,
  "faq": [
    {
      "q": "How do I export Example Bank transactions?",
      "a": "Log in to Example Bank online banking..."
    }
  ],
  "steps": [
    {
      "title": "Log in to Example Bank",
      "body": "Visit examplebank.com and sign in."
    }
  ],
  "notes": {
    "quirks": ["May limit downloads to 500 transactions"]
  }
}
```

### 2. Rebuild

```bash
npm run build
```

The new bank guide will be generated automatically at `/guides/example-bank-export-csv`.

### 3. Verify

```bash
# Check trademark safety
npm run check:pse

# Run tests
npx playwright test tests/e2e/pse-guides.spec.ts

# Check sitemap
curl https://ai-bookkeeper.app/sitemap.xml | grep example-bank
```

## Enabling OFX/QFX Formats

Currently, only CSV slugs are generated (`<bank>-export-csv`). To enable other formats:

### 1. Update slug generation in `lib/pse-banks.ts`:

```typescript
export function getAllBankSlugs(): string[] {
  const slugs: string[] = [];
  for (const bank of getAllBanks()) {
    for (const format of bank.formats) {
      slugs.push(`${bank.id}-export-${format}`);
    }
  }
  return slugs;
}
```

### 2. Update route to parse format from slug

### 3. Update metadata and content for format-specific pages

## Status Flags

### `active`
- **Included in:** Sitemap, search engines
- **Robots:** `index,follow`
- **Use for:** Current, operational banks

### `noindex`
- **Included in:** Rendered pages (for direct links)
- **Excluded from:** Sitemap
- **Robots:** `noindex,follow`
- **Use for:** Defunct, merged, or low-priority banks

## Trademark Policy

### ✅ ALLOWED:
- Plain text bank names (nominative use)
- Factual descriptions of export processes
- Generic UI colors (gray, emerald, white)

### ❌ PROHIBITED:
- Bank logos or trademarked images
- Brand-specific color schemes (see `check_pse_assets.ts`)
- Endorsement language or affiliation claims

### Enforcement:
```bash
npm run check:pse
```

This script checks for:
- Logo imports or paths
- Banned brand colors (hex codes)
- Violations in guides, components, OG images, and data

## SEO Elements

### On-Page
- **Title:** `${bankName} — Export Transactions to CSV (Guide)`
- **Description:** Step-by-step with CTA to free tool
- **Canonical:** `https://ai-bookkeeper.app/guides/${slug}`
- **H1:** `How to export ${bankName} transactions to CSV`

### JSON-LD Schemas
1. **HowTo:** Step-by-step export instructions
2. **FAQPage:** 4+ bank-specific Q&As
3. **BreadcrumbList:** Home → Guides → Bank

### Open Graph
- **Image:** `/api/og/pse?slug=${slug}` (text-only, neutral)
- **Type:** article
- **Locale:** en_US

## Analytics

### Events Tracked:
- `pse_page_view` - On page load
- `pse_cta_clicked` - On CTA click (free_categorizer | pricing)

### Properties:
- `slug` - Bank slug
- `bank` - Bank name
- `format` - Primary format (csv)
- `cta` - CTA type

## Internal Linking

Each guide page links to:
- `/free/categorizer` (primary CTA, above fold)
- `/pricing` (secondary CTA)
- `/privacy` (footer)
- `/security` (footer)

## Performance

### Targets:
- **LCP:** < 2.5s
- **CLS:** < 0.1
- **INP:** < 200ms

### Optimizations:
- Server components (zero client JS by default)
- Static generation at build time
- Image-free design (text-only OG images)
- Minimal CSS (Tailwind, tree-shaken)

## Testing

### Unit Tests
```bash
npm run check:pse
```

### E2E Tests
```bash
npx playwright test tests/e2e/pse-guides.spec.ts
```

### Manual Checks
- Visit `/guides/chase-export-csv`
- Verify H1, canonical, JSON-LD, CTAs
- Check OG image: `/api/og/pse?slug=chase-export-csv`
- Confirm in sitemap: `/sitemap.xml`

## Maintenance

### Quarterly Review:
1. Update bank list (mergers, acquisitions, closures)
2. Mark defunct banks as `noindex`
3. Verify export process accuracy
4. Check for broken internal links

### When a Bank Changes:
1. Update `banks.json` with new info
2. Adjust `status` if needed (`active` → `noindex`)
3. Rebuild and redeploy
4. Monitor GSC for 404s or indexing issues

## Troubleshooting

### Bank page not showing in sitemap
- Check `status: "active"` in banks.json
- Rebuild: `npm run build`
- Verify with `curl https://ai-bookkeeper.app/sitemap.xml | grep <slug>`

### Trademark safety check failing
- Remove logo imports or paths
- Replace banned brand colors with neutral palette
- Use `npm run check:pse` to identify violations

### Tests failing
- Ensure dev server is running on correct port
- Check `NEXT_PUBLIC_SITE_URL` env var
- Verify bank data in `banks.json` is valid JSON

## Resources

- **Bank Data:** `frontend/data/pse/banks.json`
- **Route Template:** `frontend/app/guides/[slug]/page.tsx`
- **Helper Library:** `frontend/lib/pse-banks.ts`
- **Safety Script:** `frontend/scripts/check_pse_assets.ts`
- **E2E Tests:** `frontend/tests/e2e/pse-guides.spec.ts`
- **Seed List:** `frontend/docs/PSE_SEED_LIST.md`

