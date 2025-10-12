"""
Comprehensive test suite for OCR document processing.

Tests cover:
- OCR parsing
- Confidence calibration
- LLM validation
- Document-to-transaction reconciliation
- API endpoints
- Edge cases
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ocr.ocr_parser import OCRParser, TesseractOCR
from app.ocr.confidence_calibrator import ConfidenceCalibrator, FieldThresholds
from app.ocr.llm_validator import LLMValidator, DisabledValidator
from app.ocr.reconcile_docs import DocumentReconciler


class TestOCRParser:
    """Test OCR parsing functionality."""
    
    def test_parses_basic_receipt_correctly(self):
        """Test that basic receipt fields are extracted."""
        # Mock OCR provider
        mock_provider = Mock()
        mock_provider.extract_text.return_value = (
            "Starbucks Coffee\n"
            "123 Main St\n"
            "Date: 10/08/2025\n"
            "Total: $12.50\n",
            0.90
        )
        
        parser = OCRParser(provider=mock_provider)
        result = parser.parse_document("fake_receipt.jpg")
        
        assert result['status'] == 'success'
        assert 'vendor' in result['fields']
        assert 'amount' in result['fields']
        assert 'date' in result['fields']
        assert result['fields']['amount']['value'] == 12.50
    
    def test_handles_multiple_date_formats(self):
        """Test that various date formats are parsed correctly."""
        parser = OCRParser(provider=Mock())
        
        # Test US format
        date1 = parser._parse_date("10/08/2025")
        assert date1 == "2025-10-08"
        
        # Test ISO format
        date2 = parser._parse_date("2025-10-08")
        assert date2 == "2025-10-08"
        
        # Test month name format
        date3 = parser._parse_date("8 Oct 2025")
        assert date3 == "2025-10-08"
    
    def test_normalizes_amount_formats(self):
        """Test amount extraction with various formats."""
        mock_provider = Mock()
        parser = OCRParser(provider=mock_provider)
        
        # Test currency symbol
        text1 = "Total: $123.45"
        amount1, _ = parser._extract_amount(text1, 0.9)
        assert amount1 == 123.45
        
        # Test without symbol
        text2 = "Amount: 98.76"
        amount2, _ = parser._extract_amount(text2, 0.9)
        assert amount2 == 98.76
        
        # Test with comma
        text3 = "Total $1,234.56"
        amount3, _ = parser._extract_amount(text3, 0.9)
        assert amount3 == 1234.56
    
    def test_handles_ocr_noise(self):
        """Test handling of common OCR artifacts."""
        mock_provider = Mock()
        mock_provider.extract_text.return_value = (
            "Sta rbucks  Coff ee\n"  # Extra spaces
            "To tal:  $ 1 2 . 5 0\n",  # Spaces in amount
            0.75
        )
        
        parser = OCRParser(provider=mock_provider)
        result = parser.parse_document("noisy_receipt.jpg")
        
        # Should still extract some fields
        assert result['status'] == 'success'
        assert len(result['fields']) > 0


class TestConfidenceCalibrator:
    """Test confidence calibration and routing."""
    
    def test_fields_above_threshold_accepted(self):
        """Test that high-confidence fields are accepted."""
        calibrator = ConfidenceCalibrator()
        
        fields = {
            'vendor': {'value': 'Starbucks', 'confidence': 0.95},
            'amount': {'value': 12.50, 'confidence': 0.98},
            'date': {'value': '2025-10-08', 'confidence': 0.90}
        }
        
        decisions = calibrator.evaluate_fields(fields)
        
        assert decisions['vendor'] == 'accept'
        assert decisions['amount'] == 'accept'
        assert decisions['date'] == 'accept'
    
    def test_fields_below_threshold_route_to_llm(self):
        """Test that low-confidence fields route to LLM validation."""
        calibrator = ConfidenceCalibrator()
        
        fields = {
            'vendor': {'value': 'St4rbucks', 'confidence': 0.72},  # Below 0.80
            'amount': {'value': 12.50, 'confidence': 0.88},  # Below 0.92
            'date': {'value': '10/08/2025', 'confidence': 0.78}  # Below 0.85
        }
        
        decisions = calibrator.evaluate_fields(fields)
        
        assert decisions['vendor'] == 'validate_llm'
        assert decisions['amount'] == 'validate_llm'
        assert decisions['date'] == 'validate_llm'
    
    def test_critically_low_confidence_routes_to_human(self):
        """Test that very low confidence routes to human review."""
        calibrator = ConfidenceCalibrator()
        
        fields = {
            'vendor': {'value': 'Starbucks', 'confidence': 0.45},  # Very low
            'amount': {'value': 12.50, 'confidence': 0.50}  # Very low
        }
        
        decisions = calibrator.evaluate_fields(fields)
        
        assert decisions['vendor'] == 'review'
        assert decisions['amount'] == 'review'
    
    def test_composite_score_calculation(self):
        """Test composite score for doc-txn matching."""
        calibrator = ConfidenceCalibrator()
        
        score = calibrator.compute_composite_score(
            vendor_similarity=0.95,
            amount_match=1.0,
            date_match=0.90
        )
        
        # Default weights: vendor=0.4, amount=0.4, date=0.2
        expected = 0.95 * 0.4 + 1.0 * 0.4 + 0.90 * 0.2
        assert abs(score - expected) < 0.01
    
    def test_needs_human_review_detection(self):
        """Test detection of human review requirement."""
        calibrator = ConfidenceCalibrator()
        
        decisions_no_review = {
            'vendor': 'accept',
            'amount': 'validate_llm'
        }
        assert not calibrator.needs_human_review(decisions_no_review)
        
        decisions_with_review = {
            'vendor': 'accept',
            'amount': 'review'
        }
        assert calibrator.needs_human_review(decisions_with_review)


class TestLLMValidator:
    """Test LLM validation functionality."""
    
    def test_llm_validation_stub_when_disabled(self):
        """Test that LLM validation is no-op when disabled."""
        validator = LLMValidator(provider="disabled")
        
        fields = {
            'vendor': {'value': 'St4rbucks', 'confidence': 0.72}
        }
        
        result = validator.validate("some text", fields)
        
        # Should return fields unchanged
        assert result == fields
        assert not validator.is_enabled()
    
    def test_llm_validation_enabled_check(self):
        """Test LLM validation enabled status."""
        validator_disabled = LLMValidator(provider="disabled")
        assert not validator_disabled.is_enabled()
        
        # OpenAI without key should also be disabled
        validator_no_key = LLMValidator(provider="openai", api_key="")
        assert not validator_no_key.is_enabled()
    
    def test_llm_validation_with_api_key(self):
        """Test LLM validation with API key (without actual API call)."""
        # Test that validator is initialized correctly with API key
        validator = LLMValidator(provider="openai", api_key="test_key")
        
        # Validator should be enabled with a key
        assert validator.provider_name == "openai"
        
        # Without actual API, validation should return fields unchanged or handle gracefully
        fields = {
            'vendor': {'value': 'St4rbucks', 'confidence': 0.72}
        }
        
        # This test verifies the validator structure, not actual API calls
        assert validator.is_enabled()  # Has API key, so enabled


class TestDocumentReconciliation:
    """Test document-to-transaction reconciliation."""
    
    def test_vendor_similarity_matching(self):
        """Test vendor string similarity calculation."""
        reconciler = DocumentReconciler()
        
        from app.ocr.reconcile_docs import jaro_winkler_similarity
        
        # Exact match
        assert jaro_winkler_similarity("Starbucks", "Starbucks") > 0.95
        
        # Similar
        assert jaro_winkler_similarity("Starbucks Coffee", "Starbucks") > 0.70
        
        # Different
        assert jaro_winkler_similarity("Starbucks", "Walmart") < 0.50
    
    def test_amount_tolerance_matching(self):
        """Test amount matching with tolerance."""
        reconciler = DocumentReconciler(amount_tolerance=0.05)
        
        doc_fields = {
            'vendor': {'value': 'Starbucks', 'confidence': 0.90},
            'amount': {'value': 12.50, 'confidence': 0.95},
            'date': {'value': '2025-10-08', 'confidence': 0.85}
        }
        
        # Exact match
        txn1 = {
            'txn_id': 'txn1',
            'counterparty': 'Starbucks',
            'amount': -12.50,
            'date': '2025-10-08'
        }
        
        result1 = reconciler.reconcile_document(doc_fields, [txn1])
        assert result1['status'] in ['matched', 'review_required']
        assert result1['match_confidence'] > 0.80
        
        # Within tolerance
        txn2 = {
            'txn_id': 'txn2',
            'counterparty': 'Starbucks',
            'amount': -12.52,  # +$0.02
            'date': '2025-10-08'
        }
        
        result2 = reconciler.reconcile_document(doc_fields, [txn2])
        assert result2['match_confidence'] > 0.75
    
    def test_date_window_matching(self):
        """Test date matching with window tolerance."""
        reconciler = DocumentReconciler(date_window_days=3)
        
        doc_fields = {
            'vendor': {'value': 'Starbucks', 'confidence': 0.90},
            'amount': {'value': 12.50, 'confidence': 0.95},
            'date': {'value': '2025-10-08', 'confidence': 0.85}
        }
        
        # Within 3-day window
        txn = {
            'txn_id': 'txn1',
            'counterparty': 'Starbucks',
            'amount': -12.50,
            'date': '2025-10-10'  # 2 days later
        }
        
        result = reconciler.reconcile_document(doc_fields, [txn])
        assert result['match_confidence'] > 0.70
    
    def test_match_accepted_when_composite_above_threshold(self):
        """Test that matches above threshold are auto-accepted."""
        thresholds = FieldThresholds(doc_txn_match_min=0.88)
        calibrator = ConfidenceCalibrator(thresholds)
        reconciler = DocumentReconciler()
        
        doc_fields = {
            'vendor': {'value': 'Starbucks', 'confidence': 0.90},
            'amount': {'value': 12.50, 'confidence': 0.95},
            'date': {'value': '2025-10-08', 'confidence': 0.85}
        }
        
        # Perfect match
        txn = {
            'txn_id': 'txn1',
            'counterparty': 'Starbucks',
            'amount': -12.50,
            'date': '2025-10-08'
        }
        
        result = reconciler.reconcile_document(doc_fields, [txn], calibrator)
        assert result['status'] == 'matched'
        assert result['match_confidence'] >= 0.88
    
    def test_no_match_when_no_candidates(self):
        """Test handling of no candidate transactions."""
        reconciler = DocumentReconciler()
        
        doc_fields = {
            'vendor': {'value': 'Starbucks', 'confidence': 0.90}
        }
        
        result = reconciler.reconcile_document(doc_fields, [])
        assert result['status'] == 'no_candidates'
        assert result['matched_transaction'] is None
    
    def test_edge_case_multiple_candidates_chooses_highest_score(self):
        """Test that highest-scoring transaction is chosen."""
        reconciler = DocumentReconciler()
        
        doc_fields = {
            'vendor': {'value': 'Starbucks', 'confidence': 0.90},
            'amount': {'value': 12.50, 'confidence': 0.95},
            'date': {'value': '2025-10-08', 'confidence': 0.85}
        }
        
        txns = [
            {'txn_id': 'txn1', 'counterparty': 'Starbucks', 'amount': -12.50, 'date': '2025-10-08'},
            {'txn_id': 'txn2', 'counterparty': 'Starbucks Coffee', 'amount': -12.48, 'date': '2025-10-07'},
            {'txn_id': 'txn3', 'counterparty': 'Starbucks', 'amount': -12.60, 'date': '2025-10-10'}
        ]
        
        result = reconciler.reconcile_document(doc_fields, txns)
        
        # txn1 should have highest score (perfect match)
        assert result['matched_transaction']['txn_id'] == 'txn1'


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_handles_unreadable_image(self):
        """Test handling of unreadable/corrupted images."""
        mock_provider = Mock()
        mock_provider.extract_text.return_value = ("", 0.0)
        
        parser = OCRParser(provider=mock_provider)
        result = parser.parse_document("corrupted.jpg")
        
        assert result['status'] == 'failed'
        assert 'error' in result
    
    def test_batch_processing_isolation(self):
        """Test that batch processing maintains isolation."""
        # This would test that failures in one document don't affect others
        # For now, we test that parse_document is independent
        
        mock_provider = Mock()
        parser = OCRParser(provider=mock_provider)
        
        # Document 1: Success
        mock_provider.extract_text.return_value = ("Starbucks\nTotal: $12.50", 0.90)
        result1 = parser.parse_document("doc1.jpg")
        
        # Document 2: Failure
        mock_provider.extract_text.return_value = ("", 0.0)
        result2 = parser.parse_document("doc2.jpg")
        
        # Document 3: Success
        mock_provider.extract_text.return_value = ("Walmart\nTotal: $50.00", 0.85)
        result3 = parser.parse_document("doc3.jpg")
        
        assert result1['status'] == 'success'
        assert result2['status'] == 'failed'
        assert result3['status'] == 'success'


class TestConfigurationToggles:
    """Test that environment configuration is respected."""
    
    def test_llm_validation_can_be_disabled(self):
        """Test LLM validation disabled via config."""
        validator = LLMValidator(provider="disabled")
        assert not validator.is_enabled()
    
    def test_custom_thresholds_applied(self):
        """Test custom confidence thresholds."""
        custom_thresholds = FieldThresholds(
            vendor_min=0.75,
            amount_min=0.88,
            date_min=0.80,
            category_min=0.70
        )
        
        calibrator = ConfidenceCalibrator(custom_thresholds)
        
        assert calibrator.thresholds.vendor_min == 0.75
        assert calibrator.thresholds.amount_min == 0.88


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

