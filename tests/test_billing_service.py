"""
Tests for billing service layer.
"""

import pytest
from datetime import datetime, timedelta
from app.services.billing import BillingService
from app.db.models import EntitlementDB, UsageMonthlyDB, UsageDailyDB


@pytest.fixture
def billing_service(test_db):
    """Create billing service instance."""
    return BillingService(test_db)


@pytest.fixture
def sample_entitlement(test_db):
    """Create sample entitlement for testing."""
    entitlement = EntitlementDB(
        tenant_id="test_tenant_123",
        plan="starter",
        active=True,
        tx_cap=300,
        bulk_approve=False,
        included_companies=1,
        subscription_status="active"
    )
    test_db.add(entitlement)
    test_db.commit()
    test_db.refresh(entitlement)
    return entitlement


def test_get_entitlement(billing_service, sample_entitlement):
    """Test getting entitlement for tenant."""
    result = billing_service.get_entitlement("test_tenant_123")
    
    assert result is not None
    assert result["active"] is True
    assert result["plan"] == "starter"
    assert result["tx_cap"] == 300
    assert result["bulk_approve"] is False


def test_get_entitlement_nonexistent(billing_service):
    """Test getting entitlement for non-existent tenant."""
    result = billing_service.get_entitlement("nonexistent")
    assert result is None


def test_create_entitlement(billing_service):
    """Test creating new entitlement."""
    entitlement = billing_service.create_or_update_entitlement(
        tenant_id="new_tenant",
        plan="pro",
        active=True,
        subscription_status="trialing",
        trial_ends_at=datetime.utcnow() + timedelta(days=14)
    )
    
    assert entitlement.tenant_id == "new_tenant"
    assert entitlement.plan == "pro"
    assert entitlement.active is True
    assert entitlement.tx_cap == 2000
    assert entitlement.bulk_approve is True


def test_update_entitlement(billing_service, sample_entitlement):
    """Test updating existing entitlement."""
    entitlement = billing_service.create_or_update_entitlement(
        tenant_id="test_tenant_123",
        plan="pro",
        active=True,
        subscription_status="active"
    )
    
    assert entitlement.plan == "pro"
    assert entitlement.tx_cap == 2000
    assert entitlement.bulk_approve is True


def test_map_entitlement_from_price(billing_service):
    """Test mapping entitlement from Stripe price metadata."""
    price_metadata = {
        "plan": "firm",
        "tx_cap": "10000",
        "bulk_approve": "true",
        "included_companies": "10"
    }
    
    entitlement = billing_service.map_entitlement_from_price(
        tenant_id="price_test_tenant",
        price_id="price_test123",
        price_metadata=price_metadata,
        subscription_status="active"
    )
    
    assert entitlement.plan == "firm"
    assert entitlement.tx_cap == 10000
    assert entitlement.bulk_approve is True
    assert entitlement.included_companies == 10
    assert entitlement.active is True


def test_get_monthly_usage_new_tenant(billing_service):
    """Test getting monthly usage for new tenant creates record."""
    usage = billing_service.get_monthly_usage("new_usage_tenant")
    
    assert usage["tx_analyzed"] == 0
    assert usage["tx_posted"] == 0
    assert "last_reset_at" in usage


def test_increment_analyzed(billing_service):
    """Test incrementing analyzed transaction count."""
    tenant_id = "increment_test_tenant"
    
    # First increment
    billing_service.increment_analyzed(tenant_id, count=5)
    usage = billing_service.get_monthly_usage(tenant_id)
    assert usage["tx_analyzed"] == 5
    
    # Second increment
    billing_service.increment_analyzed(tenant_id, count=3)
    usage = billing_service.get_monthly_usage(tenant_id)
    assert usage["tx_analyzed"] == 8


def test_increment_posted(billing_service):
    """Test incrementing posted transaction count."""
    tenant_id = "posted_test_tenant"
    
    billing_service.increment_posted(tenant_id, count=10)
    usage = billing_service.get_monthly_usage(tenant_id)
    assert usage["tx_posted"] == 10


