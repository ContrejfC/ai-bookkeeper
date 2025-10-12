"""
E2E UI Tests for Rules Console (Live Backend, No Mocks).

Tests the full flow: dry-run → accept → rollback
"""
import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.db.session import SessionLocal
from app.db.models import RuleCandidateDB, RuleVersionDB


client = TestClient(app)


@pytest.fixture(scope="module")
def db():
    """Database session."""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def auth_cookie(db):
    """Get auth cookie for UI."""
    response = client.post("/api/auth/login?use_cookie=true", json={
        "email": "admin@example.com",
        "magic_token": "dev"
    })
    cookies = response.cookies
    return cookies


@pytest.fixture(scope="module")
def seed_rules_ui_data(db):
    """Seed data for rules UI testing."""
    # Create pending candidates
    candidates = [
        RuleCandidateDB(
            id="ui-cand-001",
            vendor_pattern="office depot*",
            suggested_account="Office Supplies",
            evidence_count=24,
            evidence_precision=0.96,
            evidence_std_dev=0.042,
            status="pending"
        )
    ]
    
    for cand in candidates:
        db.merge(cand)
    
    db.commit()
    yield


def test_e2e_rules_page_loads(db, auth_cookie, seed_rules_ui_data):
    """Verify /rules page loads with real data from DB."""
    response = client.get("/rules", cookies=auth_cookie)
    
    assert response.status_code == 200
    content = response.content.decode()
    
    # Check for candidate data
    assert "office depot" in content.lower()
    assert "Office Supplies" in content
    
    print("✅ /rules page loads with DB data")


def test_e2e_dryrun_button_works(db, auth_cookie, seed_rules_ui_data):
    """Verify dry-run button calls API and shows impact."""
    # Simulate dry-run API call (would be triggered by JS)
    response = client.post(
        "/api/rules/dryrun",
        json={"candidate_ids": ["ui-cand-001"]},
        cookies=auth_cookie
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "before" in data
    assert "after" in data
    assert "deltas" in data
    
    print("✅ Dry-run API works from UI")
    print(f"   Delta: {data['deltas']}")


def test_e2e_accept_creates_version(db, auth_cookie, seed_rules_ui_data):
    """Verify accept button promotes candidate and creates version."""
    version_count_before = db.query(RuleVersionDB).count()
    
    response = client.post(
        "/api/rules/candidates/ui-cand-001/accept",
        cookies=auth_cookie
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    
    # Verify version created
    version_count_after = db.query(RuleVersionDB).count()
    assert version_count_after > version_count_before
    
    # Verify candidate status
    candidate = db.query(RuleCandidateDB).filter_by(id="ui-cand-001").first()
    assert candidate.status == "accepted"
    
    print("✅ Accept button works end-to-end")
    print(f"   New version: {data['version_id']}")


def test_e2e_rollback_restores_version(db, auth_cookie, seed_rules_ui_data):
    """Verify rollback button restores previous version."""
    # Create test versions
    v1 = RuleVersionDB(
        version_id="ui-test-v1",
        rules_yaml="# UI Test V1",
        created_by="user-admin-001",
        is_active=False
    )
    v2 = RuleVersionDB(
        version_id="ui-test-v2",
        rules_yaml="# UI Test V2",
        created_by="user-admin-001",
        is_active=True
    )
    
    db.add(v1)
    db.add(v2)
    db.commit()
    
    # Rollback via API
    response = client.post(
        "/api/rules/rollback",
        json={"to_version": "ui-test-v1"},
        cookies=auth_cookie
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    
    # Verify version changed
    v1_after = db.query(RuleVersionDB).filter_by(version_id="ui-test-v1").first()
    assert v1_after.is_active == True
    
    print("✅ Rollback works end-to-end")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

