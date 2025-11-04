"""
Test Synthetic PDF Generation and Parsing
=========================================

Tests that synthetic PDFs can be generated and parsed back
through the ingestion pipeline.
"""

import pytest
from pathlib import Path
import tempfile
import yaml

# Try to import the generator
try:
    from scripts.synth_statements import generate_statement
    HAS_GENERATOR = True
except ImportError:
    HAS_GENERATOR = False


@pytest.mark.skipif(not HAS_GENERATOR, reason="ReportLab not installed or generator not available")
class TestSyntheticPDFGeneration:
    """Test synthetic PDF generator."""
    
    def test_checking_statement_generates(self):
        """Test that checking statement PDF generates without errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            style_path = Path("scripts/synth_statements/styles/checking.yaml")
            output_path = Path(tmpdir) / "checking.pdf"
            
            if not style_path.exists():
                pytest.skip(f"Style file not found: {style_path}")
            
            # Generate PDF
            generate_statement(
                style_path=style_path,
                output_path=output_path,
                num_rows=20,
                num_pages=1
            )
            
            # Verify file exists and has content
            assert output_path.exists(), "PDF should be generated"
            assert output_path.stat().st_size > 1000, "PDF should have content"
    
    def test_credit_card_statement_generates(self):
        """Test that credit card statement PDF generates without errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            style_path = Path("scripts/synth_statements/styles/credit_card.yaml")
            output_path = Path(tmpdir) / "credit_card.pdf"
            
            if not style_path.exists():
                pytest.skip(f"Style file not found: {style_path}")
            
            generate_statement(
                style_path=style_path,
                output_path=output_path,
                num_rows=30,
                num_pages=2
            )
            
            assert output_path.exists()
            assert output_path.stat().st_size > 1000
    
    def test_account_analysis_statement_generates(self):
        """Test that account analysis statement PDF generates without errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            style_path = Path("scripts/synth_statements/styles/account_analysis.yaml")
            output_path = Path(tmpdir) / "account_analysis.pdf"
            
            if not style_path.exists():
                pytest.skip(f"Style file not found: {style_path}")
            
            generate_statement(
                style_path=style_path,
                output_path=output_path,
                num_rows=50,
                num_pages=3
            )
            
            assert output_path.exists()
            assert output_path.stat().st_size > 1000
    
    def test_multi_page_generation(self):
        """Test that multi-page PDFs generate correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            style_path = Path("scripts/synth_statements/styles/checking.yaml")
            output_path = Path(tmpdir) / "multi_page.pdf"
            
            if not style_path.exists():
                pytest.skip(f"Style file not found: {style_path}")
            
            # Generate 3-page PDF
            generate_statement(
                style_path=style_path,
                output_path=output_path,
                num_rows=90,
                num_pages=3
            )
            
            assert output_path.exists()
            # Multi-page should be larger
            assert output_path.stat().st_size > 5000


@pytest.mark.skipif(True, reason="Requires full PDF ingestion pipeline")
class TestPDFRoundtrip:
    """Test that synthetic PDFs can be parsed back."""
    
    def test_checking_pdf_parses(self):
        """Test that generated checking PDF can be parsed."""
        # This would require:
        # 1. Generate synthetic PDF
        # 2. Pass through PDF extraction pipeline
        # 3. Validate transaction count matches
        # 4. Validate amounts match
        pass
    
    def test_reconciliation_from_pdf(self):
        """Test that parsed PDF reconciles correctly."""
        pass
    
    def test_header_extraction_from_pdf(self):
        """Test that header information is extracted."""
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



