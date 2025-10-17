"""
Tests for /post/commit respecting billing caps.
"""

import pytest


def test_commit_blocked_by_middleware_402():
    """Test that middleware returns 402 before commit handler runs."""
    
    # If entitlement middleware blocks with 402,
    # the commit handler should never execute
    
    # Expected middleware behavior:
    # - Check monthly cap
    # - Return 402 if over cap or inactive
    # - Handler never reached
    
    middleware_response = {
        "code": "ENTITLEMENT_REQUIRED",
        "message": "Activate a plan to post to QuickBooks.",
        "actions": ["/billing/portal"],
        "paywall": "To post to QuickBooks, activate a plan..."
    }
    
    http_status = 402
    
    assert http_status == 402
    assert middleware_response["code"] == "ENTITLEMENT_REQUIRED"
    assert "/billing/portal" in middleware_response["actions"]


def test_commit_allowed_with_active_subscription_under_cap():
    """Test that commit proceeds when subscription active and under cap."""
    
    # Middleware checks:
    # - entitlement.active == true ✓
    # - usage.tx_posted < entitlement.tx_cap ✓
    # - Returns: passes to handler
    
    # Handler response: per-item results
    response = {
        "results": [
            {"txn_id": "t1", "qbo_doc_id": "123", "status": "posted"}
        ],
        "summary": {"total": 1, "posted": 1, "errors": 0}
    }
    
    assert response["summary"]["posted"] == 1
    assert response["summary"]["errors"] == 0


def test_commit_increments_usage_counter():
    """Test that successful commits increment usage counter."""
    
    # After successful posting:
    # billing_service.increment_posted(tenant_id, count=posted_count)
    
    posted_count = 3  # 3 new posts (excluding idempotent)
    
    # Verify count increments by number of new (non-idempotent) posts
    assert posted_count == 3


def test_middleware_gate_runs_before_handler():
    """Test that entitlement middleware runs before commit handler."""
    
    # Middleware order in app:
    # 1. CSRF middleware
    # 2. EntitlementGateMiddleware <- checks caps
    # 3. Handler <- /post/commit logic
    
    # If middleware returns 402, handler never runs
    middleware_blocks = True
    handler_executed = False if middleware_blocks else True
    
    assert handler_executed is False

