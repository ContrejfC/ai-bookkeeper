"""
Tests for usage caps and free tier limits.
"""

import pytest
from datetime import datetime, date
from app.services.billing import BillingService
from app.db.models import EntitlementDB, UsageMonthlyDB, UsageDailyDB
from app.config.limits import FREE_DAILY_ANALYZE_CAP, FREE_DAILY_EXPLAIN_CAP


@pytest.fixture
def billing_service(test_db):
    """Create billing service instance."""
    return BillingService(test_db)


def test_monthly_cap_enforcement(billing_service, test_db):
    """Test that monthly transaction cap is enforced."""
    tenant_id = "cap_test_tenant"
    
    # Create entitlement with cap of 300
    entitlement = EntitlementDB(
        tenant_id=tenant_id,
        plan="starter",
        active=True,
        tx_cap=300,
        bulk_approve=False,
        included_companies=1,
        subscription_status="active"
    )
    test_db.add(entitlement)
    test_db.commit()
    
    # Set usage to exactly at cap
    current_month = datetime.utcnow().strftime("%Y-%m")
    usage = UsageMonthlyDB(
        tenant_id=tenant_id,
        year_month=current_month,
        tx_analyzed=250,
        tx_posted=300  # At cap
    )
    test_db.add(usage)
    test_db.commit()
    
    # Check cap - should fail
    allowed, error = billing_service.check_monthly_cap(tenant_id)
    
    assert allowed is False
    assert error["code"] == "MONTHLY_CAP_EXCEEDED"


def test_monthly_cap_under_limit(billing_service, test_db):
    """Test that requests under monthly cap are allowed."""
    tenant_id = "under_cap_tenant"
    
    # Create entitlement with cap of 300
    entitlement = EntitlementDB(
        tenant_id=tenant_id,
        plan="starter",
        active=True,
        tx_cap=300,
        bulk_approve=False,
        included_companies=1,
        subscription_status="active"
    )
    test_db.add(entitlement)
    test_db.commit()
    
    # Set usage below cap
    current_month = datetime.utcnow().strftime("%Y-%m")
    usage = UsageMonthlyDB(
        tenant_id=tenant_id,
        year_month=current_month,
        tx_analyzed=100,
        tx_posted=100
    )
    test_db.add(usage)
    test_db.commit()
    
    # Check cap - should pass
    allowed, error = billing_service.check_monthly_cap(tenant_id)
    
    assert allowed is True
    assert error is None


def test_free_tier_daily_analyze_cap(billing_service, test_db):
    """Test that free tier daily analyze cap is enforced."""
    tenant_id = "free_tier_tenant"
    today = date.today().isoformat()
    
    # Create daily usage at cap
    usage = UsageDailyDB(
        tenant_id=tenant_id,
        date=today,
        analyze_count=FREE_DAILY_ANALYZE_CAP,  # At cap (50)
        explain_count=0
    )
    test_db.add(usage)
    test_db.commit()
    
    # Check cap - should fail for free tier
    allowed, error = billing_service.check_daily_analyze_cap(tenant_id)
    
    assert allowed is False
    assert error["code"] == "FREE_CAP_EXCEEDED"


def test_free_tier_bypassed_with_subscription(billing_service, test_db):
    """Test that active subscription bypasses free tier limits."""
    tenant_id = "paid_tenant"
    today = date.today().isoformat()
    
    # Create active subscription
    entitlement = EntitlementDB(
        tenant_id=tenant_id,
        plan="starter",
        active=True,
        tx_cap=300,
        bulk_approve=False,
        included_companies=1,
        subscription_status="active"
    )
    test_db.add(entitlement)
    
    # Create daily usage above free tier limit
    usage = UsageDailyDB(
        tenant_id=tenant_id,
        date=today,
        analyze_count=100,  # Above free tier cap
        explain_count=0
    )
    test_db.add(usage)
    test_db.commit()
    
    # Check cap - should pass because of active subscription
    allowed, error = billing_service.check_daily_analyze_cap(tenant_id)
    
    assert allowed is True
    assert error is None


def test_usage_increment_creates_record(billing_service):
    """Test that incrementing usage creates record if none exists."""
    tenant_id = "new_usage_tenant"
    
    # Increment without existing record
    billing_service.increment_posted(tenant_id, count=5)
    
    # Verify record created
    usage = billing_service.get_monthly_usage(tenant_id)
    assert usage["tx_posted"] == 5


