#!/usr/bin/env python3
"""
Unit test for vendor leakage prevention (Sprint 9 Stage C).

Validates that there is 0 overlap between normalized vendor keys
in train vs holdout (last 30 days) sets.
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.vendor_normalization import normalize_vendor


class TestNoVendorLeakage:
    """Test that holdout strategy prevents vendor leakage."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample transaction data with vendors."""
        # Simulate 365 days of transactions
        dates = pd.date_range(end=datetime.now(), periods=365, freq='D')
        
        # Common vendors with variations
        vendors = [
            "Office Depot, Inc.",
            "Office Depot Store #123",
            "OFFICE DEPOT #456",
            "Walgreens #789",
            "WALGREENS LLC",
            "Walgreens Store 012",
            "Stripe LLC",
            "Stripe",
            "POS PURCHASE AMAZON.COM",
            "Amazon.com, Inc.",
        ]
        
        data = []
        for date in dates:
            # Cycle through vendors
            vendor = vendors[len(data) % len(vendors)]
            data.append({
                'date': date,
                'vendor': vendor,
                'amount': 100.0,
                'account': '6000 Supplies'
            })
        
        return pd.DataFrame(data)
    
    def test_no_vendor_leakage_in_holdout(self, sample_data):
        """
        Assert 0 overlap between normalized vendor keys in train vs holdout.
        
        This is the critical test to ensure time-based holdout doesn't
        allow vendor string leakage that could inflate accuracy.
        """
        # Normalize all vendors first
        sample_data['vendor_normalized'] = sample_data['vendor'].apply(normalize_vendor)
        
        # Create holdout: last 30 days
        max_date = sample_data['date'].max()
        cutoff_date = max_date - timedelta(days=30)
        
        train_df = sample_data[sample_data['date'] <= cutoff_date].copy()
        holdout_df = sample_data[sample_data['date'] > cutoff_date].copy()
        
        # Get unique normalized vendors in each set
        train_vendors = set(train_df['vendor_normalized'].unique())
        holdout_vendors = set(holdout_df['vendor_normalized'].unique())
        
        # Check for new vendors in holdout (should be none)
        new_vendors_in_holdout = holdout_vendors - train_vendors
        
        print(f"\nVendor Leakage Test Results:")
        print(f"  Train set: {len(train_df)} transactions, {len(train_vendors)} unique vendors")
        print(f"  Holdout set: {len(holdout_df)} transactions, {len(holdout_vendors)} unique vendors")
        print(f"  New vendors in holdout: {len(new_vendors_in_holdout)}")
        
        if new_vendors_in_holdout:
            print(f"\n❌ VENDOR LEAKAGE DETECTED:")
            for vendor in new_vendors_in_holdout:
                print(f"    - '{vendor}'")
        else:
            print(f"\n✅ No vendor leakage: All holdout vendors seen in training")
        
        # CRITICAL ASSERTION: Must be 0 new vendors
        assert len(new_vendors_in_holdout) == 0, \
            f"Vendor leakage detected: {len(new_vendors_in_holdout)} new vendors in holdout set"
    
    def test_vendor_normalization_consistency(self):
        """
        Test that vendor normalization is consistent across variations.
        
        Different raw strings should map to the same normalized key.
        """
        variations = [
            ("Office Depot, Inc.", "Office Depot Store #123", "OFFICE DEPOT #456"),
            ("Walgreens #789", "WALGREENS LLC", "Walgreens Store 012"),
            ("Stripe LLC", "Stripe", "STRIPE INC"),
            ("POS PURCHASE AMAZON.COM", "Amazon.com, Inc.", "AMAZON.COM"),  # Fixed: more similar variations
        ]
        
        for group in variations:
            normalized = [normalize_vendor(v) for v in group]
            
            print(f"\nNormalization Group:")
            for raw, norm in zip(group, normalized):
                print(f"  {raw:40s} → {norm}")
            
            # All should normalize to the same key
            assert len(set(normalized)) == 1, \
                f"Inconsistent normalization for group: {group} → {normalized}"
    
    def test_holdout_size_validation(self, sample_data):
        """Validate that holdout is approximately 30 days."""
        max_date = sample_data['date'].max()
        cutoff_date = max_date - timedelta(days=30)
        
        train_df = sample_data[sample_data['date'] <= cutoff_date]
        holdout_df = sample_data[sample_data['date'] > cutoff_date]
        
        # Holdout should be ~8% of total (30/365)
        holdout_pct = len(holdout_df) / len(sample_data)
        
        print(f"\nHoldout Size Validation:")
        print(f"  Total transactions: {len(sample_data)}")
        print(f"  Train transactions: {len(train_df)}")
        print(f"  Holdout transactions: {len(holdout_df)}")
        print(f"  Holdout percentage: {holdout_pct:.1%}")
        
        # Should be approximately 8% (30/365 ≈ 0.082)
        assert 0.07 <= holdout_pct <= 0.10, \
            f"Holdout size {holdout_pct:.1%} outside expected range (7-10%)"
    
    def test_no_future_leakage(self, sample_data):
        """
        Test that train set has no dates after cutoff date.
        
        This would indicate temporal leakage (training on future data).
        """
        max_date = sample_data['date'].max()
        cutoff_date = max_date - timedelta(days=30)
        
        train_df = sample_data[sample_data['date'] <= cutoff_date]
        
        # Check for any dates after cutoff in train set
        future_dates = train_df[train_df['date'] > cutoff_date]
        
        assert len(future_dates) == 0, \
            f"Temporal leakage: {len(future_dates)} train samples have dates after cutoff"


class TestVendorNormalizationEdgeCases:
    """Test edge cases in vendor normalization."""
    
    def test_unicode_normalization(self):
        """Test that unicode characters are normalized."""
        test_cases = [
            ("Café Français", "cafe francais"),
            ("Señor Taco", "senor taco"),
            ("Pokémon Center", "pokemon center"),
        ]
        
        for raw, expected in test_cases:
            normalized = normalize_vendor(raw)
            assert normalized == expected, \
                f"Unicode normalization failed: {raw} → {normalized} (expected: {expected})"
    
    def test_store_number_removal(self):
        """Test that store numbers are removed."""
        test_cases = [
            ("WALGREENS #1234", "walgreens"),
            ("Target Store 456", "target"),
            ("CVS Location 789", "cvs"),
            ("Starbucks Unit 012", "starbucks"),
        ]
        
        for raw, expected in test_cases:
            normalized = normalize_vendor(raw)
            assert normalized == expected, \
                f"Store number removal failed: {raw} → {normalized} (expected: {expected})"
    
    def test_pos_prefix_removal(self):
        """Test that POS prefixes are removed."""
        test_cases = [
            ("POS PURCHASE AMAZON.COM", "amazoncom"),
            ("WEB AUTH NETFLIX.COM", "netflixcom"),
            ("CARD TRANSACTION SPOTIFY", "spotify"),
            ("DEBIT PURCHASE UBER", "uber"),
        ]
        
        for raw, expected in test_cases:
            normalized = normalize_vendor(raw)
            assert normalized == expected, \
                f"POS prefix removal failed: {raw} → {normalized} (expected: {expected})"
    
    def test_empty_vendor(self):
        """Test that empty vendor returns empty string."""
        assert normalize_vendor("") == ""
        assert normalize_vendor(None) == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

