# Wave-2 Phase 1 De-Mocking — Status Report

**Date:** 2024-10-11  
**Status:** 🚧 IN PROGRESS (Partial Delivery)

---

## Executive Summary

Phase 1 de-mocking is a **large undertaking** involving database migrations, JWT authentication, real API implementations, streaming exports, and comprehensive testing. Given the scope, I'm providing:

1. ✅ **Completed:** Tenant settings persistence + Alembic migration
2. 📋 **Documented:** Detailed implementation plans for remaining items
3. ⏳ **In Progress:** JWT auth, Rules API, Streaming CSV, E2E tests

---

## ✅ Completed: Tenant Settings Persistence

### Alembic Migration

**File:** `alembic/versions/002_tenant_settings.py`

```python
# Creates two new tables:
- tenant_settings (tenant_id PK, autopost_enabled, autopost_threshold, llm_tenant_cap_usd, updated_at, updated_by)
- user_tenants (user_id, tenant_id) for RBAC

# Seeds default tenant settings for 3 pilot tenants
```

**To run:**
```bash
alembic upgrade head
```

### Database Models

**File:** `app/db/models.py`

Added:
- `TenantSettingsDB` — Tenant configuration
- `UserTenantDB` — Staff tenant assignments

### Tenant API (De-mocked)

**File:** `app/api/tenants.py`

**Changes:**
- ✅ `GET /api/tenants` — Now queries `tenant_settings` table
- ✅ `GET /api/tenants/{id}` — Reads from DB, no mocks
- ✅ `POST /api/tenants/{id}/settings` — UPSERT to DB + audit log

**Tests Required:**
```python
tests/test_firm_settings_persist.py:
  - test_toggle_persists_and_reads_back
  - test_threshold_validation (0.80–0.98 enforced)
  - test_budget_updates_write_audit_entry
```

---

## 📋 To Be Implemented: JWT Auth + RBAC

### Requirements

1. **JWT Parsing in `get_current_user()`**
   - Read `Authorization: Bearer <token>` header
   - Decode JWT to extract `user_id`, `role`, `email`
   - Query `user_tenants` for staff assignments

2. **User Table** (if not exists)
   ```sql
   CREATE TABLE users (
       user_id VARCHAR(255) PRIMARY KEY,
       email VARCHAR(255) UNIQUE NOT NULL,
       role VARCHAR(50) NOT NULL,  -- 'owner' or 'staff'
       created_at TIMESTAMP DEFAULT NOW()
   );
   ```

3. **Update RBAC Module**

**File:** `app/ui/rbac.py`

```python
from fastapi import HTTPException, Header
from jose import jwt, JWTError
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract user from JWT token (de-mocked).
    
    Header format: Authorization: Bearer <token>
    """
    if not authorization or not authorization.startswith("Bearer "):
        # Fallback to mock for development
        return User(
            user_id="user-admin-001",
            email="admin@example.com",
            role=Role.OWNER,
            assigned_tenant_ids=[]
        )
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        role = payload.get("role")
        email = payload.get("email")
        
        if not user_id or not role:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Query assigned tenants for staff users
        assigned_tenant_ids = []
        if role == "staff":
            assignments = db.query(UserTenantDB).filter(
                UserTenantDB.user_id == user_id
            ).all()
            assigned_tenant_ids = [a.tenant_id for a in assignments]
        
        return User(
            user_id=user_id,
            email=email,
            role=Role(role),
            assigned_tenant_ids=assigned_tenant_ids
        )
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Tests Required

```python
tests/test_rbac_auth.py:
  - test_owner_sees_all_tenants
  - test_staff_sees_assigned_only
  - test_staff_cannot_update_settings
  - test_invalid_token_rejected
  - test_no_token_falls_back_to_mock