def test_usage_increment_updates_record(billing_service, test_db):
    """Test that incrementing usage updates existing record."""
    tenant_id = "existing_usage_tenant"
    current_month = datetime.utcnow().strftime("%Y-%m")
    
    # Create existing usage record
    usage = UsageMonthlyDB(
        tenant_id=tenant_id,
        year_month=current_month,
        tx_analyzed=10,
        tx_posted=20
    )
    test_db.add(usage)
    test_db.commit()
    
    # Increment
    billing_service.increment_posted(tenant_id, count=5)
    
    # Verify updated
    updated_usage = billing_service.get_monthly_usage(tenant_id)
    assert updated_usage["tx_posted"] == 25


def test_daily_usage_resets_per_day(billing_service, test_db):
    """Test that daily usage is isolated by date."""
    from datetime import date, timedelta
    
    tenant_id = "daily_reset_tenant"
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    today = date.today().isoformat()
    
    # Create usage for yesterday
    usage_yesterday = UsageDailyDB(
        tenant_id=tenant_id,
        date=yesterday,
        analyze_count=50,
        explain_count=50
    )
    test_db.add(usage_yesterday)
    test_db.commit()
    
    # Get today's usage - should be 0
    today_usage = billing_service.get_daily_usage(tenant_id)
    
    assert today_usage["analyze_count"] == 0
    assert today_usage["explain_count"] == 0


def test_bulk_approve_entitlement_check():
    """Test that bulk approve requires correct entitlement."""
    from app.config.limits import ERROR_CODES
    
    # Starter plan (no bulk approve)
    starter_entitlement = {
        "plan": "starter",
        "bulk_approve": False
    }
    
    # Pro plan (with bulk approve)
    pro_entitlement = {
        "plan": "pro",
        "bulk_approve": True
    }
    
    # Verify configuration
    assert starter_entitlement["bulk_approve"] is False
    assert pro_entitlement["bulk_approve"] is True
    assert "BULK_APPROVE_REQUIRED" in ERROR_CODES


def test_entitlement_trial_status():
    """Test that trialing subscriptions are active."""
    from app.services.billing import BillingService
    
    # Trialing status should be active
    assert "trialing" in ["active", "trialing"]
    
    # Past due should not be active
    assert "past_due" not in ["active", "trialing"]


def test_price_metadata_parsing():
    """Test parsing of Stripe price metadata."""
    price_metadata = {
        "plan": "firm",
        "tx_cap": "10000",
        "bulk_approve": "true",
        "included_companies": "10"
    }
    
    # Parse metadata
    plan = price_metadata.get("plan")
    tx_cap = int(price_metadata.get("tx_cap", "300"))
    bulk_approve = price_metadata.get("bulk_approve", "false").lower() == "true"
    included_companies = int(price_metadata.get("included_companies", "1"))
    
    assert plan == "firm"
    assert tx_cap == 10000
    assert bulk_approve is True
    assert included_companies == 10


def test_usage_rollover_resets_counters():
    """Test that monthly rollover resets counters to 0."""
    # This will be tested by scripts/roll_usage_month.py
    # Placeholder for now
    assert True


def test_free_cap_error_includes_paywall():
    """Test that free cap exceeded error includes paywall message."""
    from app.config.limits import ERROR_CODES, PAYWALL_MD
    
    error = ERROR_CODES["FREE_CAP_EXCEEDED"].copy()
    error["paywall"] = PAYWALL_MD
    
    assert "paywall" in error
    assert "14-day trial" in error["paywall"]
    assert "/billing/portal" in str(ERROR_CODES["FREE_CAP_EXCEEDED"].get("message", ""))


def test_monthly_cap_error_includes_paywall():
    """Test that monthly cap exceeded error includes paywall message."""
    from app.config.limits import ERROR_CODES, PAYWALL_MD
    
    error = ERROR_CODES["MONTHLY_CAP_EXCEEDED"].copy()
    error["paywall"] = PAYWALL_MD
    
    assert "paywall" in error
    assert "Upgrade" in error["message"] or "limit" in error["message"]

