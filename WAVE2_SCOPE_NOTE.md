# Wave-2 UI — Scope & Implementation Note

**Date:** 2024-10-11  
**Status:** 🚧 IN PROGRESS

---

## Scope Overview

Wave-2 UI is a **major expansion** adding 7 new feature areas:

1. **Firm Console** (`/firm`) — Multi-tenant management dashboard
2. **Rules Console** (`/rules`) — Rule candidate promotion workflow
3. **Audit Log** (`/audit`) — Decision history & traceability
4. **Billing** (`/billing`) — Stripe integration for subscriptions
5. **Notifications** (`/settings/notifications`) — Alert channel configuration
6. **Receipt Highlights** (`/receipts`) — Canvas overlay for OCR fields
7. **Onboarding Wizard** (`/onboarding`) — New tenant setup flow

**Additionally:**
- Analytics event system (page views, actions, exports)
- Daily rollup job for analytics reporting
- WCAG AA accessibility compliance (axe-core validation)

---

## Implementation Strategy

Given the large scope, I will:

1. **Build core structure first:**
   - Routes for all 7 pages
   - Templates with realistic UI
   - Mock data for demonstrations

2. **Add E2E tests:**
   - 7 test suites (one per major feature)
   - Performance validation (P95 < 300ms)
   - Accessibility checks (axe-core)

3. **Document integration blockers:**
   - Stripe: Needs `STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`, webhook endpoint
   - Slack: Needs webhook URL for notifications
   - OCR coordinates: Needs parser output with bounding boxes

4. **Provide artifacts:**
   - Screenshots of each page
   - Sample CSV exports
   - Test results
   - Accessibility audit

---

## Known Blockers (Production)

### 1. Stripe Integration

**Requirements:**
- Stripe account (test mode)
- `STRIPE_PUBLISHABLE_KEY` (client-side)
- `STRIPE_SECRET_KEY` (server-side)
- Webhook endpoint URL (for subscription updates)

**Workaround:**
- UI fully implemented
- Payment form renders
- Test mode simulation available
- Webhook handler stubbed

### 2. Slack Notifications

**Requirements:**
- Slack workspace
- Incoming webhook URL per tenant
- OAuth flow for workspace connection

**Workaround:**
- Configuration UI complete
- Webhook URL stored
- Notification logic implemented
- Test mode sends to console logs

### 3. Receipt Highlights (OCR Coordinates)

**Requirements:**
- OCR parser must output bounding boxes: `{"date": {"text": "10/11/2024", "bbox": [x1, y1, x2, y2]}}`
- PDF rendering library (pdf.js or similar)
- Canvas drawing logic

**Workaround:**
- UI structure complete
- Mock coordinates for demo
- Golden-set test validates IoU calculation
- Real coordinates can be integrated later

---

## Timeline

**Estimated Effort:** 2-3 days for full implementation

**Phases:**
1. **Phase 1 (Day 1):** Firm Console, Rules Console, Audit Log
2. **Phase 2 (Day 2):** Billing, Notifications, Receipt Highlights
3. **Phase 3 (Day 3):** Onboarding Wizard, Analytics, Tests, Documentation

---

## Acceptance Criteria

**For each feature:**
- ✅ Route implemented
- ✅ Template renders
- ✅ Mock data displayed
- ✅ E2E tests passing
- ✅ Performance < 300ms
- ✅ Screenshots provided

**Overall:**
- ✅ 7 E2E test suites green
- ✅ Accessibility audit (axe-core)
- ✅ Integration blockers documented
- ✅ Artifacts delivered

---

## Current Status

**Starting implementation now...**

This document will be updated with progress and final results.

---

**Document Version:** 1.0  
**Last Updated:** 2024-10-11

