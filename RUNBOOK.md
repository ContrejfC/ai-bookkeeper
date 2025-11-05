# AI Bookkeeper - Operations Runbook

## 🎯 Quick Reference

**Production URL:** https://ai-bookkeeper.app  
**Admin Email:** privacy@ai-bookkeeper.app  
**Last Updated:** November 4, 2025  

---

## 🚨 EMERGENCY PROCEDURES

### Enable Maintenance Mode (Immediate Shutdown)

**When to use:**
- Under active attack (DoS, abuse)
- Critical bug discovered
- Emergency database maintenance
- Incident response

**Steps:**
1. Go to Vercel: https://vercel.com/contrejfcs-projects/ai-bookkeeper/settings/environment-variables
2. Find or add `MAINTENANCE_MODE`
3. Set value to `true`
4. Wait 30-60 seconds for edge propagation

**Effect:**
- All POST `/api/free/categorizer/*` routes return HTTP 503
- Response: `{ code: "MAINTENANCE", retryAfterSec: 120 }`
- GET requests (HTML pages) still work
- Users see friendly "temporarily unavailable" message

**Disable:**
1. Set `MAINTENANCE_MODE=false` or remove variable
2. Wait 30-60 seconds

**Verify:**
```bash
# Test maintenance mode active
curl -X POST https://ai-bookkeeper.app/api/free/categorizer/upload \
  -F "file=@test.csv"

# Expected: HTTP 503 with Retry-After: 120

# Test disabled
# Expected: HTTP 200 or 400 (normal behavior)
```

---

## 🔐 SECURITY OPERATIONS

### Rotate Admin Tokens

**ADMIN_PURGE_TOKEN** (for cron purge endpoint):
1. Generate new token: `openssl rand -hex 32`
2. Update in Vercel environment variables
3. Update in GitHub Secrets if used in CI
4. Old token invalid immediately

**ADMIN_VERIFY_TOKEN** (for deletion SLA verifier):
1. Generate new token: `openssl rand -hex 32`
2. Update in Vercel: `ADMIN_VERIFY_TOKEN`
3. Update in CI: GitHub Secrets → `ADMIN_VERIFY_TOKEN`
4. Test: 
```bash
curl -X POST https://ai-bookkeeper.app/api/admin/verify-deletions \
  -H "Authorization: Bearer NEW_TOKEN" | jq .
```

**Rotation Schedule:** Every 90 days or after security incident

### Monitor Rate Limiting

**Check logs:**
```
https://vercel.com/contrejfcs-projects/ai-bookkeeper/logs
```

**Look for:**
```
[RateLimit] No Upstash configured, allowing request from abc123...
429 responses with RATE_LIMIT_EXCEEDED
```

**Adjust limits if needed:**
```bash
# In env.example, then update Vercel:
FREE_API_CONCURRENCY_PER_IP=2    # Concurrent requests per IP
# Middleware hardcoded: 20 req/min/IP
```

**Enable Distributed Rate Limiting (Upstash):**
1. Sign up: https://upstash.com/
2. Create Redis database
3. Copy REST URL and token
4. Add to Vercel:
   - `UPSTASH_REDIS_REST_URL=https://...`
   - `UPSTASH_REDIS_REST_TOKEN=...`
5. Redeploy

### Review Security Headers

**Check live site:**
```bash
curl -I https://ai-bookkeeper.app/free/categorizer
```

**Expected headers:**
```
content-security-policy: default-src 'self'; img-src 'self' data: blob:; ...
strict-transport-security: max-age=31536000; includeSubDomains
x-frame-options: DENY
x-content-type-options: nosniff
referrer-policy: strict-origin-when-cross-origin
permissions-policy: camera=(), microphone=(), geolocation=()
```

---

## 🗑️ DATA RETENTION & DELETION

### Verify Deletion SLA (24 Hours)

