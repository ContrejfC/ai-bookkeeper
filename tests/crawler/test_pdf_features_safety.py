"""
Test PII Redaction in Feature Extraction
=========================================

Tests to ensure PII is properly redacted from extracted features.
"""

import pytest
from pathlib import Path
from scripts.crawler.pdf_features import _redact_pii, _extract_tokens


class TestPIIRedaction:
    """Tests for PII redaction."""
    
    def test_redact_email(self):
        """Test email redaction."""
        text = "Contact us at support@example.com for help."
        redacted = _redact_pii(text)
        
        assert "support@example.com" not in redacted
        assert "***EMAIL***" in redacted
    
    def test_redact_phone(self):
        """Test phone number redaction."""
        # Various phone formats
        texts = [
            "Call 123-456-7890 for help",
            "Phone: (555) 123-4567",
            "Contact 555.123.4567",
        ]
        
        for text in texts:
            redacted = _redact_pii(text)
            assert "***PHONE***" in redacted
            # Check no digits remain in phone-like patterns
            assert "123-456-7890" not in redacted
            assert "(555) 123-4567" not in redacted
    
    def test_redact_ssn(self):
        """Test SSN redaction."""
        text = "SSN: 123-45-6789 on file"
        redacted = _redact_pii(text)
        
        assert "123-45-6789" not in redacted
        assert "***SSN***" in redacted
    
    def test_redact_account_number(self):
        """Test account number redaction."""
        text = "Account 1234567890 has been credited"
        redacted = _redact_pii(text)
        
        assert "1234567890" not in redacted
        assert "***ACCOUNT***" in redacted
    
    def test_redact_credit_card(self):
        """Test credit card redaction."""
        texts = [
            "Card 1234 5678 9012 3456",
            "Card 1234-5678-9012-3456",
        ]
        
        for text in texts:
            redacted = _redact_pii(text)
            assert "***CARD***" in redacted
            assert "1234" not in redacted or redacted.count("1234") == 0
    
    def test_redact_multiple_pii(self):
        """Test multiple PII types in same text."""
        text = "Contact john.doe@example.com or call (555) 123-4567. Account: 9876543210"
        redacted = _redact_pii(text)
        
        # All PII should be redacted
        assert "john.doe@example.com" not in redacted
        assert "(555) 123-4567" not in redacted
        assert "9876543210" not in redacted
        
        # Redaction tokens should be present
        assert "***EMAIL***" in redacted
        assert "***PHONE***" in redacted
        assert "***ACCOUNT***" in redacted
    
    def test_redact_preserves_safe_text(self):
        """Test that safe text is preserved."""
        text = "Bank of America Statement for January 2023"
        redacted = _redact_pii(text)
        
        # Safe text should remain
        assert "Bank of America" in redacted
        assert "Statement" in redacted
        assert "January" in redacted


class TestTokenExtraction:
    """Tests for token extraction."""
    
    def test_extract_tokens_basic(self):
        """Test basic token extraction."""
        text = "Bank of America Statement Period"
        tokens = _extract_tokens(text)
        
        assert "bank" in tokens
        assert "america" in tokens
        assert "statement" in tokens
        assert "period" in tokens
    
    def test_extract_tokens_removes_stop_words(self):
        """Test that common stop words are removed."""
        text = "The bank statement is for the account"
        tokens = _extract_tokens(text)
        
        # Stop words should be removed
        assert "the" not in tokens
        assert "is" not in tokens
        assert "for" not in tokens
        
        # Content words should remain
        assert "bank" in tokens
        assert "statement" in tokens
        assert "account" in tokens
    
    def test_extract_tokens_unique_and_sorted(self):
        """Test tokens are unique and sorted."""
        text = "statement bank statement account bank"
        tokens = _extract_tokens(text)
        
        # Should be unique
        assert tokens.count("statement") == 1
        assert tokens.count("bank") == 1
        
        # Should be sorted
        assert tokens == sorted(tokens)
    
    def test_extract_tokens_min_length(self):
        """Test minimum token length."""
        text = "Bank of a statement at US"
        tokens = _extract_tokens(text)
        
        # Single letter words should be excluded (< 2 chars)
        assert "a" not in tokens
        
        # 2+ letter words should be included (except stop words)
        assert "bank" in tokens
        assert "statement" in tokens
    
    def test_extract_tokens_empty_input(self):
        """Test empty input."""
        assert _extract_tokens("") == []
        assert _extract_tokens(None) == []


class TestFeatureExtractionSafety:
    """Integration tests for feature extraction safety."""
    
    def test_features_contain_no_raw_pii(self):
        """Test that extracted features contain no raw PII."""
        # This would require a test PDF with PII
        # For now, we test the redaction functions work
        
        pii_text = """
        Contact: john.doe@example.com
        Phone: (555) 123-4567
        Account: 1234567890
        SSN: 123-45-6789
        """
        
        redacted = _redact_pii(pii_text)
        
        # Verify all PII is redacted
        assert "@example.com" not in redacted
        assert "123-4567" not in redacted
        assert "1234567890" not in redacted
        assert "123-45-6789" not in redacted
    
    def test_tokens_safe_for_storage(self):
        """Test that extracted tokens are safe to store."""
        text_with_pii = "Account 1234567890 at support@bank.com"
        
        # First redact PII
        redacted = _redact_pii(text_with_pii)
        
        # Then extract tokens
        tokens = _extract_tokens(redacted)
        
        # Tokens should not contain PII
        assert "1234567890" not in ' '.join(tokens)
        assert "support" not in ' '.join(tokens)
        
        # Should contain safe words
        assert "account" in tokens


def test_pii_redaction_enabled_by_default():
    """Test that PII redaction is enabled by default in config."""
    from scripts.crawler.config import CrawlerConfig
    
    config = CrawlerConfig(
        allow_domains=['test.com'],
        seed_urls=['https://test.com']
    )
    
    assert config.extract_features['pii_redaction'] == True



