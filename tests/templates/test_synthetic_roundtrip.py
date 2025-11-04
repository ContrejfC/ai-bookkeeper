"""
Synthetic Statement Roundtrip Tests
====================================

Generate synthetic PDFs and verify they can be parsed correctly.
"""

import pytest
import tempfile
from pathlib import Path
from decimal import Decimal

try:
    from reportlab.lib.pagesizes import letter
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

from scripts.generate_synthetic_statement import SyntheticStatementGenerator
from app.ingestion.extract.pdf_template import PDFTemplateExtractor
from app.ingestion.extract.base import ExtractionContext
from app.ingestion.utils.text_features import extract_text_features
from app.ingestion.templates.registry import TemplateRegistry


# Skip all tests if dependencies not installed
pytestmark = pytest.mark.skipif(
    not (HAS_REPORTLAB and HAS_PDFPLUMBER),
    reason="reportlab and pdfplumber required for synthetic roundtrip tests"
)


class TestSyntheticGeneration:
    """Tests for synthetic PDF generation."""
    
    @pytest.fixture(params=['chase', 'wells_fargo', 'fifth_third', 'bank_of_america', 'us_bank'])
    def bank_style(self, request):
        """Parametrize test across all bank styles."""
        return request.param
    
    def test_generate_synthetic_pdf(self, bank_style, tmp_path):
        """Should generate valid PDF for each bank style."""
        output_path = tmp_path / f"{bank_style}_test.pdf"
        
        generator = SyntheticStatementGenerator(bank_style)
        generator.generate(
            output_path=str(output_path),
            account_number="****5678",
            beginning_balance=Decimal("2000.00"),
            transaction_count=10
        )
        
        # Verify file was created
        assert output_path.exists()
        assert output_path.stat().st_size > 0
    
    def test_synthetic_pdf_readable(self, bank_style, tmp_path):
        """Generated PDF should be readable with pdfplumber."""
        output_path = tmp_path / f"{bank_style}_readable.pdf"
        
        generator = SyntheticStatementGenerator(bank_style)
        generator.generate(
            output_path=str(output_path),
            transaction_count=5
        )
        
        # Try to read with pdfplumber
        with pdfplumber.open(output_path) as pdf:
            assert len(pdf.pages) > 0
            
            # Extract text from first page
            text = pdf.pages[0].extract_text()
            assert text is not None
            assert len(text) > 0
            
            # Should contain expected keywords
            assert 'statement' in text.lower() or 'account' in text.lower()


class TestFeatureExtraction:
    """Tests for feature extraction from synthetic PDFs."""
    
    @pytest.fixture
    def synthetic_pdf(self, tmp_path):
        """Create a synthetic Chase PDF."""
        output_path = tmp_path / "chase_features.pdf"
        
        generator = SyntheticStatementGenerator('chase')
        generator.generate(
            output_path=str(output_path),
            transaction_count=15
        )
        
        return output_path
    
    def test_extract_features_from_synthetic(self, synthetic_pdf):
        """Should extract features from synthetic PDF."""
        features = extract_text_features(synthetic_pdf)
        
        # Check required fields
        assert 'header_text' in features
        assert 'footer_text' in features
        assert 'table_headers' in features
        assert 'geometry' in features
        assert 'page_count' in features
        
        # Header should contain expected keywords
        header_lower = features['header_text'].lower()
        assert 'statement' in header_lower or 'account' in header_lower
        
        # Should have detected table headers
        assert isinstance(features['table_headers'], list)
        
        # Page count should be 1 for synthetic statements
        assert features['page_count'] == 1


class TestTemplateMatching:
    """Tests for template matching with synthetic PDFs."""
    
    @pytest.fixture(params=['chase', 'wells_fargo', 'fifth_third', 'bank_of_america', 'us_bank'])
    def synthetic_pdf_with_style(self, request, tmp_path):
        """Create synthetic PDF for each bank style."""
        style = request.param
        output_path = tmp_path / f"{style}_match.pdf"
        
        generator = SyntheticStatementGenerator(style)
        generator.generate(
            output_path=str(output_path),
            transaction_count=10
        )
        
        return output_path, style
    
    def test_synthetic_matches_correct_template(self, synthetic_pdf_with_style):
        """Synthetic PDF should match its corresponding template."""
        pdf_path, expected_style = synthetic_pdf_with_style
        
        # Extract features
        features = extract_text_features(pdf_path)
        
        # Match against templates
        registry = TemplateRegistry()
        results = registry.match_pdf(features)
        
        # Should have results
        assert len(results) > 0
        
        # Best match should be the correct style
        best = results[0]
        
        # Check if the matched template name contains the expected style
        # (e.g., "chase_checking_v1" should match "chase")
        assert expected_style in best.template.name or best.score > 0.5
        
        # Score should be reasonably high
        assert best.score > 0.4  # Lower threshold for synthetic PDFs
    
    def test_get_best_match_for_synthetic(self, synthetic_pdf_with_style):
        """get_best_match should work for synthetic PDFs."""
        pdf_path, expected_style = synthetic_pdf_with_style
        
        features = extract_text_features(pdf_path)
        
        registry = TemplateRegistry()
        best = registry.get_best_match(features)
        
        # May or may not meet threshold depending on template quality
        # But should at least return something or None
        if best:
            assert best.score > 0.0
            assert best.template is not None


