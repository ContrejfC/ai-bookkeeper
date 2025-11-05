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
- **Robots:** `index: true, follow: true` (via Next.js metadata API)
- **Rendering:** All pages render (static generation)
- **Use for:** Current, operational banks

### `noindex`
- **Rendering:** Pages render (for direct links, bookmarks)
- **Excluded from:** Sitemap (only active banks included)
- **Robots:** `index: false, follow: true` (via Next.js metadata API)
- **HTML Output:** `<meta name="robots" content="noindex,follow">` (via metadata)
- **Use for:** Defunct, merged, or low-priority banks

## Robots Behavior

### Generation Rules
- **All pages render:** Both active and noindex pages are statically generated
- **Robots via metadata:** Next.js metadata API sets robots directives
- **No manual meta tags:** Robots handled automatically by `generateMetadata()`

### Active Pages
```typescript
robots: {
  index: true,
  follow: true
}
```

### Noindex Pages
```typescript
robots: {
  index: false,
  follow: true
}
```

## Sitemap Policy

### Inclusion Rules
- **Only active banks:** `getActiveBanks()` filters `status === 'active'`
- **Excludes noindex:** Defunct/merged banks not in sitemap
- **Priority:** Uses bank-specific priority (0.6-0.9)
- **Change frequency:** `monthly`
- **Last modified:** Uses `updatedAt` field or current date

### Structure
```typescript
{
  url: `${SITE_URL}/guides/${bank.bankSlug}`,
  lastModified: new Date(bank.updatedAt || Date.now()),
  changeFrequency: 'monthly',
  priority: bank.priority
}
```

### Verification
```bash
# Count guide URLs in sitemap
curl -s https://ai-bookkeeper.app/sitemap.xml | grep -c '/guides/'

# Should return ≥50 (52 active banks)
```

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

## OG Image Usage

### Endpoint
- **URL:** `/api/og/pse?slug=${slug}`
- **Method:** GET
- **Returns:** PNG image (1200×630)

### Features
- **Text-only:** No logos, no brand colors
- **Neutral palette:** Gray/emerald background
- **Cache headers:** `public, max-age=86400, stale-while-revalidate=604800`
- **404 handling:** Returns 404 if bank not found

### Usage in Metadata
```typescript
images: [
  {
    url: `${SITE_URL}/api/og/pse?slug=${encodeURIComponent(slug)}`,
    width: 1200,
    height: 630,
    alt: `${bank.bankName} Export Guide`,
  },
]
```

### Verification
```bash
curl -sI 'https://ai-bookkeeper.app/api/og/pse?slug=chase-export-csv' | head -5
# Should return 200 with cache-control header
```

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

## Verification Steps

### Quick Verification Script
```bash
npm run verify:pse  # If added to package.json
# OR
bash scripts/verify_pse.sh
```

### Manual Verification

**1. Active guide page (200, indexable):**
```bash
curl -sI https://ai-bookkeeper.app/guides/chase-export-csv | head -5
# Should return 200 OK
```

**2. Noindex guide page (200, robots noindex):**
```bash
curl -s https://ai-bookkeeper.app/guides/peoples-united-export-csv | grep -i 'name="robots"'
# Should show: <meta name="robots" content="noindex,follow">
```

**3. Sitemap includes ≥50 guides:**
```bash
curl -s https://ai-bookkeeper.app/sitemap.xml | grep -c '/guides/'
# Should return ≥50 (52 active banks)
```

**4. OG endpoint returns 200 PNG:**
```bash
curl -sI 'https://ai-bookkeeper.app/api/og/pse?slug=chase-export-csv' | head -5
# Should return 200 with content-type: image/png
# Should have cache-control header
```

### E2E Tests
```bash
npx playwright test tests/e2e/pse-guides.spec.ts
```

**Coverage:**
- ✅ Active guide (Chase): 200, H1, canonical, JSON-LD, CTAs, OG
- ✅ Noindex guide (People's United): 200, robots noindex, not in sitemap
- ✅ Sitemap: ≥50 guide URLs, excludes noindex
- ✅ OG endpoint: 200 PNG with cache headers
- ✅ 404 handling: Invalid slug returns 404

## Troubleshooting

### Bank page not showing in sitemap
- Check `status: "active"` in banks.json
- Verify `getActiveBanks()` filters correctly
- Rebuild: `npm run build`
- Verify with `curl https://ai-bookkeeper.app/sitemap.xml | grep <slug>`

### Noindex page still indexed
- Check `robots: { index: false }` in `generateMetadata()`
- Verify Next.js metadata is rendering correctly
- Check browser dev tools for `<meta name="robots">` tag
- Ensure noindex bank is not in sitemap

### OG image not loading
- Check slug parameter: `/api/og/pse?slug=chase-export-csv`
- Verify bank exists: `getBankBySlug(slug)`
- Check cache headers in response
- Verify edge runtime is enabled

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