def test_check_monthly_cap_no_entitlement(billing_service):
    """Test monthly cap check for tenant without entitlement."""
    allowed, error = billing_service.check_monthly_cap("no_entitlement_tenant")
    
    assert allowed is False
    assert error is not None
    assert error["code"] == "ENTITLEMENT_REQUIRED"


def test_check_monthly_cap_under_limit(billing_service, sample_entitlement):
    """Test monthly cap check when under limit."""
    allowed, error = billing_service.check_monthly_cap("test_tenant_123")
    
    assert allowed is True
    assert error is None


def test_check_monthly_cap_exceeded(billing_service, sample_entitlement, test_db):
    """Test monthly cap check when limit exceeded."""
    # Set usage to cap limit
    current_month = datetime.utcnow().strftime("%Y-%m")
    usage = UsageMonthlyDB(
        tenant_id="test_tenant_123",
        year_month=current_month,
        tx_analyzed=0,
        tx_posted=300  # At cap
    )
    test_db.add(usage)
    test_db.commit()
    
    allowed, error = billing_service.check_monthly_cap("test_tenant_123")
    
    assert allowed is False
    assert error is not None
    assert error["code"] == "MONTHLY_CAP_EXCEEDED"


def test_get_daily_usage(billing_service):
    """Test getting daily usage."""
    usage = billing_service.get_daily_usage("daily_test_tenant")
    
    assert usage["analyze_count"] == 0
    assert usage["explain_count"] == 0


def test_increment_daily_analyze(billing_service):
    """Test incrementing daily analyze count."""
    tenant_id = "daily_analyze_tenant"
    
    billing_service.increment_daily_analyze(tenant_id)
    billing_service.increment_daily_analyze(tenant_id)
    
    usage = billing_service.get_daily_usage(tenant_id)
    assert usage["analyze_count"] == 2


def test_check_daily_analyze_cap_under_limit(billing_service):
    """Test daily analyze cap check when under limit."""
    allowed, error = billing_service.check_daily_analyze_cap("new_daily_tenant")
    
    assert allowed is True
    assert error is None


def test_check_daily_analyze_cap_exceeded(billing_service, test_db):
    """Test daily analyze cap check when exceeded."""
    from datetime import date
    tenant_id = "daily_cap_tenant"
    today = date.today().isoformat()
    
    # Set usage to cap limit
    usage = UsageDailyDB(
        tenant_id=tenant_id,
        date=today,
        analyze_count=50,  # At cap
        explain_count=0
    )
    test_db.add(usage)
    test_db.commit()
    
    allowed, error = billing_service.check_daily_analyze_cap(tenant_id)
    
    assert allowed is False
    assert error is not None
    assert error["code"] == "FREE_CAP_EXCEEDED"


def test_check_daily_analyze_cap_with_subscription(billing_service, sample_entitlement):
    """Test daily analyze cap bypassed with active subscription."""
    # Even with high daily usage, active subscription bypasses free tier limits
    allowed, error = billing_service.check_daily_analyze_cap("test_tenant_123")
    
    assert allowed is True
    assert error is None


def test_get_billing_status_complete(billing_service, sample_entitlement, test_db):
    """Test getting complete billing status."""
    # Add some usage
    current_month = datetime.utcnow().strftime("%Y-%m")
    usage = UsageMonthlyDB(
        tenant_id="test_tenant_123",
        year_month=current_month,
        tx_analyzed=25,
        tx_posted=10
    )
    test_db.add(usage)
    test_db.commit()
    
    status = billing_service.get_billing_status("test_tenant_123")
    
    assert status["active"] is True
    assert status["plan"] == "starter"
    assert status["limits"]["tx_cap"] == 300
    assert status["usage"]["tx_analyzed"] == 25
    assert status["usage"]["tx_posted"] == 10