```

### Dependencies

```bash
pip install python-jose[cryptography]
```

---

## 📋 To Be Implemented: Rules Console Real Backend

### Endpoints Needed

**File:** `app/api/rules.py` (new)

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import RuleCandidateDB, RuleVersionDB

router = APIRouter(prefix="/api/rules", tags=["rules"])

@router.get("/candidates")
async def list_candidates(db: Session = Depends(get_db)):
    """List all pending rule candidates from DB."""
    candidates = db.query(RuleCandidateDB).filter(
        RuleCandidateDB.status == "pending"
    ).all()
    
    return [
        {
            "id": c.id,
            "vendor_pattern": c.vendor_pattern,
            "suggested_account": c.suggested_account,
            "evidence": {
                "count": c.evidence_count,
                "precision": c.evidence_precision,
                "std_dev": c.evidence_std_dev
            },
            "created_at": c.created_at.isoformat()
        }
        for c in candidates
    ]

@router.post("/dryrun")
async def dryrun_rule(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """
    Simulate rule promotion and compute impact deltas.
    
    Must NOT mutate DB. Computes:
    - Projected automation rate
    - Reason code deltas
    - Affected transactions count
    """
    candidate = db.query(RuleCandidateDB).filter(
        RuleCandidateDB.id == candidate_id
    ).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # TODO: Compute impact from decision_audit_log
    # - Count transactions matching vendor_pattern
    # - Calculate current auto-post rate
    # - Project new auto-post rate with this rule
    
    return {
        "candidate_id": candidate_id,
        "projected_impact": {
            "automation_rate_before": 0.847,
            "automation_rate_after": 0.862,
            "delta": 0.015
        },
        "reason_deltas": {
            "below_threshold": {"before": 87, "after": 72, "delta": -15}
        },
        "affected_transactions": 15
    }

@router.post("/candidates/{id}/accept")
async def accept_candidate(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Promote candidate to accepted rule."""
    candidate = db.query(RuleCandidateDB).filter(
        RuleCandidateDB.id == id
    ).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Update status
    candidate.status = "accepted"
    candidate.reviewed_by = user.user_id
    candidate.reviewed_at = datetime.now()
    
    # Create new rule version
    # TODO: Merge into rules YAML and create RuleVersionDB entry
    
    # Audit entry
    audit = DecisionAuditLogDB(
        timestamp=datetime.now(),
        action="rule_promoted",
        user_id=user.user_id
    )
    db.add(audit)
    db.commit()
    
    return {"success": True, "candidate_id": id}

@router.post("/candidates/{id}/reject")
async def reject_candidate(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Decline candidate."""
    # Similar to accept but status = "rejected"
    ...

@router.post("/rollback")
async def rollback_rules(
    to_version: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rollback to a previous rule version."""
    # Query RuleVersionDB, restore rules YAML, create audit entry
    ...
```

### Tests Required

```python
tests/test_rules_console_live.py:
  - test_dryrun_no_mutation
  - test_promote_persists_and_version_increments
  - test_rollback_restores_prior_version
```

---

## 📋 To Be Implemented: Streaming CSV Export

### Implementation

**File:** `app/api/audit.py` (new)

```python
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import DecisionAuditLogDB
import csv
from io import StringIO

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("/export.csv")
async def export_audit_csv(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    tenant_id: Optional[str] = None,
    vendor: Optional[str] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Stream audit log as CSV (memory-bounded for large exports).
    
    Uses generator to avoid loading all rows into memory.
    """
    def generate_csv():
        # CSV header
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "timestamp", "tenant_id", "txn_id", "vendor_normalized",
            "action", "not_auto_post_reason", "calibrated_p",
            "threshold_used", "user_id"
        ])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)
        
        # Query with filters
        query = db.query(DecisionAuditLogDB)
        if tenant_id:
            query = query.filter(DecisionAuditLogDB.tenant_id == tenant_id)
        if action:
            query = query.filter(DecisionAuditLogDB.action == action)
        # Add date_from, date_to, vendor filters
        
        # Stream rows in batches
        BATCH_SIZE = 1000
        offset = 0
        while True:
            batch = query.offset(offset).limit(BATCH_SIZE).all()
            if not batch:
                break
            
            for entry in batch:
                writer.writerow([
                    entry.timestamp.isoformat(),
                    entry.tenant_id or "",
                    entry.txn_id or "",
                    entry.vendor_normalized or "",
                    entry.action or "",
                    entry.not_auto_post_reason or "",
                    entry.calibrated_p or "",
                    entry.threshold_used or "",
                    entry.user_id or ""
                ])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)
            
            offset += BATCH_SIZE
    
    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=audit_export_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )
```

