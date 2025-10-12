"""
Tests for Rules Console Live Backend (Wave-2 Phase 1).

Tests:
- test_dryrun_no_mutation
- test_promote_persists_and_versions_increment
- test_rollback_restores_prior_version
- test_conflict_returns_error_no_mutation
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.main import app
from app.db.session import SessionLocal
from app.db.models import RuleCandidateDB, RuleVersionDB, DecisionAuditLogDB


client = TestClient(app)


@pytest.fixture(scope="module")
def db():
    """Database session for tests."""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def auth_token(db):
    """Get auth token for tests."""
    response = client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "magic_token": "dev"
    })
    return response.json()["token"]


@pytest.fixture(scope="module")
def seed_test_data(db):
    """Seed test data for rules tests."""
    # Create rule candidates
    candidates = [
        RuleCandidateDB(
            id="test-cand-001",
            vendor_pattern="office depot*",
            suggested_account="Office Supplies",
            evidence_count=24,
            evidence_precision=0.96,
            evidence_std_dev=0.042,
            status="pending"
        ),
        RuleCandidateDB(
            id="test-cand-002",
            vendor_pattern="amazon.com*",
            suggested_account="Office Supplies",
            evidence_count=47,
            evidence_precision=0.87,
            evidence_std_dev=0.128,
            status="pending"
        )
    ]
    
    for cand in candidates:
        db.merge(cand)
    
    # Create audit entries for dry-run testing
    audit_entries = [
        DecisionAuditLogDB(
            txn_id=f"txn-test-{i}",
            vendor_normalized="office depot" if i % 2 == 0 else "amazon.com",
            action="reviewed",
            not_auto_post_reason="below_threshold",
            calibrated_p=0.85,
            tenant_id="pilot-acme-corp-082aceed"
        )
        for i in range(20)
    ]
    
    # Add some auto-posted for baseline
    for i in range(80):
        audit_entries.append(
            DecisionAuditLogDB(
                txn_id=f"txn-auto-{i}",
                vendor_normalized="other vendor",
                action="auto_posted",
                calibrated_p=0.95,
                tenant_id="pilot-acme-corp-082aceed"
            )
        )
    
    for entry in audit_entries:
        db.add(entry)
    
    db.commit()
    
    yield
    
    # Cleanup (optional)


def test_dryrun_no_mutation(db, auth_token, seed_test_data):
    """
    Verify dry-run computes impact WITHOUT mutating database.
    
    Checks:
    - Candidate status unchanged
    - No new versions created
    - Dry-run audit entry created (allowed)
    - Response contains before/after/deltas
    """
    # Count before
    candidate_count_before = db.query(RuleCandidateDB).count()
    version_count_before = db.query(RuleVersionDB).count()
    
    candidate = db.query(RuleCandidateDB).filter_by(id="test-cand-001").first()
    status_before = candidate.status if candidate else None
    
    # Execute dry-run
    response = client.post(
        "/api/rules/dryrun",
        json={
            "candidate_ids": ["test-cand-001"],
            "tenant_id": "pilot-acme-corp-082aceed"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "before" in data
    assert "after" in data
    assert "deltas" in data
    assert "affected_txn_ids" in data
    
    assert "automation_rate" in data["before"]
    assert "automation_rate" in data["after"]
    assert "automation_rate" in data["deltas"]
    
    # Verify NO MUTATION
    candidate_count_after = db.query(RuleCandidateDB).count()
    version_count_after = db.query(RuleVersionDB).count()
    
    candidate_after = db.query(RuleCandidateDB).filter_by(id="test-cand-001").first()
    status_after = candidate_after.status if candidate_after else None
    
    assert candidate_count_before == candidate_count_after, "Candidate count changed!"
    assert version_count_before == version_count_after, "Version count changed!"
    assert status_before == status_after, "Candidate status changed!"
    
    # Verify automation rate increase projected
    assert data["deltas"]["automation_rate"] > 0, "Automation rate should increase"
    
    print(f"✅ Dry-run NO MUTATION verified")
    print(f"   Before automation: {data['before']['automation_rate']}")
    print(f"   After automation: {data['after']['automation_rate']}")
    print(f"   Delta: +{data['deltas']['automation_rate']}")


def test_promote_persists_and_versions_increment(db, auth_token, seed_test_data):
    """
    Verify rule promotion creates version and updates status.
    
    Checks:
    - Candidate status changes to 'accepted'
    - New version created
    - Version is active
    - Audit entry created
    """
    version_count_before = db.query(RuleVersionDB).count()
    
    # Promote candidate
    response = client.post(
        "/api/rules/candidates/test-cand-002/accept",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] == True
    assert "version_id" in data
    assert data["candidate_id"] == "test-cand-002"
    
    # Verify candidate updated
    candidate = db.query(RuleCandidateDB).filter_by(id="test-cand-002").first()
    assert candidate.status == "accepted"
    assert candidate.reviewed_by == "user-admin-001"
    assert candidate.reviewed_at is not None
    
    # Verify version created
    version_count_after = db.query(RuleVersionDB).count()
    assert version_count_after == version_count_before + 1
    
    new_version = db.query(RuleVersionDB).filter_by(version_id=data["version_id"]).first()
    assert new_version is not None
    assert new_version.is_active == True
    
    # Verify audit entry
    audit = db.query(DecisionAuditLogDB).filter_by(action="rule_promoted").order_by(
        DecisionAuditLogDB.timestamp.desc()
    ).first()
    assert audit is not None
    assert audit.user_id == "user-admin-001"
    
    print(f"✅ Promotion persisted successfully")
    print(f"   New version: {data['version_id']}")


def test_rollback_restores_prior_version(db, auth_token, seed_test_data):
    """
    Verify rollback changes active version.
    
    Checks:
    - Target version becomes active
    - Previous active version deactivated
    - Audit entry created
    """
    # Create two versions
    v1 = RuleVersionDB(
        version_id="test-v1",
        rules_yaml="# Version 1",
        created_by="user-admin-001",
        is_active=False
    )
    v2 = RuleVersionDB(
        version_id="test-v2",
        rules_yaml="# Version 2",
        created_by="user-admin-001",
        is_active=True
    )
    
    db.add(v1)
    db.add(v2)
    db.commit()
    
    # Rollback to v1
    response = client.post(
        "/api/rules/rollback",
        json={"to_version": "test-v1"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] == True
    assert data["version_id"] == "test-v1"
    assert data["old_version_id"] == "test-v2"
    
    # Verify v1 is now active
    v1_after = db.query(RuleVersionDB).filter_by(version_id="test-v1").first()
    v2_after = db.query(RuleVersionDB).filter_by(version_id="test-v2").first()
    
    assert v1_after.is_active == True
    assert v2_after.is_active == False
    
    # Verify audit entry
    audit = db.query(DecisionAuditLogDB).filter_by(action="rule_rollback").order_by(
        DecisionAuditLogDB.timestamp.desc()
    ).first()
    assert audit is not None
    
    print(f"✅ Rollback successful: test-v2 → test-v1")


def test_conflict_returns_error_no_mutation(db, auth_token, seed_test_data):
    """
    Verify conflicting rules are rejected without mutation.
    
    Checks:
    - Multiple candidates with same vendor pattern trigger conflict
    - 409 Conflict status code
    - No database changes
    - Error message is human-readable
    """
    # Create two candidates with same vendor pattern
    conflict_cand_1 = RuleCandidateDB(
        id="conflict-001",
        vendor_pattern="walmart*",
        suggested_account="Office Supplies",
        evidence_count=10,
        evidence_precision=0.9,
        evidence_std_dev=0.05,
        status="pending"
    )
    conflict_cand_2 = RuleCandidateDB(
        id="conflict-002",
        vendor_pattern="walmart*",  # Same pattern!
        suggested_account="Groceries",  # Different account
        evidence_count=8,
        evidence_precision=0.85,
        evidence_std_dev=0.07,
        status="pending"
    )
    
    db.add(conflict_cand_1)
    db.add(conflict_cand_2)
    db.commit()
    
    version_count_before = db.query(RuleVersionDB).count()
    
    # Try dry-run with conflicting candidates
    response = client.post(
        "/api/rules/dryrun",
        json={
            "candidate_ids": ["conflict-001", "conflict-002"]
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 409  # Conflict
    data = response.json()
    
    assert "detail" in data
    assert "conflict" in data["detail"].lower()
    assert "vendor pattern" in data["detail"].lower()
    
    # Verify NO MUTATION
    version_count_after = db.query(RuleVersionDB).count()
    assert version_count_before == version_count_after
    
    # Candidates still pending
    cand1_after = db.query(RuleCandidateDB).filter_by(id="conflict-001").first()
    cand2_after = db.query(RuleCandidateDB).filter_by(id="conflict-002").first()
    
    assert cand1_after.status == "pending"
    assert cand2_after.status == "pending"
    
    print(f"✅ Conflict detected and rejected without mutation")
    print(f"   Error: {data['detail']}")


def test_idempotent_accept(db, auth_token, seed_test_data):
    """Verify accepting already-accepted candidate returns no_change=true."""
    # Accept a candidate
    response1 = client.post(
        "/api/rules/candidates/test-cand-001/accept",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response1.status_code == 200
    
    # Accept again (idempotent)
    response2 = client.post(
        "/api/rules/candidates/test-cand-001/accept",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response2.status_code == 200
    data = response2.json()
    
    assert data["no_change"] == True
    print(f"✅ Idempotent accept verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

