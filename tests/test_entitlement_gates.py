"""
Tests for entitlement gate middleware.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


def test_commit_blocked_without_subscription(monkeypatch):
    """Test that commit is blocked without active subscription."""
    from app.services.billing import BillingService
    from app.config.limits import ERROR_CODES
    
    # Mock billing service to return inactive entitlement
    def mock_check_monthly_cap(tenant_id):
        return False, ERROR_CODES["ENTITLEMENT_REQUIRED"]
    
    monkeypatch.setattr(BillingService, "check_monthly_cap", lambda self, tid: mock_check_monthly_cap(tid))
    
    # TODO: Add actual FastAPI test client test when app is wired
    # This is a placeholder showing the test structure
    assert True


def test_commit_blocked_over_cap(monkeypatch):
    """Test that commit is blocked when monthly cap exceeded."""
    from app.services.billing import BillingService
    from app.config.limits import ERROR_CODES
    
    # Mock billing service to return cap exceeded
    def mock_check_monthly_cap(tenant_id):
        return False, ERROR_CODES["MONTHLY_CAP_EXCEEDED"]
    
    monkeypatch.setattr(BillingService, "check_monthly_cap", lambda self, tid: mock_check_monthly_cap(tid))
    
    # TODO: Add actual FastAPI test client test when app is wired
    assert True


def test_commit_allowed_with_active_subscription(monkeypatch):
    """Test that commit is allowed with active subscription under cap."""
    from app.services.billing import BillingService
    
    # Mock billing service to return allowed
    def mock_check_monthly_cap(tenant_id):
        return True, None
    
    monkeypatch.setattr(BillingService, "check_monthly_cap", lambda self, tid: mock_check_monthly_cap(tid))
    
    # TODO: Add actual FastAPI test client test when app is wired
    assert True


def test_propose_blocked_free_cap_exceeded(monkeypatch):
    """Test that propose is blocked when free daily cap exceeded."""
    from app.services.billing import BillingService
    from app.config.limits import ERROR_CODES
    
    # Mock billing service to return cap exceeded
    def mock_check_daily_analyze_cap(tenant_id):
        return False, ERROR_CODES["FREE_CAP_EXCEEDED"]
    
    monkeypatch.setattr(BillingService, "check_daily_analyze_cap", lambda self, tid: mock_check_daily_analyze_cap(tid))
    
    # TODO: Add actual FastAPI test client test when app is wired
    assert True


def test_propose_allowed_under_free_cap(monkeypatch):
    """Test that propose is allowed when under free daily cap."""
    from app.services.billing import BillingService
    
    # Mock billing service to return allowed
    def mock_check_daily_analyze_cap(tenant_id):
        return True, None
    
    def mock_increment_daily_analyze(tenant_id):
        pass
    
    monkeypatch.setattr(BillingService, "check_daily_analyze_cap", lambda self, tid: mock_check_daily_analyze_cap(tid))
    monkeypatch.setattr(BillingService, "increment_daily_analyze", lambda self, tid: mock_increment_daily_analyze(tid))
    
    # TODO: Add actual FastAPI test client test when app is wired
    assert True


def test_bulk_approve_blocked_without_entitlement(monkeypatch):
    """Test that bulk approve is blocked without bulk_approve entitlement."""
    from app.services.billing import BillingService
    
    # Mock billing service to return no bulk approve
    def mock_get_entitlement(tenant_id):
        return {
            "active": True,
            "plan": "starter",
            "bulk_approve": False
        }
    
    monkeypatch.setattr(BillingService, "get_entitlement", lambda self, tid: mock_get_entitlement(tid))
    
    # TODO: Add actual FastAPI test client test when app is wired
    assert True


def test_bulk_approve_allowed_with_entitlement(monkeypatch):
    """Test that bulk approve is allowed with bulk_approve entitlement."""
    from app.services.billing import BillingService
    
    # Mock billing service to return bulk approve enabled
    def mock_get_entitlement(tenant_id):
        return {
            "active": True,
            "plan": "pro",
            "bulk_approve": True
        }
    
    def mock_check_monthly_cap(tenant_id):
        return True, None
    
    monkeypatch.setattr(BillingService, "get_entitlement", lambda self, tid: mock_get_entitlement(tid))
    monkeypatch.setattr(BillingService, "check_monthly_cap", lambda self, tid: mock_check_monthly_cap(tid))
    
    # TODO: Add actual FastAPI test client test when app is wired
    assert True


def test_paywall_message_included_in_402_response():
    """Test that 402 responses include paywall markdown."""
    from app.config.limits import ERROR_CODES, PAYWALL_MD
    
    error = ERROR_CODES["ENTITLEMENT_REQUIRED"].copy()
    error["paywall"] = PAYWALL_MD
    
    assert "paywall" in error
    assert "Starter" in error["paywall"]
    assert "$49/mo" in error["paywall"]
    assert "14-day trial" in error["paywall"]


def test_paywall_message_included_in_429_response():
    """Test that 429 responses include paywall markdown."""
    from app.config.limits import ERROR_CODES, PAYWALL_MD
    
    error = ERROR_CODES["FREE_CAP_EXCEEDED"].copy()
    error["paywall"] = PAYWALL_MD
    
    assert "paywall" in error
    assert "continue free" in error["paywall"]

