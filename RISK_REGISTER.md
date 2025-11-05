# AI Bookkeeper - Risk Register

## 📋 Risk Management Overview

**Last Updated:** November 4, 2025  
**Review Cycle:** Quarterly  
**Owner:** Engineering Team  

---

## 🔴 CRITICAL RISKS (P0)

### RISK-001: CSV Formula Injection

**Risk:** Attacker uploads CSV with formulas that execute in victim's Excel

**Impact:** HIGH  
**Likelihood:** MEDIUM  
**Severity:** CRITICAL  

**Mitigation:** ✅ SHIPPED  
- `lib/csv_sanitize.ts` - Neutralizes =, +, -, @, \t, \r prefixes
- Applied to all download/export paths
- Tested with 17 unit tests including DDE attacks

**Owner:** Engineering  
**SLI:** 0 formula execution incidents  
**SLO:** 100% of exports sanitized  
**Alert:** User reports formula execution → P0 incident  

**Verification:**
```bash
# Download CSV with =1+1
# Open in Excel  
# Should show '=1+1 as text, not 2
```

**Status:** ✅ MITIGATED

---

### RISK-002: ZIP Bomb DoS

**Risk:** Attacker uploads small ZIP that expands to gigabytes

**Impact:** HIGH (server crash, disk exhaustion)  
**Likelihood:** MEDIUM  
**Severity:** CRITICAL  

**Mitigation:** ✅ SHIPPED  
- `lib/mime-validator.ts` - 6 ZIP safety checks
- Total uncompressed size limit: 50MB
- Entry count limit: 500 files
- Nested archive detection
- Path traversal prevention

**Owner:** Engineering  
**SLI:** 0 successful ZIP bomb uploads  
**SLO:** 100% of ZIP bombs rejected  
**Alert:** `ZIP_SAFETY_VIOLATION` errors spike → investigate  

**Verification:**
```bash
# Create 1KB zip that expands to 500MB
# Upload → Expect rejection
```

**Status:** ✅ MITIGATED

---

### RISK-003: Denial of Service (Rate-Based)

**Risk:** Attacker hammers API endpoints to exhaust resources

**Impact:** HIGH (service unavailable)  
**Likelihood:** HIGH  
**Severity:** CRITICAL  

**Mitigation:** ✅ SHIPPED  
- Middleware rate limiting: 20 req/min per IP
- Per-IP concurrency gate: 2 concurrent requests
- Circuit breaker with 5-minute cooldown
- Maintenance mode kill-switch

**Owner:** Engineering  
**SLI:** <1% of requests return 429  
**SLO:** 99.9% availability under normal load  
**Alert:** 429 rate >10% for >5 min → enable maintenance mode  

**Verification:**
```bash
# Send 25 rapid requests
# Expect: 20 success, 5 rate-limited (429)
```

**Status:** ✅ MITIGATED

---

## 🟠 HIGH RISKS (P1)

### RISK-004: Data Retention Violation (Privacy)

**Risk:** Ephemeral files not deleted within 24-hour SLA

**Impact:** MEDIUM (GDPR violation, user trust)  
**Likelihood:** LOW  
**Severity:** HIGH  

**Mitigation:** ✅ SHIPPED  
- Automated purge cron (daily at midnight)
- Deletion SLA verifier endpoint
- `/api/admin/verify-deletions` monitors p95 age
- Manual purge capability

**Owner:** Engineering + Compliance  
**SLI:** p95 file age ≤ 1440 minutes  
**SLO:** staleCount === 0 (100% deleted on time)  
**Alert:** `p95Minutes > 1440` or `staleCount > 0` → P1 incident  

**Verification:**
```bash
curl -s -X POST https://ai-bookkeeper.app/api/admin/verify-deletions \
  -H "Authorization: Bearer $TOKEN" | jq '{p95Minutes, staleCount}'
```

**Status:** ✅ MITIGATED

---

### RISK-005: XSS via User-Uploaded Content

**Risk:** Malicious scripts in uploaded files execute in browser

**Impact:** HIGH (account takeover, data theft)  
**Likelihood:** MEDIUM  
**Severity:** HIGH  

**Mitigation:** ✅ SHIPPED  
- Content Security Policy (CSP) headers
- `script-src 'self'` only
- `connect-src` limited to known APIs
- File type validation (no .html, .js)
- Input sanitization

**Owner:** Engineering  
**SLI:** 0 successful XSS attacks  
**SLO:** 100% of user content sanitized  
**Alert:** CSP violation reports → investigate  

**Verification:**
```bash
curl -I https://ai-bookkeeper.app/free/categorizer | grep content-security-policy
```

**Status:** ✅ MITIGATED

---

### RISK-006: AI Budget Overrun

**Risk:** Unexpected traffic spike exhausts OpenAI budget

**Impact:** HIGH (service degraded, cost overrun)  
**Likelihood:** MEDIUM  
**Severity:** HIGH  

**Mitigation:** ✅ SHIPPED  
- Budget caps: `AI_MAX_CALLS_PER_MIN=60`, `AI_MAX_DAILY_USD=50`
- Circuit breaker: Opens for 5 minutes on breach
- Automatic fallback to GPT-4o
- Degraded mode with heuristics
- Cost tracking per request

**Owner:** Engineering + Finance  
**SLI:** <90% of daily budget used  
**SLO:** No service degradation >15 min/day  
**Alert:** Daily spend >80% of limit → notify  