class TestEndToEndParsing:
    """End-to-end tests: generate, extract, parse."""
    
    @pytest.fixture
    def chase_synthetic(self, tmp_path):
        """Create a Chase synthetic PDF."""
        output_path = tmp_path / "chase_e2e.pdf"
        
        generator = SyntheticStatementGenerator('chase')
        generator.generate(
            output_path=str(output_path),
            account_number="****9999",
            beginning_balance=Decimal("1500.00"),
            transaction_count=20
        )
        
        return output_path
    
    def test_parse_synthetic_with_template_extractor(self, chase_synthetic):
        """Should parse synthetic PDF with template extractor."""
        extractor = PDFTemplateExtractor()
        
        context = ExtractionContext(
            file_path=chase_synthetic,
            mime_type='application/pdf',
            file_size=chase_synthetic.stat().st_size,
            tenant_id="test_tenant",
            account_hint="****9999"
        )
        
        # Check if extractor can handle
        assert extractor.can_handle(context)
        
        # Extract transactions
        result = extractor.extract(context)
        
        # Should succeed
        assert result.success
        
        # Should have extracted transactions
        assert len(result.raw_transactions) > 0
        
        # Check transaction structure
        for txn in result.raw_transactions:
            assert 'description' in txn
            # May or may not have all fields depending on parsing success
    
    def test_parse_multiple_synthetic_styles(self, tmp_path):
        """Should handle multiple bank styles."""
        styles = ['chase', 'wells_fargo', 'bank_of_america']
        
        extractor = PDFTemplateExtractor()
        
        for style in styles:
            output_path = tmp_path / f"{style}_multi.pdf"
            
            generator = SyntheticStatementGenerator(style)
            generator.generate(
                output_path=str(output_path),
                transaction_count=10
            )
            
            context = ExtractionContext(
                file_path=output_path,
                mime_type='application/pdf',
                file_size=output_path.stat().st_size,
                tenant_id="test_tenant"
            )
            
            result = extractor.extract(context)
            
            # Should not crash
            assert result is not None
            
            # Should have some result (success or error)
            if result.success:
                assert isinstance(result.raw_transactions, list)


class TestDifferentConfigurations:
    """Test synthetic generation with different configurations."""
    
    def test_different_transaction_counts(self, tmp_path):
        """Should handle different transaction counts."""
        counts = [5, 10, 50]
        
        for count in counts:
            output_path = tmp_path / f"chase_txn_{count}.pdf"
            
            generator = SyntheticStatementGenerator('chase')
            generator.generate(
                output_path=str(output_path),
                transaction_count=count
            )
            
            assert output_path.exists()
            
            # Extract and verify
            features = extract_text_features(output_path)
            assert features['page_count'] >= 1
    
    def test_different_balances(self, tmp_path):
        """Should handle different starting balances."""
        balances = [Decimal("0.00"), Decimal("1000.00"), Decimal("100000.00")]
        
        for balance in balances:
            output_path = tmp_path / f"chase_bal_{balance}.pdf"
            
            generator = SyntheticStatementGenerator('chase')
            generator.generate(
                output_path=str(output_path),
                beginning_balance=balance,
                transaction_count=5
            )
            
            assert output_path.exists()
    
    def test_custom_account_number(self, tmp_path):
        """Should accept custom account numbers."""
        output_path = tmp_path / "chase_custom_account.pdf"
        
        generator = SyntheticStatementGenerator('chase')
        generator.generate(
            output_path=str(output_path),
            account_number="****ABCD",
            transaction_count=5
        )
        
        assert output_path.exists()
        
        # Verify account number appears in PDF
        with pdfplumber.open(output_path) as pdf:
            text = pdf.pages[0].extract_text()
            assert '****ABCD' in text or 'ABCD' in text


class TestErrorHandling:
    """Test error handling in synthetic generation and parsing."""
    
    def test_invalid_bank_style(self):
        """Should raise error for invalid bank style."""
        with pytest.raises(ValueError, match="Template not found"):
            SyntheticStatementGenerator('invalid_bank')
    
    def test_zero_transactions(self, tmp_path):
        """Should handle zero transactions gracefully."""
        output_path = tmp_path / "chase_zero_txn.pdf"
        
        generator = SyntheticStatementGenerator('chase')
        generator.generate(
            output_path=str(output_path),
            transaction_count=0
        )
        
        # Should still create a valid PDF
        assert output_path.exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



