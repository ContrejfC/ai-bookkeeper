"""
Tests for Onboarding Wizard (Phase 2b).

Tests:
- test_wizard_persists_settings_and_coa
- test_autopost_disabled_by_default_after_onboarding
- test_redirects_to_review_on_finish
- test_staff_cannot_run_onboarding_for_unassigned_tenant
"""
import pytest
from fastapi.testclient import TestClient
from io import BytesIO

from app.api.main import app
from app.db.session import SessionLocal
from app.db.models import TenantSettingsDB, DecisionAuditLogDB


client = TestClient(app)


@pytest.fixture(scope="module")
def db():
    """Database session."""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def owner_token(db):
    """Get owner auth token."""
    response = client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "magic_token": "dev"
    })
    assert response.status_code == 200
    return response.json()["token"]


@pytest.fixture(scope="module")
def staff_token(db):
    """Get staff auth token."""
    response = client.post("/api/auth/login", json={
        "email": "staff@acmecorp.com",
        "magic_token": "dev"
    })
    assert response.status_code == 200
    return response.json()["token"]


def test_wizard_persists_settings_and_coa(owner_token, db):
    """
    Test onboarding wizard persists tenant settings and CoA.
    
    Verifies:
    - Owner can complete onboarding
    - Tenant settings persisted to DB
    - CoA template applied (14 accounts for standard_small_business)
    - Audit entry created
    """
    response = client.post(
        "/api/onboarding/complete",
        data={
            "coa_method": "template",
            "coa_template": "standard_small_business",
            "autopost_threshold": "0.90",
            "llm_budget": "50.0"
        },
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] == True
    assert "tenant_id" in data
    assert data["summary"]["coa_method"] == "template"
    assert data["summary"]["coa_accounts"] == 14  # Standard small business has 14 accounts
    assert data["summary"]["autopost_enabled"] == False
    assert data["summary"]["autopost_threshold"] == 0.90
    assert data["summary"]["llm_budget"] == 50.0
    
    # Verify settings persisted to DB
    tenant_id = data["tenant_id"]
    settings = db.query(TenantSettingsDB).filter_by(
        tenant_id=tenant_id
    ).first()
    
    assert settings is not None
    assert settings.autopost_enabled == False
    assert settings.autopost_threshold == 0.90
    assert settings.llm_tenant_cap_usd == 50.0
    
    # Verify audit entry
    audit = db.query(DecisionAuditLogDB).filter(
        DecisionAuditLogDB.tenant_id == tenant_id,
        DecisionAuditLogDB.action == "onboarding_complete"
    ).first()
    
    assert audit is not None
    
    print("✅ Onboarding persisted settings and CoA correctly")


def test_autopost_disabled_by_default_after_onboarding(owner_token, db):
    """
    Test that autopost is ALWAYS disabled after onboarding.
    
    Verifies:
    - AUTOPOST=false regardless of threshold setting
    - Cannot be changed during onboarding
    """
    response = client.post(
        "/api/onboarding/complete",
        data={
            "coa_method": "template",
            "coa_template": "professional_services",
            "autopost_threshold": "0.95",  # High threshold, but still disabled
            "llm_budget": "100.0"
        },
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    tenant_id = data["tenant_id"]
    
    # Verify autopost is disabled
    assert data["summary"]["autopost_enabled"] == False
    
    # Verify in DB
    settings = db.query(TenantSettingsDB).filter_by(
        tenant_id=tenant_id
    ).first()
    
    assert settings.autopost_enabled == False  # Always false after onboarding
    
    print("✅ Autopost disabled by default after onboarding")


def test_redirects_to_review_on_finish(owner_token):
    """
    Test that onboarding completion returns tenant_id for redirect.
    
    Verifies:
    - Response contains tenant_id
    - Frontend can redirect to /review?tenant_id=...
    """
    response = client.post(
        "/api/onboarding/complete",
        data={
            "coa_method": "template",
            "coa_template": "gaap_accounting_firm",
            "autopost_threshold": "0.90",
            "llm_budget": "50.0"
        },
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Response includes tenant_id for redirect
    assert "tenant_id" in data
    assert data["tenant_id"].startswith("onboarded-")
    
    # Frontend redirects to /review?tenant_id={tenant_id}
    tenant_id = data["tenant_id"]
    redirect_url = f"/review?tenant_id={tenant_id}"
    
    print(f"✅ Onboarding returns tenant_id for redirect: {redirect_url}")


def test_staff_cannot_run_onboarding_for_unassigned_tenant(staff_token):
    """
    Test RBAC enforcement: staff cannot run onboarding (Owner only).
    
    Verifies:
    - Staff user gets 403 when attempting onboarding
    - RBAC enforced via require_role(Role.OWNER)
    """
    response = client.post(
        "/api/onboarding/complete",
        data={
            "coa_method": "template",
            "coa_template": "standard_small_business",
            "autopost_threshold": "0.90",
            "llm_budget": "50.0"
        },
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    
    # Should fail with 403 (RBAC)
    assert response.status_code == 403
    
    print("✅ Staff blocked from onboarding (RBAC enforced)")


def test_wizard_with_file_uploads(owner_token):
    """
    Test onboarding with file uploads (CoA CSV + transactions).
    
    Verifies:
    - Can upload CoA CSV
    - Can upload transactions file
    - Files processed correctly
    """
    # Create mock CSV files
    coa_csv = "code,name,type\n1000,Cash,Asset\n2000,AP,Liability\n4000,Revenue,Revenue"
    transactions_csv = "date,description,amount\n2024-10-01,Office Supplies,145.50\n2024-10-02,Rent,2500.00"
    
    response = client.post(
        "/api/onboarding/complete",
        data={
            "coa_method": "upload",
            "autopost_threshold": "0.90",
            "llm_budget": "50.0"
        },
        files={
            "coa_file": ("chart.csv", BytesIO(coa_csv.encode()), "text/csv"),
            "transactions_file": ("transactions.csv", BytesIO(transactions_csv.encode()), "text/csv")
        },
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] == True
    assert data["summary"]["coa_method"] == "upload"
    assert data["summary"]["coa_accounts"] == 3  # 3 accounts in CSV
    assert data["summary"]["transactions"] == 2  # 2 transactions
    
    print("✅ File uploads handled correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

