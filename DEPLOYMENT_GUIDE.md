# Phase 2b — Production Deployment Guide

**Date:** 2024-10-11  
**Version:** v2.0b  
**Status:** Ready for Production

---

## Pre-Deployment Checklist

### Prerequisites
- [ ] PostgreSQL 15+ running
- [ ] Python 3.9+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment variables configured (`.env` file)
- [ ] Backups enabled and tested

### Security Verification
- [ ] CSRF middleware enabled
- [ ] JWT authentication configured
- [ ] RBAC enforced on all write endpoints
- [ ] Login/webhook routes exempt from CSRF
- [ ] Receipt PDF serving uses safe path handling
- [ ] No secrets in code/logs

---

## Deployment Steps

### 1. Apply Migrations

```bash
cd /path/to/ai-bookkeeper

# Backup database first
pg_dump ai_bookkeeper > backup_pre_006_$(date +%Y%m%d).sql

# Apply migration
alembic upgrade head

# Verify
alembic current
# Expected output: 006_receipt_fields (head)
```

**Migration Details:**
- **ID:** `006_receipt_fields`
- **Down Revision:** `005_notifications`
- **Changes:** Adds `receipt_fields` table for bbox storage

### 2. Restart Services

```bash
# If using systemd
sudo systemctl restart ai-bookkeeper

# If using supervisor
sudo supervisorctl restart ai-bookkeeper

# If running manually
pkill -f "uvicorn app.api.main:app"
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. Verify Routes

**Health Checks:**
```bash
curl http://localhost:8000/healthz
# Expected: 200 OK with uptime, db_ping_ms, etc.

curl http://localhost:8000/readyz
# Expected: 200 OK with db=ok, migrations=ok
```

**New Routes:**
```bash
# Onboarding (requires auth)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/onboarding
# Expected: 200 OK (HTML)

# Receipts (requires auth)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/receipts
# Expected: 200 OK (HTML)

# Analytics (requires auth)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/analytics
# Expected: 200 OK (HTML)

# API Endpoints
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/analytics/last7
# Expected: 200 OK (JSON array)

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/receipts
# Expected: 200 OK (JSON with receipts list)
```

**Performance Verification:**
```bash
# Use Apache Bench or wrk to verify p95 < 300ms
ab -n 100 -c 10 -H "Authorization: Bearer $TOKEN" http://localhost:8000/analytics
```

### 4. Schedule Analytics Rollup Job

**Option A: Automated Setup**
```bash
cd /path/to/ai-bookkeeper
./scripts/setup_analytics_cron.sh
```

**Option B: Manual Setup**
```bash
# Add to crontab
crontab -e

# Add this line (runs daily at 02:00 local)
0 2 * * * cd /path/to/ai-bookkeeper && /usr/bin/python3 jobs/analytics_rollup.py >> logs/analytics_cron.log 2>&1

# Verify
crontab -l | grep analytics
```

**Test Rollup Manually:**
```bash
cd /path/to/ai-bookkeeper
python3 jobs/analytics_rollup.py
# Expected output: ✅ Rollup complete: reports/analytics/daily_YYYY-MM-DD.json
```

### 5. Verify Navigation

Navigate to the UI and confirm:
- [ ] Header shows: Firm, Review, Rules, Audit Log, Receipts, Analytics, Billing, Notifications
- [ ] "Onboarding" link visible (Owner role only)
- [ ] All links navigate correctly
- [ ] No 404 errors

### 6. Security Re-Verification

**CSRF Protection:**
```bash
# Should fail without CSRF token
curl -X POST http://localhost:8000/api/onboarding/complete
# Expected: 403 Forbidden

# Should succeed with valid token
curl -X POST -H "X-CSRF-Token: $CSRF_TOKEN" -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/onboarding/complete
# Expected: 200 or 400 (not 403)
```

**RBAC:**
```bash
# Staff user attempting onboarding
curl -H "Authorization: Bearer $STAFF_TOKEN" http://localhost:8000/api/onboarding/complete
# Expected: 403 Forbidden

# Owner user
curl -H "Authorization: Bearer $OWNER_TOKEN" http://localhost:8000/api/onboarding/complete
# Expected: 200 or 400 (not 403)
```

### 7. Monitoring Setup

**Add Endpoint Checks:**

```python
# In monitoring/checks.py
ENDPOINTS_TO_MONITOR = [
    "/healthz",
    "/readyz",
    "/api/analytics/last7",
    "/api/receipts",
    # ... existing endpoints
]
```

**Prometheus Labels:**
```yaml
# In prometheus.yml
- job_name: 'ai-bookkeeper'
  static_configs:
    - targets: ['localhost:8000']
  metrics_path: '/metrics'
  relabel_configs:
    - source_labels: [__address__]
      target_label: instance
    - source_labels: [__path__]
      target_label: endpoint
