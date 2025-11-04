# Free Categorizer v1 – Trust & Conversion

## Overview

Enhanced free statement categorizer with trust-building compliance features and improved conversion optimizations.

## Key Features

✅ **Compliance & Trust**
- Dynamic SOC2 status based on `SOC2_STATUS` env var
- 24-hour automatic deletion with manual purge option
- Explicit opt-in consent for model training (default OFF)
- Privacy-preserving consent logging
- Updated Privacy Policy and Terms with accurate dates

✅ **Conversion Optimizations**
- Optional email gate with bypass link
- Sample data demonstration
- Sample CSV output preview
- Watermark banners with upgrade CTAs
- Post-export upgrade modal

✅ **Error Handling**
- Typed error codes with repair tips
- Inline help with links to export guides
- Accessible error states

✅ **Security**
- Server-side MIME sniffing
- File size validation
- Encrypted PDF detection
- Virus scan stub (TODO: ClamAV integration)
- IP hashing with per-deployment salt

✅ **Analytics**
- Provider-agnostic telemetry wrapper
- Conversion funnel tracking
- Lead attribution

## Environment Variables

Add these to your `.env` file:

```bash
# SOC2 Status (controls compliance copy)
SOC2_STATUS=aligned  # aligned | in_progress | certified

# Free Tool Limits
FREE_MAX_ROWS=500
FREE_MAX_FILE_MB=10

# Features
NEXT_PUBLIC_ENABLE_EMAIL_GATE=true

# Retention
FREE_RETENTION_HOURS=24

# Admin (for cron purge endpoint)
ADMIN_PURGE_TOKEN=your-secure-token-here-min-32-chars

# Backend
BACKEND_API_BASE=https://api.ai-bookkeeper.app
BACKEND_API_KEY=optional-api-key-for-backend-auth

# Storage
FREE_UPLOAD_DIR=/tmp/free_uploads

# IP Hashing Salt (for privacy)
IP_HASH_SALT=your-random-salt-change-in-production
```

## Frontend Environment

Add to `.env.local` (development) and Vercel (production):

```bash
NEXT_PUBLIC_API_URL=https://your-backend.run.app
NEXT_PUBLIC_ENABLE_EMAIL_GATE=true
NEXT_PUBLIC_ENABLE_ANALYTICS=true
```

## Cron Configuration (Vercel)

Add to `vercel.json`:

```json
{
  "crons": [
    {
      "path": "/api/admin/purge-ephemeral",
      "schedule": "0 * * * *"
    }
  ]
}
```

Or use external cron (recommended for production):

```bash
# Hourly purge of expired uploads
0 * * * * curl -X POST https://api.ai-bookkeeper.app/api/free/categorizer/admin/purge-ephemeral \
  -H "X-Purge-Token: your-admin-token"
```

## Installation

```bash
# Install dependencies
cd frontend
npm install

# Run development server
npm run dev
```

## Running Tests

### E2E Tests

```bash
# Install Playwright
npx playwright install

# Run E2E tests
npx playwright test e2e/free-categorizer.spec.ts

# Run with UI
npx playwright test --ui

# Run specific test
npx playwright test -g "sample flow"
```

### Unit Tests

```bash
# Run unit tests
npm test

# Run with coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

## Files Changed

### Frontend

**Configuration & Utilities:**
- `frontend/lib/config.ts` - Environment-driven configuration
- `frontend/lib/analytics.ts` - Provider-agnostic event tracking
- `frontend/lib/errors.ts` - Error codes and repair tips

**Pages:**
- `frontend/app/page.tsx` - Updated SOC2 copy
- `frontend/app/security/page.tsx` - Dynamic SOC2 status
- `frontend/app/privacy/page.tsx` - Added Free Tool & Model Training sections
- `frontend/app/terms/page.tsx` - Fixed date rendering
- `frontend/app/free/categorizer/page.tsx` - Enhanced with all v1 features

**Actions:**
- `frontend/app/free/categorizer/actions.ts` - Added deleteUpload function

**Tests:**
- `frontend/__tests__/validators.test.ts` - Unit tests
- `e2e/free-categorizer.spec.ts` - E2E tests

### Backend

**Models:**
- `app/models/free_tool.py` - FreeUploadDB, FreeLeadDB, ConsentLogDB

**Routes:**
- `app/api/free_categorizer.py` - Upload, delete, lead capture, purge

## API Endpoints

### Public Endpoints

```
POST /api/free/categorizer/upload
  - Upload file with consent tracking
  - Body: FormData with file + consent_training boolean

DELETE /api/free/categorizer/uploads/:id
  - Delete upload immediately

POST /api/free/categorizer/lead
  - Capture lead from email gate
  - Body: { email, uploadId, rows }
```

### Admin Endpoints

```
POST /api/free/categorizer/admin/purge-ephemeral
  - Purge expired uploads (24h+)
  - Header: X-Purge-Token: <ADMIN_PURGE_TOKEN>
```

## Acceptance Criteria

- ✅ SOC2 language is dynamic based on `SOC2_STATUS` env var
- ✅ Privacy and Terms render accurate "Last Updated" dates
- ✅ Free tool clearly states 24h deletion and opt-in training
- ✅ Consent toggle exists, default OFF, logged server-side
- ✅ Email gate present with working bypass
- ✅ All error codes produce UI messages with repair tips
- ✅ Sample file and sample CSV demo work
- ✅ "Delete now" fully purges upload
- ✅ Telemetry events fire with correct payloads
- ✅ E2E tests cover main flows
- ✅ Accessibility improvements (aria-labels, focus states, keyboard nav)

## Testing Checklist

- [ ] Test consent checkbox defaults to OFF
- [ ] Test "Use Sample Statement" loads preview
- [ ] Test "See Sample CSV Output" opens modal
- [ ] Test email gate with bypass link
- [ ] Test watermark banner appears for > 500 rows
- [ ] Test "Delete Now" purges data
- [ ] Test error states show repair tips
- [ ] Test keyboard navigation works
- [ ] Test with screen reader
- [ ] Run Lighthouse audit (target: a11y score ≥ 90)

## Deployment

### Frontend (Vercel)

```bash
# Set environment variables in Vercel dashboard
# Then deploy
vercel --prod
```

### Backend (Google Cloud Run / Render)

```bash
# Set environment variables
# Deploy latest code

# Verify purge endpoint works
curl -X POST https://api.ai-bookkeeper.app/api/free/categorizer/admin/purge-ephemeral \
  -H "X-Purge-Token: your-token"
```

## Monitoring

Track these metrics:
- Upload success rate
- Email gate bypass rate
- Lead capture rate
- Training consent opt-in rate
- Error frequency by code
- Time to purge (should be < 24h)

## Next Steps (Out of Scope for v1)

- [ ] Integrate ClamAV for virus scanning
- [ ] Add support for additional file formats
- [ ] Implement automated email nurture sequence for leads
- [ ] Add more sophisticated ML model training pipeline
- [ ] Implement IP-based rate limiting (currently email-based)

## Support

For questions or issues:
- Email: support@ai-bookkeeper.app
- GitHub: https://github.com/ContrejfC/ai-bookkeeper/issues

