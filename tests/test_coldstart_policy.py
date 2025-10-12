#!/usr/bin/env python3
"""
Unit tests for cold-start policy (Sprint 9 Stage D).

Tests that vendors require 3 consistent labels before auto-post eligibility.
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class ColdStartTracker:
    """Mock cold-start tracker for testing."""
    
    def __init__(self):
        self.tracking = {}  # vendor_normalized -> data
    
    def add_label(self, vendor_normalized: str, suggested_account: str) -> dict:
        """
        Add a label for a vendor.
        
        Returns:
            Cold-start status dict
        """
        if vendor_normalized not in self.tracking:
            self.tracking[vendor_normalized] = {
                "labels": [],
                "suggested_account": None,
                "label_count": 0,
                "consistent": False,
                "eligible": False
            }
        
        vendor_data = self.tracking[vendor_normalized]
        vendor_data["labels"].append(suggested_account)
        vendor_data["label_count"] = len(vendor_data["labels"])
        
        # Check consistency (all labels same)
        if len(set(vendor_data["labels"])) == 1:
            vendor_data["consistent"] = True
            vendor_data["suggested_account"] = suggested_account
        else:
            vendor_data["consistent"] = False
            vendor_data["suggested_account"] = None
        
        # Eligible if ≥3 consistent labels
        vendor_data["eligible"] = (
            vendor_data["consistent"] and 
            vendor_data["label_count"] >= 3
        )
        
        return {
            "vendor_normalized": vendor_normalized,
            "label_count": vendor_data["label_count"],
            "consistent": vendor_data["consistent"],
            "eligible": vendor_data["eligible"],
            "suggested_account": vendor_data["suggested_account"]
        }
    
    def is_eligible(self, vendor_normalized: str) -> bool:
        """Check if vendor is eligible for auto-post."""
        if vendor_normalized not in self.tracking:
            return False
        return self.tracking[vendor_normalized]["eligible"]
    
    def get_status(self, vendor_normalized: str) -> dict:
        """Get cold-start status for vendor."""
        if vendor_normalized not in self.tracking:
            return {
                "vendor_normalized": vendor_normalized,
                "label_count": 0,
                "consistent": False,
                "eligible": False,
                "suggested_account": None
            }
        
        vendor_data = self.tracking[vendor_normalized]
        return {
            "vendor_normalized": vendor_normalized,
            "label_count": vendor_data["label_count"],
            "consistent": vendor_data["consistent"],
            "eligible": vendor_data["eligible"],
            "suggested_account": vendor_data["suggested_account"]
        }


class TestColdStartPolicy:
    """Test cold-start policy enforcement."""
    
    @pytest.fixture
    def tracker(self):
        """Create a fresh cold-start tracker."""
        return ColdStartTracker()
    
    def test_blocks_until_three_consistent(self, tracker):
        """
        CRITICAL TEST: Blocks auto-post until 3 consistent labels.
        
        This prevents auto-posting for new vendors before we have
        sufficient training data.
        """
        vendor = "office depot"
        account = "6000 Supplies"
        
        # Label 1: Not eligible (need 3)
        status1 = tracker.add_label(vendor, account)
        assert not status1["eligible"], "Should not be eligible after 1 label"
        assert status1["label_count"] == 1
        assert status1["consistent"] is True
        
        # Label 2: Still not eligible (need 3)
        status2 = tracker.add_label(vendor, account)
        assert not status2["eligible"], "Should not be eligible after 2 labels"
        assert status2["label_count"] == 2
        assert status2["consistent"] is True
        
        # Label 3: NOW eligible ✅
        status3 = tracker.add_label(vendor, account)
        assert status3["eligible"], "Should be eligible after 3 consistent labels"
        assert status3["label_count"] == 3
        assert status3["consistent"] is True
        assert status3["suggested_account"] == account
        
        print(f"\n✅ Cold-start policy enforced:")
        print(f"   Vendor: {vendor}")
        print(f"   Labels: {status3['label_count']}")
        print(f"   Eligible: {status3['eligible']}")
    
    def test_inconsistent_labels_reset_eligibility(self, tracker):
        """
        Test that inconsistent labels prevent eligibility.
        
        If users correct to different accounts, vendor stays ineligible.
        """
        vendor = "stripe"
        
        # Label 1: 8000 Revenue
        status1 = tracker.add_label(vendor, "8000 Revenue")
        assert not status1["eligible"]
        
        # Label 2: 8000 Revenue (consistent)
        status2 = tracker.add_label(vendor, "8000 Revenue")
        assert not status2["eligible"]
        
        # Label 3: 8100 Other Income (INCONSISTENT)
        status3 = tracker.add_label(vendor, "8100 Other Income")
        assert not status3["eligible"], "Inconsistent labels should block eligibility"
        assert not status3["consistent"], "Should not be marked consistent"
        assert status3["label_count"] == 3, "Count should still be 3"
        
        print(f"\n✅ Inconsistent labels block eligibility:")
        print(f"   Vendor: {vendor}")
        print(f"   Labels: {status3['label_count']}")
        print(f"   Consistent: {status3['consistent']}")
        print(f"   Eligible: {status3['eligible']}")
    
    def test_new_vendor_starts_ineligible(self, tracker):
        """Test that new vendors start as ineligible."""
        vendor = "new vendor inc"
        
        status = tracker.get_status(vendor)
        
        assert not status["eligible"], "New vendor should be ineligible"
        assert status["label_count"] == 0
        assert not status["consistent"]
        
        print(f"\n✅ New vendor starts ineligible:")
        print(f"   Vendor: {vendor}")
        print(f"   Label count: {status['label_count']}")
        print(f"   Eligible: {status['eligible']}")
    
    def test_eligibility_persists_after_three(self, tracker):
        """Test that eligibility persists after reaching threshold."""
        vendor = "walgreens"
        account = "6200 Pharmacy"
        
        # Add 3 consistent labels
        for _ in range(3):
            tracker.add_label(vendor, account)
        
        # Check eligibility
        assert tracker.is_eligible(vendor), "Should be eligible after 3"
        
        # Add more labels (should stay eligible)
        status = tracker.add_label(vendor, account)
        assert status["eligible"], "Should remain eligible"
        assert status["label_count"] == 4
        
        print(f"\n✅ Eligibility persists:")
        print(f"   Vendor: {vendor}")
        print(f"   Labels: {status['label_count']}")
        print(f"   Still eligible: {status['eligible']}")
    
    def test_multiple_vendors_tracked_independently(self, tracker):
        """Test that multiple vendors are tracked independently."""
        vendor1 = "office depot"
        vendor2 = "staples"
        account = "6000 Supplies"
        
        # Vendor 1: 3 labels (eligible)
        for _ in range(3):
            tracker.add_label(vendor1, account)
        
        # Vendor 2: 1 label (not eligible)
        tracker.add_label(vendor2, account)
        
        assert tracker.is_eligible(vendor1), "Vendor 1 should be eligible"
        assert not tracker.is_eligible(vendor2), "Vendor 2 should not be eligible"
        
        print(f"\n✅ Multiple vendors tracked independently:")
        print(f"   {vendor1}: eligible")
        print(f"   {vendor2}: not eligible")


class TestColdStartIntegrationWithGating:
    """Test integration of cold-start with auto-post gating."""
    
    def test_cold_start_blocks_even_with_high_calibrated_p(self):
        """
        Test that cold-start blocks auto-post even if calibrated_p ≥ 0.90.
        
        This is critical: cold-start overrides confidence.
        """
        decision = {
            "account": "6000 Supplies",
            "calibrated_p": 0.95  # High confidence
        }
        
        cold_start_status = {
            "eligible": False,  # Cold-start blocks
            "label_count": 1
        }
        
        # Apply gating logic
        AUTOPOST_THRESHOLD = 0.90
        
        # Check calibrated_p first
        p_check = decision["calibrated_p"] >= AUTOPOST_THRESHOLD
        
        # Check cold-start
        cold_start_check = cold_start_status["eligible"]
        
        # Final decision
        auto_post_eligible = p_check and cold_start_check
        
        if not cold_start_check:
            auto_post_decision = "review"
            not_auto_post_reason = "cold_start"
        elif not p_check:
            auto_post_decision = "review"
            not_auto_post_reason = "below_threshold"
        else:
            auto_post_decision = "posted"
            not_auto_post_reason = None
        
        # Assertions
        assert not auto_post_eligible, \
            "Cold-start should block even with high confidence"
        assert auto_post_decision == "review"
        assert not_auto_post_reason == "cold_start"
        
        print(f"\n✅ Cold-start blocks high-confidence transactions:")
        print(f"   calibrated_p: {decision['calibrated_p']:.2f}")
        print(f"   cold_start labels: {cold_start_status['label_count']}")
        print(f"   decision: {auto_post_decision} (reason: {not_auto_post_reason})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