### Tests Required

```python
tests/test_audit_export_stream.py:
  - test_streams_large_export (100k rows, memory < 100MB)
  - test_filters_restrict_rows
  - test_csv_headers_and_columns
```

---

## 📋 E2E Tests with Fixtures

### Fixture Generation

**File:** `tests/fixtures/seed_phase1_fixtures.py`

```python
"""
Seed DB with realistic fixtures for E2E testing.

Generates:
- 3 tenants with settings
- 100 transactions per tenant
- 50 rule candidates
- 500 audit log entries
"""
from app.db.session import SessionLocal
from app.db.models import (
    TenantSettingsDB, TransactionDB, RuleCandidateDB,
    DecisionAuditLogDB
)
from datetime import datetime, timedelta
import random

def seed_fixtures():
    db = SessionLocal()
    
    # Seed tenants
    tenants = [
        {"tenant_id": "pilot-acme-corp-082aceed", "autopost_enabled": False, "autopost_threshold": 0.90},
        {"tenant_id": "pilot-beta-accounting-inc-31707447", "autopost_enabled": True, "autopost_threshold": 0.92},
        {"tenant_id": "pilot-gamma-llc-abc123", "autopost_enabled": False, "autopost_threshold": 0.90}
    ]
    
    for t in tenants:
        settings = TenantSettingsDB(**t)
        db.merge(settings)
    
    # Seed transactions, candidates, audit entries...
    # (implementation details)
    
    db.commit()
    db.close()

if __name__ == "__main__":
    seed_fixtures()
    print("✅ Fixtures seeded")
```

### E2E Tests

```python
tests/test_e2e_firm_demock.py:
  - test_firm_page_loads_from_db
  - test_settings_update_persists
  - test_p95_render_under_300ms

tests/test_e2e_rules_demock.py:
  - test_rules_page_loads_from_db
  - test_dryrun_uses_real_data
  - test_promote_creates_version

tests/test_e2e_audit_demock.py:
  - test_audit_page_loads_from_db
  - test_filters_query_db
  - test_csv_export_streams
```

---

## Estimated Effort Remaining

| Task | Estimated Hours | Priority |
|------|-----------------|----------|
| JWT Auth + RBAC | 4-6 hours | HIGH |
| Rules Console API | 6-8 hours | HIGH |
| Streaming CSV Export | 3-4 hours | MEDIUM |
| E2E Tests + Fixtures | 4-6 hours | MEDIUM |
| Performance Validation | 2-3 hours | LOW |

**Total:** 19-27 hours of focused development

---

## Acceptance Blockers

**To mark Phase 1 as Accepted:**

1. ✅ Tenant settings persist to DB (DONE)
2. ⏳ JWT auth implemented (IN PROGRESS)
3. ⏳ Rules Console wired to real backend (PLANNED)
4. ⏳ Audit CSV streams (PLANNED)
5. ⏳ E2E tests green with fixtures (PLANNED)
6. ⏳ P95 < 300ms validated (PLANNED)

---

## Next Steps

**Immediate (Next Session):**
1. Complete JWT auth implementation
2. Wire Rules Console to real DB queries
3. Implement streaming CSV export
4. Seed fixtures and run E2E tests
5. Measure performance (p95)

**Then:** Phase 2 skeleton with mocks

---

## Artifacts Delivered (So Far)

- ✅ `alembic/versions/002_tenant_settings.py` — Migration
- ✅ `app/db/models.py` — Updated with new tables
- ✅ `app/api/tenants.py` — De-mocked tenant API
- 📋 `WAVE2_PHASE1_DEMOCK_STATUS.md` — This document

---

**Status:** 🚧 Partial Delivery (1/5 items complete)  
**Recommendation:** Continue with JWT auth next, then Rules API, then streaming CSV.

---

**Document Version:** 1.0  
**Last Updated:** 2024-10-11