```

**Sentry Tags:**
```python
# Already configured in app/api/main.py
# New routes automatically tagged
```

---

## Post-Deployment Verification

### Smoke Tests

**1. Onboarding Flow:**
```bash
# Navigate to /onboarding as Owner
# Complete all 4 steps
# Verify redirect to /review?tenant_id=...
# Check database for new tenant_settings row
```

**2. Receipt Highlights:**
```bash
# Navigate to /receipts
# Select a receipt
# Verify colored bbox overlays appear
# Toggle overlays on/off
# Check hover tooltips
```

**3. Product Analytics:**
```bash
# Navigate to /analytics
# Verify summary cards show data
# Verify daily reports render
# Check sample data banner if no real events
```

### Database Verification

```sql
-- Verify migration applied
SELECT * FROM alembic_version;
-- Expected: 006_receipt_fields

-- Check receipt_fields table
SELECT COUNT(*) FROM receipt_fields;
-- Expected: 0 initially, grows as receipts processed

-- Check tenant_settings for onboarded tenants
SELECT tenant_id, autopost_enabled, autopost_threshold 
FROM tenant_settings 
WHERE tenant_id LIKE 'onboarded-%';
```

### Log Verification

```bash
# Check application logs
tail -f /var/log/ai-bookkeeper/app.log

# Check analytics cron logs (after first run)
tail -f logs/analytics_cron.log

# Check for errors
grep -i error /var/log/ai-bookkeeper/app.log | tail -20
```

---

## Rollback Plan

If issues arise, rollback procedure:

### 1. Database Rollback
```bash
# Revert migration
alembic downgrade 005_notifications

# Verify
alembic current
# Expected: 005_notifications
```

### 2. Code Rollback
```bash
# Revert to previous version
git checkout <previous-tag>

# Reinstall dependencies
pip install -r requirements.txt

# Restart services
sudo systemctl restart ai-bookkeeper
```

### 3. Verify Rollback
```bash
# Ensure /onboarding, /receipts, /analytics return 404 or redirect
# Ensure previous functionality intact
```

---

## Troubleshooting

### Issue: Migration Fails

**Symptoms:** `alembic upgrade head` errors  
**Solution:**
```bash
# Check current version
alembic current

# Check PostgreSQL connection
psql $DATABASE_URL -c "SELECT 1;"

# Check for conflicting tables
psql $DATABASE_URL -c "\dt receipt_fields"

# If table exists, check if migration was partially applied
alembic history
```

### Issue: Routes Return 404

**Symptoms:** `/receipts` or `/analytics` not found  
**Solution:**
```bash
# Verify routes registered
curl http://localhost:8000/docs
# Check if routes appear in OpenAPI spec

# Check logs for import errors
grep -i "import" /var/log/ai-bookkeeper/app.log

# Verify routers included in main.py
grep "receipts.router" app/api/main.py
grep "analytics_api.router" app/api/main.py
```

### Issue: Cron Job Not Running

**Symptoms:** No daily rollups generated  
**Solution:**
```bash
# Check crontab
crontab -l | grep analytics

# Check cron logs
tail -f logs/analytics_cron.log

# Test manually
cd /path/to/ai-bookkeeper
python3 jobs/analytics_rollup.py

# Check permissions
ls -la jobs/analytics_rollup.py

# Check Python path in cron
which python3
```

### Issue: Receipt Bboxes Not Showing

**Symptoms:** Overlays don't appear on PDFs  
**Solution:**
```bash
# Check API response
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/receipts/0001/fields

# Verify fixtures exist
ls -la tests/fixtures/receipts/
ls -la tests/fixtures/receipts_pdf/

# Check database
psql $DATABASE_URL -c "SELECT COUNT(*) FROM receipt_fields;"

# Check browser console for JS errors
# Open DevTools → Console
```

---

## Performance Tuning

### Database Indexes

```sql
-- Verify indexes created by migration
\d receipt_fields

-- Should see:
-- idx_receipt_fields_receipt (receipt_id)
-- idx_receipt_fields_field (field)
```

### Caching

```python
# Receipt fields are cached in DB after first extraction
# No additional caching needed

# Analytics uses file-based storage
# No DB overhead
```

### Load Testing

```bash
# Test onboarding endpoint
ab -n 100 -c 10 -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/onboarding

# Test receipts list
ab -n 100 -c 10 -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/receipts

# Test analytics
ab -n 100 -c 10 -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/analytics/last7

# Target: p95 < 300ms for all routes
```

---

## Success Criteria

Deployment is successful when:

- [x] Migration 006_receipt_fields applied
- [x] All new routes return 200 OK
- [x] Navigation links visible and functional
- [x] Analytics cron job scheduled and tested
- [x] Security (CSRF/JWT/RBAC) verified
- [x] Performance targets met (p95 < 300ms)
- [x] Monitoring configured
- [x] Logs clean (no errors)
- [x] Smoke tests pass
- [x] Rollback plan tested

---

## Next Steps

1. **Capture Screenshots** (see SCREENSHOT_CAPTURE_GUIDE.md)
2. **Enable Pilot Tenants** (see PILOT_ENABLEMENT.md)
3. **Monitor for 24 hours**
4. **Review analytics dashboard daily**

---

**Deployment Contact:** Phase 2b Team  
**Emergency Rollback:** See "Rollback Plan" section above  
**Documentation:** PHASE2B_FINAL_DELIVERY.md

