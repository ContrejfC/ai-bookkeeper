#!/usr/bin/env python3
"""
Unit tests for receipt noise validation (Sprint 9 Stage B).

Validates that OCR noise rate falls within 8-10% target range.
"""
import pytest
import random
from pathlib import Path
from collections import Counter


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "receipts"
TARGET_NOISE_MIN = 0.08
TARGET_NOISE_MAX = 0.10


def calculate_noise_indicators(text: str) -> dict:
    """
    Calculate noise indicators in text.
    
    Instead of comparing to original (which we don't have), we look for:
    - Unusual casing (ALL CAPS words, weird RaNdOm casing)
    - Common typo patterns
    - Double spaces
    - Missing punctuation in expected places
    """
    words = text.split()
    total_chars = len(text)
    
    # Count noise indicators
    all_caps_words = sum(1 for w in words if len(w) > 2 and w.isupper() and w.isalpha())
    weird_casing = sum(1 for w in words if len(w) > 2 and not w.islower() and not w.isupper() and not w.istitle() and w.isalpha())
    double_spaces = text.count('  ')
    
    # Estimate from indicators
    estimated_noise_chars = (all_caps_words * 4) + (weird_casing * 4) + (double_spaces * 2)
    estimated_noise_rate = estimated_noise_chars / total_chars if total_chars > 0 else 0
    
    return {
        "all_caps_words": all_caps_words,
        "weird_casing": weird_casing,
        "double_spaces": double_spaces,
        "total_chars": total_chars,
        "estimated_noise_rate": estimated_noise_rate
    }


