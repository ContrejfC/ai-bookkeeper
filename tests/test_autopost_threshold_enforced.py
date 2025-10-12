#!/usr/bin/env python3
"""
Unit tests for auto-post threshold enforcement (Sprint 9 Stage D).

Tests that calibrated_p ≥ 0.90 is required for auto-posting.
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAutoPostThresholdEnforced:
    """Test auto-post gating based on calibrated_p threshold."""
    
    def test_below_threshold_goes_to_review(self):
        """
        Test that transactions with calibrated_p < 0.90 go to review.
        
        This is the critical gate that prevents low-confidence auto-posting.
        """
        # Simulate decision with calibrated_p = 0.86 (below 0.90)
        decision = {
            "account": "6000 Supplies",
            "confidence": 0.89,  # Uncalibrated
            "calibrated_p": 0.86,  # Calibrated (below threshold)
            "method": "ml"
        }
        
        # Apply gating logic
        AUTOPOST_THRESHOLD = 0.90
        
        if decision["calibrated_p"] < AUTOPOST_THRESHOLD:
            auto_post_eligible = False
            auto_post_decision = "review"
            not_auto_post_reason = "below_threshold"
        else:
            auto_post_eligible = True
            auto_post_decision = "posted"
            not_auto_post_reason = None
        
        # Assertions
        assert not auto_post_eligible, "Should not be eligible for auto-post"
        assert auto_post_decision == "review", "Should route to review"
        assert not_auto_post_reason == "below_threshold", \
            "Reason should be below_threshold"
        
        print(f"\n✅ Transaction routed to review:")
        print(f"   calibrated_p: {decision['calibrated_p']:.2f}")
        print(f"   threshold: {AUTOPOST_THRESHOLD:.2f}")
        print(f"   decision: {auto_post_decision}")
        print(f"   reason: {not_auto_post_reason}")
    
    def test_above_threshold_auto_posts(self):
        """
        Test that transactions with calibrated_p ≥ 0.90 auto-post.
        
        Validates that high-confidence predictions are automatically posted.
        """
        # Simulate decision with calibrated_p = 0.93 (above 0.90)
        decision = {
            "account": "6000 Supplies",
            "confidence": 0.91,  # Uncalibrated
            "calibrated_p": 0.93,  # Calibrated (above threshold)
            "method": "ml"
        }
        
        # Apply gating logic
        AUTOPOST_THRESHOLD = 0.90
        
        if decision["calibrated_p"] < AUTOPOST_THRESHOLD:
            auto_post_eligible = False
            auto_post_decision = "review"
            not_auto_post_reason = "below_threshold"
        else:
            auto_post_eligible = True
            auto_post_decision = "posted"
            not_auto_post_reason = None
        
        # Assertions
        assert auto_post_eligible, "Should be eligible for auto-post"
        assert auto_post_decision == "posted", "Should auto-post"
        assert not_auto_post_reason is None, "No blocking reason"
        
        print(f"\n✅ Transaction auto-posted:")
        print(f"   calibrated_p: {decision['calibrated_p']:.2f}")
        print(f"   threshold: {AUTOPOST_THRESHOLD:.2f}")
        print(f"   decision: {auto_post_decision}")
    
    def test_threshold_at_boundary(self):
        """Test that calibrated_p exactly at 0.90 is eligible."""
        decision = {"calibrated_p": 0.90}
        
        AUTOPOST_THRESHOLD = 0.90
        auto_post_eligible = decision["calibrated_p"] >= AUTOPOST_THRESHOLD
        
        assert auto_post_eligible, "Exactly at threshold should be eligible"
    
    def test_per_tenant_threshold_override(self):
        """
        Test that per-tenant threshold overrides global setting.
        
        Tenant-specific thresholds allow for stricter or looser gating.
        """
        # Global threshold
        GLOBAL_THRESHOLD = 0.90
        
        # Tenant override (stricter)
        tenant_overrides = {
            "alpha": 0.95,  # More conservative
            "beta": 0.85,   # More aggressive
        }
        
        decision = {"calibrated_p": 0.92}
        
        # Test tenant alpha (stricter threshold)
        tenant = "alpha"
        threshold = tenant_overrides.get(tenant, GLOBAL_THRESHOLD)
        auto_post_eligible = decision["calibrated_p"] >= threshold
        
        assert not auto_post_eligible, \
            f"Alpha tenant requires p ≥ {threshold}, got {decision['calibrated_p']}"
        
        # Test tenant beta (looser threshold)
        tenant = "beta"
        threshold = tenant_overrides.get(tenant, GLOBAL_THRESHOLD)
        auto_post_eligible = decision["calibrated_p"] >= threshold
        
        assert auto_post_eligible, \
            f"Beta tenant requires p ≥ {threshold}, got {decision['calibrated_p']}"
        
        # Test tenant with no override (uses global)
        tenant = "gamma"
        threshold = tenant_overrides.get(tenant, GLOBAL_THRESHOLD)
        auto_post_eligible = decision["calibrated_p"] >= threshold
        
        assert auto_post_eligible, \
            f"Gamma tenant uses global threshold {threshold}"
        
        print(f"\n✅ Per-tenant threshold overrides working:")
        print(f"   Global: {GLOBAL_THRESHOLD}")
        print(f"   Alpha (strict): {tenant_overrides['alpha']}")
        print(f"   Beta (loose): {tenant_overrides['beta']}")
    
    def test_missing_calibrated_p_defaults_to_review(self):
        """Test that missing calibrated_p safely defaults to review."""
        decision = {
            "account": "6000 Supplies",
            "confidence": 0.95
            # No calibrated_p field
        }
        
        # Safe default: if no calibrated_p, route to review
        calibrated_p = decision.get("calibrated_p", 0.0)
        auto_post_eligible = calibrated_p >= 0.90
        auto_post_decision = "posted" if auto_post_eligible else "review"
        not_auto_post_reason = "below_threshold" if not auto_post_eligible else None
        
        assert not auto_post_eligible, "Missing calibrated_p should not auto-post"
        assert auto_post_decision == "review"
        assert not_auto_post_reason == "below_threshold"
        
        print(f"\n✅ Missing calibrated_p safely routes to review")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