**Run deletion verifier:**
```bash
curl -s -X POST https://ai-bookkeeper.app/api/admin/verify-deletions \
  -H "Authorization: Bearer YOUR_ADMIN_VERIFY_TOKEN" | jq .
```

**Expected output:**
```json
{
  "p50Minutes": 360,      // Median age: 6 hours
  "p95Minutes": 1200,     // 95th percentile: 20 hours
  "staleCount": 0,        // Files older than 24h: NONE
  "total": 15,            // Total files
  "retentionHours": 24,
  "retentionMinutes": 1440,
  "timestamp": "2025-11-04T..."
}
```

**⚠️ Alert if:**
- `staleCount > 0` - Files not being deleted on time
- `p95Minutes > 1440` - 95th percentile exceeds 24 hours

**Fix:**
1. Check cron job is running: https://vercel.com/contrejfcs-projects/ai-bookkeeper/cron
2. Check purge endpoint logs
3. Manually trigger purge:
```bash
curl -X POST https://ai-bookkeeper.app/api/admin/purge-ephemeral \
  -H "Authorization: Bearer YOUR_ADMIN_PURGE_TOKEN"
```

### Manual Data Purge

**Emergency purge (if automated fails):**
```bash
# SSH to server (if applicable) or use Vercel CLI
# rm -rf /tmp/free_uploads/*

# Or trigger via API:
curl -X POST https://ai-bookkeeper.app/api/admin/purge-ephemeral \
  -H "Authorization: Bearer $ADMIN_PURGE_TOKEN"
```

---

## 🤖 LLM & AI OPERATIONS

### Monitor AI Budget

**Check current usage:**
```bash
curl -s https://ai-bookkeeper.app/api/ai/health | jq '.'
```

**Response includes:**
```json
{
  "ok": true,
  "model": "gpt-5-chat-latest",
  "fallback": false,
  "latency_ms": 1234,
  "config": {
    "primary": "gpt-5-chat-latest",
    "fallback": "gpt-4o"
  }
}
```

**Budget limits (configured in env):**
```bash
AI_MAX_CALLS_PER_MIN=60        # Call rate limit
AI_MAX_DAILY_USD=50            # Daily spend cap
AI_CIRCUIT_OPEN_SEC=300        # 5 min circuit breaker
```

**When limits exceeded:**
- First: Falls back to GPT-4o
- Then: Circuit breaker opens for 5 minutes
- Returns: `{ llm_degraded: true }` with heuristic response

**Adjust limits:**
1. Update in Vercel environment variables
2. Redeploy (automatic on env change)
3. Monitor for 24 hours

### Adjust Export Confidence Threshold

**Current threshold:**
```bash
CONF_MIN_EXPORT=0.72    # 72% confidence minimum
```

**When to raise:**
- Too many low-quality exports
- User complaints about accuracy
- Compliance requirements

