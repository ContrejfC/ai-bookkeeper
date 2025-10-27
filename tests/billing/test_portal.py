"""
Test Stripe Billing Portal Integration
========================================

Tests for creating Stripe Customer Portal sessions.

Test Cases:
-----------
1. Owner can create portal session
2. Staff cannot create portal session (403)
3. Returns valid Stripe portal URL
4. Handles missing subscription gracefully
5. Handles Stripe API errors
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from app.api.main import app
from app.db.models import BillingSubscriptionDB, UserDB, TenantDB
from app.auth.security import create_access_token


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def owner_user(db_session):
    """Create owner user with subscription."""
    # Create tenant
    tenant = TenantDB(
        tenant_id="test-tenant-001",
        name="Test Company",
        auto_post_threshold=0.85
    )
    db_session.add(tenant)
    
    # Create user
    user = UserDB(
        user_id="owner-001",
        email="owner@test.com",
        hashed_password="hashed",
        role="owner",
        tenant_ids=["test-tenant-001"]
    )
    db_session.add(user)
    
    # Create subscription
    subscription = BillingSubscriptionDB(
        tenant_id="test-tenant-001",
        plan_id="professional",
        status="active",
        stripe_customer_id="cus_test123",
        stripe_subscription_id="sub_test123"
    )
    db_session.add(subscription)
    
    db_session.commit()
    return user


@pytest.fixture
def staff_user(db_session):
    """Create staff user."""
    user = UserDB(
        user_id="staff-001",
        email="staff@test.com",
        hashed_password="hashed",
        role="staff",
        tenant_ids=["test-tenant-001"]
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def owner_token(owner_user):
    """Create JWT token for owner."""
    return create_access_token({"sub": owner_user.email, "user_id": owner_user.user_id})


@pytest.fixture
def staff_token(staff_user):
    """Create JWT token for staff."""
    return create_access_token({"sub": staff_user.email, "user_id": staff_user.user_id})


def test_owner_can_create_portal_session(client, owner_token):
    """Test that owner can create billing portal session."""
    with patch('stripe.billing_portal.Session.create') as mock_create:
        # Mock Stripe response
        mock_session = Mock()
        mock_session.url = "https://billing.stripe.com/session/test_123"
        mock_create.return_value = mock_session
        
        response = client.post(
            "/api/billing/portal",
            cookies={"access_token": owner_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert data["url"].startswith("https://billing.stripe.com")
        
        # Verify Stripe API was called
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["customer"] == "cus_test123"
        assert "return_url" in call_kwargs


def test_staff_cannot_create_portal_session(client, staff_token):
    """Test that staff users cannot access billing portal (403)."""
    response = client.post(
        "/api/billing/portal",
        cookies={"access_token": staff_token}
    )
    
    assert response.status_code == 403
    assert "owner" in response.json()["detail"].lower()


def test_portal_requires_authentication(client):
    """Test that unauthenticated requests are rejected."""
    response = client.post("/api/billing/portal")
    
    assert response.status_code == 401


def test_portal_handles_missing_subscription(client, db_session):
    """Test graceful handling when user has no subscription."""
    # Create user without subscription
    user = UserDB(
        user_id="no-sub-001",
        email="nosub@test.com",
        hashed_password="hashed",
        role="owner",
        tenant_ids=["tenant-no-sub"]
    )
    db_session.add(user)
    db_session.commit()
    
    token = create_access_token({"sub": user.email, "user_id": user.user_id})
    
    response = client.post(
        "/api/billing/portal",
        cookies={"access_token": token}
    )
    
    assert response.status_code == 404
    assert "no subscription" in response.json()["detail"].lower()


def test_portal_handles_stripe_error(client, owner_token):
    """Test handling of Stripe API errors."""
    with patch('stripe.billing_portal.Session.create') as mock_create:
        # Mock Stripe error
        import stripe
        mock_create.side_effect = stripe.error.StripeError("API Error")
        
        response = client.post(
            "/api/billing/portal",
            cookies={"access_token": owner_token}
        )
        
        assert response.status_code == 400
        assert "error" in response.json()["detail"].lower()


def test_portal_uses_correct_return_url(client, owner_token):
    """Test that portal session uses configured return URL."""
    with patch('stripe.billing_portal.Session.create') as mock_create:
        mock_session = Mock()
        mock_session.url = "https://billing.stripe.com/session/test"
        mock_create.return_value = mock_session
        
        with patch.dict('os.environ', {'STRIPE_BILLING_PORTAL_RETURN_URL': 'https://custom.com/return'}):
            response = client.post(
                "/api/billing/portal",
                cookies={"access_token": owner_token}
            )
            
            assert response.status_code == 200
            
            # Verify custom return URL was used
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["return_url"] == "https://custom.com/return"


@pytest.mark.integration
def test_portal_logs_action(client, owner_token, caplog):
    """Test that portal creation is logged."""
    with patch('stripe.billing_portal.Session.create') as mock_create:
        mock_session = Mock()
        mock_session.url = "https://billing.stripe.com/session/test"
        mock_create.return_value = mock_session
        
        response = client.post(
            "/api/billing/portal",
            cookies={"access_token": owner_token}
        )
        
        assert response.status_code == 200
        
        # Check logs
        assert "Billing portal session created" in caplog.text
        assert "test-tenant-001" in caplog.text