**Verification:**
```bash
# Monitor in OpenAI dashboard
https://platform.openai.com/usage
```

**Status:** ✅ MITIGATED

---

## 🟡 MEDIUM RISKS (P2)

### RISK-007: Keyword Cannibalization

**Risk:** Multiple PSE pages target same search intent

**Impact:** MEDIUM (SEO ranking dilution)  
**Likelihood:** MEDIUM (human error)  
**Severity:** MEDIUM  

**Mitigation:** ✅ SHIPPED  
- `scripts/intent_dedupe_check.ts` in CI
- Validates `primaryIntent` uniqueness in `data/pse.json`
- CI fails on duplicates
- Prevents merge of duplicate content

**Owner:** SEO Lead  
**SLI:** 0 duplicate intents in production  
**SLO:** 100% unique intents  
**Alert:** CI failure on duplicate → fix before merge  

**Verification:**
```bash
npx ts-node frontend/scripts/intent_dedupe_check.ts
```

**Status:** ✅ MITIGATED

---

### RISK-008: Accessibility Violations (ADA)

**Risk:** Site not accessible to users with disabilities

**Impact:** MEDIUM (legal risk, user exclusion)  
**Likelihood:** LOW (Next UI components)  
**Severity:** MEDIUM  

**Mitigation:** 🟡 PLANNED  
- NextUI components (ARIA-compliant by default)
- Modal focus traps
- Keyboard navigation
- Axe-core tests (to be added)
- WCAG 2.2 AA target

**Owner:** Engineering  
**SLI:** 0 critical a11y violations  
**SLO:** Pass WCAG 2.2 AA automated scans  
**Alert:** Axe scan failures → fix in next sprint  

**Verification:**
```bash
# Planned: Playwright + axe-core tests
npx playwright test tests/e2e/a11y.spec.ts
```

**Status:** 🟡 PARTIAL (manual review done, automated tests pending)

---

### RISK-009: Confidence Threshold Too Low

**Risk:** Users export low-quality categorizations to QuickBooks

**Impact:** MEDIUM (poor UX, data quality issues)  
**Likelihood:** LOW  
**Severity:** MEDIUM  

**Mitigation:** 🟡 PLANNED  
- `CONF_MIN_EXPORT=0.72` threshold
- Confirm modal for low-confidence exports
- Analytics tracking
- User can override with explicit confirmation

**Owner:** Product + Engineering  
**SLI:** <5% of exports below confidence threshold  
**SLO:** Users satisfied with quality (survey)  
**Alert:** Export block rate >20% → lower threshold  

**Verification:**
```bash
# Set CONF_MIN_EXPORT=0.99
# Try export → should require confirmation
```

**Status:** 🟡 PARTIAL (threshold set, modal UI pending)

---

## 🟢 LOW RISKS (P3)

### RISK-010: Sitemap Not Indexed

**Risk:** Google doesn't discover new PSE pages

**Impact:** LOW (delayed ranking)  
**Likelihood:** LOW  
**Severity:** LOW  

**Mitigation:** ✅ SHIPPED  
- `scripts/ping-sitemap.ts` notifies Google on deploy
- Automatic sitemap generation
- Robots.txt includes sitemap URL
- Weekly sitemap updates

**Owner:** SEO Lead  
**SLI:** 90% of URLs indexed within 7 days  
**SLO:** All URLs indexed within 30 days  
**Alert:** Search Console coverage <70% → investigate  

**Verification:**
```bash
# Check Search Console → Coverage report
https://search.google.com/search-console
```

**Status:** ✅ MITIGATED

---

## 📊 RISK SUMMARY

| Risk ID | Risk | Severity | Status |
|---------|------|----------|--------|
| RISK-001 | CSV Formula Injection | CRITICAL | ✅ MITIGATED |
| RISK-002 | ZIP Bomb DoS | CRITICAL | ✅ MITIGATED |
| RISK-003 | Denial of Service | CRITICAL | ✅ MITIGATED |
| RISK-004 | Data Retention Violation | HIGH | ✅ MITIGATED |
| RISK-005 | XSS Attack | HIGH | ✅ MITIGATED |
| RISK-006 | AI Budget Overrun | HIGH | ✅ MITIGATED |
| RISK-007 | Keyword Cannibalization | MEDIUM | ✅ MITIGATED |
| RISK-008 | Accessibility Violations | MEDIUM | 🟡 PARTIAL |
| RISK-009 | Low Confidence Exports | MEDIUM | 🟡 PARTIAL |
| RISK-010 | Sitemap Not Indexed | LOW | ✅ MITIGATED |

**Overall Posture:** 8/10 MITIGATED (80%)  
**Residual Risk:** LOW  

---

## 🔄 REVIEW SCHEDULE

**Weekly:**
- Review Vercel logs for anomalies
- Check deletion SLA verifier
- Monitor AI health endpoint

**Monthly:**
- Review rate limiting effectiveness
- Audit security headers
- Test maintenance mode
- Review AI budget vs actual spend

**Quarterly:**
- Full security audit
- Update this risk register
- Penetration testing
- Compliance review (SOC 2, GDPR)

---

**Last Review:** November 4, 2025  
**Next Review:** February 4, 2026  
**Reviewed by:** Engineering Team