**When to lower:**
- Too restrictive (users can't export)
- False rejections
- Model accuracy improves

**How to change:**
1. Update Vercel: `CONF_MIN_EXPORT=0.80` (for 80%)
2. Redeploy
3. Monitor export block rate in analytics

---

## 📊 MONITORING & DIAGNOSTICS

### Run Comprehensive Smoke Test

```bash
curl -s https://ai-bookkeeper.app/api-smoke | jq '.'
```

**Expected:**
```json
{
  "assertions": {
    "privacyDate": true,
    "termsDate": true,
    "soc2Copy": true,
    "apiUpload405": true,
    "uiControls": true
  },
  "version_sha": "abc1234"
}
```

**⚠️ Alert if any assertion is `false`**

### Check AI Health

```bash
curl -s https://ai-bookkeeper.app/api/ai/health | jq '{ok, model, fallback, latency_ms}'
```

**Healthy:**
```json
{
  "ok": true,
  "model": "gpt-5-chat-latest",
  "fallback": false,
  "latency_ms": 1200
}
```

**Degraded (acceptable):**
```json
{
  "ok": true,
  "model": "gpt-4o",
  "fallback": true,
  "latency_ms": 890
}
```

**Broken:**
```json
{
  "ok": false,
  "error": "missing_api_key"
}
```

### Check Deletion SLA

**Run daily or when issues suspected:**
```bash
curl -s -X POST https://ai-bookkeeper.app/api/admin/verify-deletions \
  -H "Authorization: Bearer $ADMIN_VERIFY_TOKEN" | jq '.'
```

**SLA compliance:**
- `p95Minutes ≤ 1440` (24 hours)
- `staleCount === 0` (no overdue files)

---

## 🔧 COMMON TASKS

### Update Environment Variable

1. Go to Vercel: https://vercel.com/contrejfcs-projects/ai-bookkeeper/settings/environment-variables
2. Find variable or click "Add New"
3. Update value
4. Check "Production"
5. Click "Save"
6. Wait 30-60 seconds for propagation (automatic redeploy)

### Trigger Manual Deployment

**Option A - GitHub Actions:**
```
https://github.com/ContrejfC/ai-bookkeeper/actions
→ Deploy Prod (Monorepo)
→ Run workflow
```

**Option B - Vercel Dashboard:**
```
https://vercel.com/contrejfcs-projects/ai-bookkeeper
→ Deployments
→ ... → Redeploy
```

### Check Deployment Status

```
https://github.com/ContrejfC/ai-bookkeeper/actions
```

**Look for:**
- ✅ Green checkmark = Success
- 🔄 Yellow circle = In progress
- ❌ Red X = Failed (click for logs)

### Review Logs

**Vercel logs:**
```
https://vercel.com/contrejfcs-projects/ai-bookkeeper/logs
```

**Filter by:**
- Errors only
- Specific route
- Time range

---

## 📈 SEO OPERATIONS

### Ping Google After Sitemap Updates

**Automatic (in CI):**
```bash
# Runs in GitHub Actions after deploy
SITEMAP_URL=https://ai-bookkeeper.app/sitemap.xml \
  npx ts-node scripts/ping-sitemap.ts
```

**Manual:**
```bash
cd frontend
SITEMAP_URL=https://ai-bookkeeper.app/sitemap.xml \
  npx ts-node scripts/ping-sitemap.ts
```

### Check for Duplicate Intents

**Run locally:**
```bash
cd frontend
npx ts-node scripts/intent_dedupe_check.ts
```

**Expected:**
```
✅ Intent deduplication check passed
   Checked 3 pages, 3 unique intents
```

**If duplicates found:**
1. Edit `frontend/data/pse.json`
2. Fix duplicate `primaryIntent` values
3. Commit and push
4. CI will validate

### Noindex Low Performers

**To noindex a PSE page:**
1. Edit `frontend/data/pse.json`
2. Find the page
3. Set `"status": "noindex"`
4. Commit and push

**Effect:**
- Page excluded from sitemap.xml
- Renders `<meta name="robots" content="noindex,follow">`
- Google stops indexing within days

**To reindex:**
1. Set `"status": "active"`
2. Commit and push
3. Request reindexing in Search Console

---

## 🧪 TESTING & VALIDATION

### Run Security Smoke Tests

**After any deploy:**
```bash
# 1. Security headers
curl -I https://ai-bookkeeper.app/free/categorizer | grep -Ei 'content-security|strict-transport|x-frame'

# 2. Rate limiting (safe - just 5 requests)
for i in {1..5}; do
  curl -s -o /dev/null -w "%{http_code}\n" https://ai-bookkeeper.app/api/ai/health
done

# 3. Maintenance mode test (don't run in prod!)
# Set MAINTENANCE_MODE=true → test → set false

# 4. AI health
curl -s https://ai-bookkeeper.app/api/ai/health | jq '{ok, model}'

# 5. Deletion SLA
curl -s -X POST https://ai-bookkeeper.app/api/admin/verify-deletions \
  -H "Authorization: Bearer $ADMIN_VERIFY_TOKEN" | jq '{p95Minutes, staleCount}'
```

### Run Full CI Smoke Tests Locally

```bash
cd frontend

# Intent deduplication
npx ts-node scripts/intent_dedupe_check.ts

# Sitemap ping
SITEMAP_URL=https://ai-bookkeeper.app/sitemap.xml \
  npx ts-node scripts/ping-sitemap.ts

# Build
npm run build

# (E2E tests require Playwright browsers)
```

---

## 📋 ENVIRONMENT VARIABLES REFERENCE

### Critical (Required)
```bash
NEXT_PUBLIC_SITE_URL=https://ai-bookkeeper.app
OPENAI_API_KEY=sk-proj-...
```

### Security
```bash
FREE_MAX_FILE_MB=10
FREE_MAX_UNZIP_MB=50
FREE_API_CONCURRENCY_PER_IP=2
MAINTENANCE_MODE=false
```

### AI/LLM
```bash
OPENAI_MODEL=gpt-5-chat-latest
OPENAI_FALLBACK_MODEL=gpt-4o
AI_MAX_CALLS_PER_MIN=60
AI_MAX_DAILY_USD=50
AI_CIRCUIT_OPEN_SEC=300
CONF_MIN_EXPORT=0.72
```

### Admin
```bash
ADMIN_PURGE_TOKEN=your-secure-token-32-chars-min
ADMIN_VERIFY_TOKEN=your-secure-token-32-chars-min
```

### Privacy
```bash
FREE_RETENTION_HOURS=24
IP_HASH_SALT=your-random-salt-32-chars-min
```

### Rate Limiting (Optional)
```bash
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...
```

### SEO
```bash
SITEMAP_URL=https://ai-bookkeeper.app/sitemap.xml
SOC2_STATUS=aligned
```

---

## 🔍 TROUBLESHOOTING

### Issue: High Rate of 429 Errors

**Symptoms:** Users reporting "too many requests"

**Diagnosis:**
```bash
# Check Vercel logs for rate limit triggers
# Look for patterns: same IP, time of day
```

**Solutions:**
1. **If legitimate traffic spike:**
   - Temporarily disable rate limiting (comment out in middleware)
   - Or increase limit in code (requires redeploy)
   
2. **If attack/abuse:**
   - Keep rate limiting
   - Consider adding IP to blocklist
   - Enable maintenance mode if severe

### Issue: Deletion SLA Violation

**Symptoms:** `staleCount > 0` or `p95Minutes > 1440`

**Diagnosis:**
```bash
curl -s -X POST https://ai-bookkeeper.app/api/admin/verify-deletions \
  -H "Authorization: Bearer $TOKEN" | jq '.p95Minutes, .staleCount'
```

**Solutions:**
1. Check cron job status in Vercel
2. Manually trigger purge endpoint
3. Check disk space (if self-hosted)
4. Verify `FREE_RETENTION_HOURS` is set correctly

### Issue: AI Budget Exceeded

**Symptoms:** Users see "Service temporarily degraded"

**Diagnosis:**
```bash
curl -s https://ai-bookkeeper.app/api/ai/health | jq '.model'
# If returns "degraded-heuristic" → budget exceeded
```

**Solutions:**
1. **Increase daily budget:**
   ```bash
   AI_MAX_DAILY_USD=100  # Raise from 50 to 100
   ```

2. **Increase call rate:**
   ```bash
   AI_MAX_CALLS_PER_MIN=120  # Raise from 60 to 120
   ```

3. **Check OpenAI usage:**
   - https://platform.openai.com/usage
   - Verify actual costs vs estimates

### Issue: CSV Download Contains Formulas

**Symptoms:** Excel executes formulas in downloaded CSV

**Diagnosis:** Sanitization not applied

**Solutions:**
1. Check `frontend/lib/csv_sanitize.ts` is imported
2. Check `sanitizeCsvField()` is called in export path
3. Verify build includes latest code
4. Test locally with malicious CSV

### Issue: ZIP Upload Rejected

**Symptoms:** `ZIP_SAFETY_VIOLATION` error

**Diagnosis:** Check error message:
- "too many files" → Limit: 500 files
- "total uncompressed size" → Limit: 50MB
- "nested archive" → Remove .zip inside .zip
- "unsafe path" → Remove ../ from filenames

**Solutions:**
1. Ask user to extract and upload files individually
2. Or adjust limits:
   ```bash
   FREE_MAX_UNZIP_MB=100  # Increase if legitimate
   ```

---

## 📊 METRICS & ALERTING

### Key SLIs (Service Level Indicators)

**Availability:**
- **Target:** 99.9% uptime
- **Measurement:** `/api-smoke` returns all assertions true
- **Alert:** Any assertion false for >5 minutes

**Deletion SLA:**
- **Target:** p95 ≤ 1440 minutes (24 hours)
- **Measurement:** `/api/admin/verify-deletions`
- **Alert:** `staleCount > 0` or `p95Minutes > 1440`

**AI Health:**
- **Target:** GPT-5 primary, fallback allowed
- **Measurement:** `/api/ai/health`
- **Alert:** `ok: false` for >15 minutes

**Security:**
- **Target:** CSP + 5 other headers present
- **Measurement:** Manual curl checks
- **Alert:** Any header missing

### Recommended Alert Rules

**Uptime Monitoring (e.g., UptimeRobot, Pingdom):**
```
URL: https://ai-bookkeeper.app/api-smoke
Interval: 5 minutes
Alert: Response not 200 OR any assertion false
```

**Deletion SLA (daily cron):**
```
URL: https://ai-bookkeeper.app/api/admin/verify-deletions
Method: POST
Header: Authorization: Bearer ...
Schedule: Daily at 00:00 UTC
Alert: staleCount > 0 OR p95Minutes > 1440
```

**AI Health (every 15 min):**
```
URL: https://ai-bookkeeper.app/api/ai/health
Interval: 15 minutes
Alert: ok === false for >2 consecutive checks
```

---

## 🚀 DEPLOYMENT CHECKLIST

**Pre-Deploy:**
- [ ] Code reviewed
- [ ] Tests passing locally
- [ ] Environment variables verified
- [ ] No secrets in code

**Deploy:**
- [ ] Push to `main` branch
- [ ] GitHub Actions triggered
- [ ] Wait for green checkmark (3-5 min)

**Post-Deploy:**
- [ ] Run `/api-smoke` → all assertions true
- [ ] Run `/api/ai/health` → ok: true
- [ ] Test Free Categorizer → works
- [ ] Check security headers → all present
- [ ] Run deletion verifier → p95 ≤ 1440

---

## 📞 ESCALATION

### Severity Levels

**P0 - Critical (Immediate Response):**
- Site down (>5 min)
- Data breach
- Security incident
- **Action:** Enable maintenance mode, investigate

**P1 - High (1 hour response):**
- Feature broken
- Deletion SLA violated
- AI budget exhausted
- **Action:** Review logs, apply fix, deploy

**P2 - Medium (4 hour response):**
- Performance degraded
- Rate limiting too aggressive
- Minor UI issues
- **Action:** Schedule fix in next deploy

**P3 - Low (24 hour response):**
- Feature requests
- Documentation updates
- SEO optimizations
- **Action:** Add to backlog

### Contact Information

**Engineering:**
- GitHub: https://github.com/ContrejfC/ai-bookkeeper
- Issues: https://github.com/ContrejfC/ai-bookkeeper/issues

**Security:**
- Email: security@ai-bookkeeper.app
- Disclosure: Follow responsible disclosure

**Privacy:**
- Email: privacy@ai-bookkeeper.app
- Data requests: GDPR/CCPA compliance

---

**Last Updated:** November 4, 2025  
**Version:** 2.1  
**Maintained by:** Engineering Team

