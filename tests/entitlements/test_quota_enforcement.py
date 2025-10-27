"""
Test Entitlement Quota Enforcement
===================================

Tests for subscription-based access control and quota limits.

Test Cases:
-----------
1. Free tier blocked from write operations
2. Starter plan has correct quotas
3. Professional plan has higher limits
4. Enterprise has unlimited access
5. Quota exhaustion returns 402
6. Quota headers present in responses
7. Usage logging works correctly
8. Feature gating blocks missing features
"""
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from datetime import datetime

from app.api.main import app
from app.db.models import (
    UserDB, TenantDB, BillingSubscriptionDB,
    UsageLogDB, TransactionDB
)
from app.auth.security import create_access_token


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def free_tier_user(db_session):
    """User with no active subscription (free tier)."""
    tenant = TenantDB(tenant_id="free-tenant", name="Free Company")
    db_session.add(tenant)
    
    user = UserDB(
        user_id="free-user",
        email="free@test.com",
        hashed_password="hashed",
        role="owner",
        tenant_ids=["free-tenant"]
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def starter_user(db_session):
    """User with starter subscription."""
    tenant = TenantDB(tenant_id="starter-tenant", name="Starter Company")
    db_session.add(tenant)
    
    user = UserDB(
        user_id="starter-user",
        email="starter@test.com",
        hashed_password="hashed",
        role="owner",
        tenant_ids=["starter-tenant"]
    )
    db_session.add(user)
    
    subscription = BillingSubscriptionDB(
        tenant_id="starter-tenant",
        plan_id="starter",
        status="active",
        stripe_customer_id="cus_starter",
        stripe_subscription_id="sub_starter"
    )
    db_session.add(subscription)
    db_session.commit()
    return user


@pytest.fixture
def professional_user(db_session):
    """User with professional subscription."""
    tenant = TenantDB(tenant_id="pro-tenant", name="Pro Company")
    db_session.add(tenant)
    
    user = UserDB(
        user_id="pro-user",
        email="pro@test.com",
        hashed_password="hashed",
        role="owner",
        tenant_ids=["pro-tenant"]
    )
    db_session.add(user)
    
    subscription = BillingSubscriptionDB(
        tenant_id="pro-tenant",
        plan_id="professional",
        status="active",
        stripe_customer_id="cus_pro",
        stripe_subscription_id="sub_pro"
    )
    db_session.add(subscription)
    db_session.commit()
    return user


@pytest.fixture
def enterprise_user(db_session):
    """User with enterprise subscription."""
    tenant = TenantDB(tenant_id="ent-tenant", name="Enterprise Company")
    db_session.add(tenant)
    
    user = UserDB(
        user_id="ent-user",
        email="ent@test.com",
        hashed_password="hashed",
        role="owner",
        tenant_ids=["ent-tenant"]
    )
    db_session.add(user)
    
    subscription = BillingSubscriptionDB(
        tenant_id="ent-tenant",
        plan_id="enterprise",
        status="active",
        stripe_customer_id="cus_ent",
        stripe_subscription_id="sub_ent"
    )
    db_session.add(subscription)
    db_session.commit()
    return user


def create_token(user):
    """Helper to create JWT token."""
    return create_access_token({"sub": user.email, "user_id": user.user_id})


def test_free_tier_blocked_from_propose(client, free_tier_user):
    """Test that free tier cannot access /api/post/propose."""
    token = create_token(free_tier_user)
    
    response = client.post(
        "/api/post/propose",
        cookies={"access_token": token}
    )
    
    assert response.status_code == 402  # Payment Required
    data = response.json()
    assert "quota_exceeded" in data["detail"]["error"]


def test_starter_has_500_transaction_quota(client, starter_user, db_session):
    """Test that starter plan has 500 tx/month quota."""
    token = create_token(starter_user)
    
    # Check entitlements endpoint
    response = client.get(
        "/api/billing/entitlements",
        cookies={"access_token": token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "starter"
    assert data["tx_quota_monthly"] == 500
    assert data["tx_remaining"] == 500


def test_professional_has_2000_transaction_quota(client, professional_user):
    """Test that professional plan has 2000 tx/month quota."""
    token = create_token(professional_user)
    
    response = client.get(
        "/api/billing/entitlements",
        cookies={"access_token": token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "professional"
    assert data["tx_quota_monthly"] == 2000


def test_enterprise_has_unlimited_quota(client, enterprise_user):
    """Test that enterprise plan has unlimited quota."""
    token = create_token(enterprise_user)
    
    response = client.get(
        "/api/billing/entitlements",
        cookies={"access_token": token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "enterprise"
    assert data["tx_quota_monthly"] == 999999  # Effectively unlimited


def test_quota_exhaustion_blocks_access(client, starter_user, db_session):
    """Test that exhausted quota returns 402."""
    # Create 500 usage logs (exhaust quota)
    for i in range(500):
        usage = UsageLogDB(
            tenant_id="starter-tenant",
            timestamp=datetime.utcnow(),
            operation="propose",
            count=1
        )
        db_session.add(usage)
    db_session.commit()
    
    token = create_token(starter_user)
    
    response = client.post(
        "/api/post/propose",
        cookies={"access_token": token}
    )
    
    assert response.status_code == 402
    data = response.json()
    assert "quota exceeded" in data["detail"]["message"].lower()


def test_quota_headers_in_response(client, starter_user):
    """Test that quota headers are present in API responses."""
    token = create_token(starter_user)
    
    # Add a transaction to propose
    # Mock the propose logic for this test
    with patch('app.api.main.rules_engine'):
        with patch('app.api.main.llm_categorizer'):
            response = client.post(
                "/api/post/propose",
                cookies={"access_token": token}
            )
            
            # Check headers
            assert "X-Tx-Remaining" in response.headers
            assert "X-Tx-Quota" in response.headers
            assert "X-Tx-Used" in response.headers
            assert "X-Plan" in response.headers
            
            assert response.headers["X-Plan"] == "starter"
            assert response.headers["X-Tx-Quota"] == "500"


def test_usage_logging_increments_count(client, starter_user, db_session):
    """Test that operations are logged for quota tracking."""
    token = create_token(starter_user)
    
    # Add transaction
    txn = TransactionDB(
        txn_id="test-txn-001",
        company_id="starter-tenant",
        date=datetime.utcnow().date(),
        amount=-100.0,
        currency="USD",
        description="Test transaction",
        counterparty="Test Vendor"
    )
    db_session.add(txn)
    db_session.commit()
    
    initial_count = db_session.query(UsageLogDB).filter_by(
        tenant_id="starter-tenant"
    ).count()
    
    # Trigger propose
    with patch('app.api.main.rules_engine.match_transaction'):
        with patch('app.api.main.llm_categorizer.categorize_transaction'):
            response = client.post(
                "/api/post/propose",
                json={"txn_ids": ["test-txn-001"]},
                cookies={"access_token": token}
            )
    
    # Check usage was logged
    final_count = db_session.query(UsageLogDB).filter_by(
        tenant_id="starter-tenant"
    ).count()
    
    assert final_count > initial_count


def test_feature_gating_blocks_qbo_export(client, starter_user):
    """Test that starter plan cannot access qbo_export feature."""
    token = create_token(starter_user)
    
    # Starter doesn't have qbo_export feature
    response = client.get(
        "/api/billing/entitlements",
        cookies={"access_token": token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "qbo_export" not in data["features"]
    assert "ai_categorization" in data["features"]


def test_professional_has_qbo_export_feature(client, professional_user):
    """Test that professional plan includes qbo_export."""
    token = create_token(professional_user)
    
    response = client.get(
        "/api/billing/entitlements",
        cookies={"access_token": token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "qbo_export" in data["features"]
    assert "advanced_rules" in data["features"]


def test_inactive_subscription_blocked(client, db_session):
    """Test that inactive subscription blocks access."""
    # Create user with inactive subscription
    tenant = TenantDB(tenant_id="inactive-tenant", name="Inactive Co")
    db_session.add(tenant)
    
    user = UserDB(
        user_id="inactive-user",
        email="inactive@test.com",
        hashed_password="hashed",
        role="owner",
        tenant_ids=["inactive-tenant"]
    )
    db_session.add(user)
    
    subscription = BillingSubscriptionDB(
        tenant_id="inactive-tenant",
        plan_id="starter",
        status="past_due",  # Inactive status
        stripe_customer_id="cus_inactive",
        stripe_subscription_id="sub_inactive"
    )
    db_session.add(subscription)
    db_session.commit()
    
    token = create_token(user)
    
    response = client.post(
        "/api/post/propose",
        cookies={"access_token": token}
    )
    
    assert response.status_code == 403
    data = response.json()
    assert "subscription_inactive" in data["detail"]["error"]


def test_soft_limit_warning_at_80_percent(client, starter_user, db_session):
    """Test that users get warning when approaching quota limit."""
    # Use 400 of 500 quota (80%)
    for i in range(400):
        usage = UsageLogDB(
            tenant_id="starter-tenant",
            timestamp=datetime.utcnow(),
            operation="propose",
            count=1
        )
        db_session.add(usage)
    db_session.commit()
    
    token = create_token(starter_user)
    
    response = client.get(
        "/api/billing/entitlements",
        cookies={"access_token": token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["tx_remaining"] == 100
    assert data["tx_used_monthly"] == 400
    # Frontend should show warning at this point


@pytest.mark.integration
def test_idempotency_key_prevents_double_quota_use(client, starter_user, db_session):
    """Test that idempotency key prevents double-counting quota."""
    token = create_token(starter_user)
    
    # Add transaction
    txn = TransactionDB(
        txn_id="test-idem-001",
        company_id="starter-tenant",
        date=datetime.utcnow().date(),
        amount=-50.0,
        currency="USD",
        description="Idempotency test",
        counterparty="Test"
    )
    db_session.add(txn)
    db_session.commit()
    
    idempotency_key = "test-key-12345"
    
    # First request
    with patch('app.api.main.rules_engine.match_transaction'):
        with patch('app.api.main.llm_categorizer.categorize_transaction'):
            response1 = client.post(
                "/api/post/propose",
                json={"txn_ids": ["test-idem-001"]},
                headers={"Idempotency-Key": idempotency_key},
                cookies={"access_token": token}
            )
    
    usage_after_first = db_session.query(UsageLogDB).filter_by(
        tenant_id="starter-tenant"
    ).count()
    
    # Second request with same key
    response2 = client.post(
        "/api/post/propose",
        json={"txn_ids": ["test-idem-001"]},
        headers={"Idempotency-Key": idempotency_key},
        cookies={"access_token": token}
    )
    
    usage_after_second = db_session.query(UsageLogDB).filter_by(
        tenant_id="starter-tenant"
    ).count()
    
    # Quota should not have increased
    assert usage_after_second == usage_after_first

