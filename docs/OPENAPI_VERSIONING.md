# OpenAPI Versioning Policy

**Purpose:** Maintain API stability for ChatGPT GPT Actions and external integrations.

---

## Version Files

**Current Spec:**
- `/openapi.json` - Live, auto-generated from FastAPI
- `/docs/openapi-latest.json` - Snapshot of current spec

**Versioned Specs:**
- `/docs/openapi-v1.0.json` - Initial release (October 2025)
- `/docs/openapi-v1.1.json` - Future minor update
- `/docs/openapi-v2.0.json` - Future breaking change

---

## Semantic Versioning

### Major Version (X.0)

**When to bump:**
- Breaking changes to existing endpoints
- Removed endpoints
- Required field changes (add required field, remove optional field)
- Response schema breaking changes

**Examples:**
- Change `/api/billing/status` response structure
- Remove `/api/post/approve` endpoint
- Make `txn_id` required in commit request

### Minor Version (X.Y)

**When to bump:**
- New endpoints added
- New optional fields in requests
- New fields in responses (backward compatible)
- New error codes

**Examples:**
- Add `/api/analytics/forecasting`
- Add optional `metadata` field to commit request
- Add `forecast_confidence` to billing status response

### No Version Bump

**When NOT to bump:**
- Internal implementation changes
- Bug fixes that restore intended behavior
- Documentation updates
- Performance improvements

---

## How to Publish a New Version

### Step 1: Generate New Spec

```bash
# Fetch current OpenAPI spec
curl http://localhost:8000/openapi.json > docs/openapi-vX.Y.json

# Or from production
curl https://YOUR_DOMAIN/openapi.json > docs/openapi-vX.Y.json
```

### Step 2: Update openapi-latest.json

```bash
# Copy to latest
cp docs/openapi-vX.Y.json docs/openapi-latest.json
```

### Step 3: Commit Both Files

```bash
git add docs/openapi-vX.Y.json docs/openapi-latest.json
git commit -m "feat(api): bump OpenAPI to vX.Y - added /new/endpoint"
git push origin main
```

### Step 4: Update GPT Actions (if GPT configured)

1. Go to ChatGPT → Your GPT → Configure → Actions
2. Click existing action → Edit schema
3. Re-import from URL: `https://YOUR_DOMAIN/openapi.json`
4. Verify new endpoints appear
5. Test connection

---

## Backward Compatibility Policy

### Minor Versions (Same Major)

**Guaranteed:**
- All existing endpoints continue to work
- All existing required fields accepted
- All existing response fields present
- All existing error codes returned

**May Change:**
- New optional fields in requests (ignored if not sent)
- New fields in responses (GPT should ignore unknown fields)
- New endpoints (GPT may not use them yet)

### Major Versions (Breaking Changes)

**Before Breaking Change:**
1. Announce deprecation (30 days notice)
2. Add new endpoint/version alongside old
3. Document migration path
4. Update GPT configuration

**Example Migration:**
```
Old: POST /api/post/commit
New: POST /v2/post/commit
```

Maintain old endpoint for 90 days, then remove.

---

## CI Guard

### GitHub Action: openapi_version_guard.yml

**Triggers:**
- On pull request to `main`
- On push to `main`

**Checks:**
1. Compare `/openapi.json` to `/docs/openapi-latest.json`
2. If different, ensure `/docs/openapi-v*.json` added in commit
3. Fail PR if spec changed without version bump

**Manual Override:**
- Add `[skip-openapi-check]` to commit message for docs-only changes

---

## GPT Actions Integration

### Initial Setup

When creating GPT Actions:
1. Import from: `https://YOUR_DOMAIN/openapi.json`
2. Save versioned copy to `gpt_config/openapi-v1.0.json` (local backup)

### When API Changes

**Minor Update:**
1. Re-import OpenAPI in GPT Actions
2. Test all conversation starters
3. Update instructions if new endpoints useful

**Major Update:**
1. Review breaking changes
2. Update GPT instructions
3. Update conversation starters
4. Re-import OpenAPI
5. **Test thoroughly** before deploying GPT

---

## Version History

### v1.0 (2025-10-17) - Initial Release

**Endpoints:**
- Auth: `/api/auth/login`, `/api/auth/signup`, `/api/auth/logout`, `/api/auth/me`
- Billing: `/api/billing/status`, `/api/billing/create_checkout_session`, `/api/billing/portal_link`
- QBO: `/api/auth/qbo/start`, `/api/auth/qbo/callback`, `/api/qbo/status`, `/api/qbo/journalentry`
- Post: `/api/post/propose`, `/api/post/approve`, `/api/post/commit`
- Rules: `/api/rules/candidates`, `/api/rules/dryrun`, `/api/rules/versions`, `/api/rules/rollback`
- Privacy: `/api/privacy/consent`, `/api/privacy/labels/export`, `/api/privacy/labels/purge`
- Actions: `/actions` (GPT discovery)
- Health: `/healthz`, `/readyz`

**Error Codes:**
- `402 ENTITLEMENT_REQUIRED` - No active subscription
- `429 FREE_CAP_EXCEEDED` - Daily free cap reached
- `400 UNBALANCED_JE` - Journal entry not balanced
- `401 QBO_UNAUTHORIZED` - QBO not connected
- `422 QBO_VALIDATION` - QBO rejected entry
- `502 QBO_UPSTREAM` - QBO API unavailable

---

## Migration Examples

### Example 1: Adding Optional Field (Minor Bump)

**Before (v1.0):**
```json
POST /api/post/commit
{
  "approvals": [...]
}
```

**After (v1.1):**
```json
POST /api/post/commit
{
  "approvals": [...],
  "dry_run": true  // NEW optional field
}
```

**Impact:** None. Old clients continue to work.

### Example 2: Breaking Change (Major Bump)

**Before (v1.x):**
```json
GET /api/billing/status
{
  "plan": "starter",
  "active": true
}
```

**After (v2.0):**
```json
GET /api/billing/status
{
  "subscription": {  // BREAKING: nested structure
    "plan": "starter",
    "active": true
  }
}
```

**Impact:** Old clients break. Requires migration.

**Migration Path:**
1. Deploy v2.0 API
2. Maintain v1.x at `/v1/billing/status` for 90 days
3. Update GPT Actions to use v2.0
4. Remove v1.x endpoint after grace period

---

## Testing Versioned Specs

```bash
# Compare specs
diff docs/openapi-v1.0.json docs/openapi-latest.json

# Validate spec
python scripts/check_openapi_frozen.py

# Test GPT import
# (Manual: Import URL in ChatGPT GPT Builder)
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-17  
**Current API Version:** v1.0