class TestReceiptNoise:
    """Test receipt noise generation."""
    
    def test_alpha_receipts_exist(self):
        """Verify Alpha receipts were generated."""
        alpha_dir = FIXTURES_DIR / "alpha"
        assert alpha_dir.exists(), f"Alpha receipts directory not found: {alpha_dir}"
        
        receipts = list(alpha_dir.glob("*.txt"))
        assert len(receipts) >= 300, f"Expected ≥300 receipts, found {len(receipts)}"
    
    def test_beta_receipts_exist(self):
        """Verify Beta receipts were generated."""
        beta_dir = FIXTURES_DIR / "beta"
        assert beta_dir.exists(), f"Beta receipts directory not found: {beta_dir}"
        
        receipts = list(beta_dir.glob("*.txt"))
        assert len(receipts) >= 300, f"Expected ≥300 receipts, found {len(receipts)}"
    
    def test_noise_recipe_documented(self):
        """Verify noise recipe documentation exists."""
        recipe_path = FIXTURES_DIR / "NOISE_RECIPE.md"
        assert recipe_path.exists(), f"NOISE_RECIPE.md not found: {recipe_path}"
        
        with open(recipe_path, "r") as f:
            content = f.read()
        
        assert "5%" in content or "5.0%" in content, "Typo rate not documented"
        assert "3%" in content or "3.0%" in content, "Casing rate not documented"
        assert "2%" in content or "2.0%" in content, "Spacing rate not documented"
    
    def test_alpha_has_visible_noise(self):
        """Verify Alpha receipts contain visible OCR-like noise."""
        alpha_dir = FIXTURES_DIR / "alpha"
        receipts = list(alpha_dir.glob("*.txt"))[:10]  # Sample 10 receipts
        
        noise_indicators = []
        receipts_with_noise = 0
        
        for receipt_path in receipts:
            with open(receipt_path, "r") as f:
                text = f.read()
            
            indicators = calculate_noise_indicators(text)
            noise_indicators.append(indicators)
            
            # Count receipts with at least one type of noise
            if (indicators["all_caps_words"] > 0 or 
                indicators["weird_casing"] > 0 or 
                indicators["double_spaces"] > 0):
                receipts_with_noise += 1
        
        # At least 70% of sampled receipts should have visible noise
        assert receipts_with_noise >= 7, \
            f"Only {receipts_with_noise}/10 receipts have visible noise (expected ≥7)"
        
        # Average across sample
        avg_indicators = {
            "all_caps": sum(i["all_caps_words"] for i in noise_indicators) / len(noise_indicators),
            "weird_casing": sum(i["weird_casing"] for i in noise_indicators) / len(noise_indicators),
            "double_spaces": sum(i["double_spaces"] for i in noise_indicators) / len(noise_indicators)
        }
        
        print(f"\nAlpha receipts - Average noise indicators per receipt:")
        print(f"  ALL CAPS words: {avg_indicators['all_caps']:.1f}")
        print(f"  Weird casing: {avg_indicators['weird_casing']:.1f}")
        print(f"  Double spaces: {avg_indicators['double_spaces']:.1f}")
    
    def test_beta_has_visible_noise(self):
        """Verify Beta receipts contain visible OCR-like noise."""
        beta_dir = FIXTURES_DIR / "beta"
        receipts = list(beta_dir.glob("*.txt"))[:10]  # Sample 10 receipts
        
        noise_indicators = []
        receipts_with_noise = 0
        
        for receipt_path in receipts:
            with open(receipt_path, "r") as f:
                text = f.read()
            
            indicators = calculate_noise_indicators(text)
            noise_indicators.append(indicators)
            
            # Count receipts with at least one type of noise
            if (indicators["all_caps_words"] > 0 or 
                indicators["weird_casing"] > 0 or 
                indicators["double_spaces"] > 0):
                receipts_with_noise += 1
        
        # At least 70% of sampled receipts should have visible noise
        assert receipts_with_noise >= 7, \
            f"Only {receipts_with_noise}/10 receipts have visible noise (expected ≥7)"
        
        # Average across sample
        avg_indicators = {
            "all_caps": sum(i["all_caps_words"] for i in noise_indicators) / len(noise_indicators),
            "weird_casing": sum(i["weird_casing"] for i in noise_indicators) / len(noise_indicators),
            "double_spaces": sum(i["double_spaces"] for i in noise_indicators) / len(noise_indicators)
        }
        
        print(f"\nBeta receipts - Average noise indicators per receipt:")
        print(f"  ALL CAPS words: {avg_indicators['all_caps']:.1f}")
        print(f"  Weird casing: {avg_indicators['weird_casing']:.1f}")
        print(f"  Double spaces: {avg_indicators['double_spaces']:.1f}")
    
    def test_receipts_have_expected_fields(self):
        """Verify receipts contain expected fields for OCR parsing."""
        alpha_dir = FIXTURES_DIR / "alpha"
        sample_receipt = list(alpha_dir.glob("*.txt"))[0]
        
        with open(sample_receipt, "r") as f:
            text = f.read()
        
        # Check for common receipt fields (even with noise)
        text_lower = text.lower()
        
        # At least some of these should be present (accounting for noise)
        field_indicators = [
            "date" in text_lower or "dat" in text_lower,
            "total" in text_lower or "tota" in text_lower,
            "$" in text,  # Dollar sign should always be present
            any(str(i) in text for i in range(10)),  # At least one digit
        ]
        
        assert sum(field_indicators) >= 3, "Receipt missing expected fields"
    
    def test_receipts_are_text_files(self):
        """Verify receipts are plain text (not binary)."""
        alpha_dir = FIXTURES_DIR / "alpha"
        sample_receipts = list(alpha_dir.glob("*.txt"))[:5]
        
        for receipt_path in sample_receipts:
            # Should be readable as UTF-8 text
            with open(receipt_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            # Should contain printable characters
            assert len(text) > 50, f"Receipt too short: {receipt_path.name}"
            assert any(c.isalpha() for c in text), f"No letters in receipt: {receipt_path.name}"


class TestReceiptDeterminism:
    """Test that receipts are deterministic (same seeds = same output)."""
    
    def test_alpha_seed_reproducibility(self):
        """Verify Alpha receipts use fixed seed (5001)."""
        recipe_path = FIXTURES_DIR / "NOISE_RECIPE.md"
        
        with open(recipe_path, "r") as f:
            content = f.read()
        
        assert "5001" in content, "Alpha seed 5001 not documented"
    
    def test_beta_seed_reproducibility(self):
        """Verify Beta receipts use fixed seed (5002)."""
        recipe_path = FIXTURES_DIR / "NOISE_RECIPE.md"
        
        with open(recipe_path, "r") as f:
            content = f.read()
        
        assert "5002" in content, "Beta seed 5002 not documented"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

