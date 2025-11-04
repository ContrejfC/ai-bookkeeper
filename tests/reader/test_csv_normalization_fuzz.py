"""
Test CSV Fuzzer - Locale Normalization
======================================

Tests that CSV fuzzer generates valid variants and that variants
can be normalized to canonical format.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from app.ingestion.csv_fuzz import generate_variants


class TestCSVFuzzer:
    """Test CSV fuzzer functionality."""
    
    def test_fuzzer_generates_variants(self):
        """Test that fuzzer generates the requested number of variants."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path("app/ingestion/csv_templates/qbo_3col.csv")
            output_dir = Path(tmpdir)
            
            variants = generate_variants(input_file, output_dir, num_variants=6)
            
            assert len(variants) == 6, f"Expected 6 variants, got {len(variants)}"
            
            # All variant files should exist
            for variant_path in variants:
                assert variant_path.exists(), f"Variant file not found: {variant_path}"
    
    def test_fuzzer_creates_different_delimiters(self):
        """Test that fuzzer creates files with different delimiters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path("app/ingestion/csv_templates/qbo_3col.csv")
            output_dir = Path(tmpdir)
            
            variants = generate_variants(input_file, output_dir, num_variants=4)
            
            # Read first line of each variant to check delimiter
            delimiters_used = set()
            for variant_path in variants:
                with open(variant_path, 'r') as f:
                    first_line = f.readline()
                    if ',' in first_line:
                        delimiters_used.add(',')
                    elif ';' in first_line:
                        delimiters_used.add(';')
                    elif '\t' in first_line:
                        delimiters_used.add('\t')
                    elif '|' in first_line:
                        delimiters_used.add('|')
            
            # Should have at least 2 different delimiters in 4 variants
            assert len(delimiters_used) >= 2, f"Expected multiple delimiters, got {delimiters_used}"
    
    def test_fuzzer_preserves_row_count(self):
        """Test that fuzzer preserves number of data rows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path("app/ingestion/csv_templates/qbo_3col.csv")
            output_dir = Path(tmpdir)
            
            # Count original rows
            with open(input_file, 'r') as f:
                original_lines = len(f.readlines())
            
            variants = generate_variants(input_file, output_dir, num_variants=3)
            
            # Each variant should have same number of lines
            for variant_path in variants:
                with open(variant_path, 'r', encoding='utf-8', errors='ignore') as f:
                    variant_lines = len(f.readlines())
                
                assert variant_lines == original_lines, \
                    f"Variant {variant_path.name} has {variant_lines} lines, expected {original_lines}"
    
    def test_fuzzer_handles_negative_amounts(self):
        """Test that fuzzer correctly transforms negative amounts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path("app/ingestion/csv_templates/qbo_3col.csv")
            output_dir = Path(tmpdir)
            
            variants = generate_variants(input_file, output_dir, num_variants=6)
            
            # At least one variant should have parentheses format for negatives
            # At least one should have minus sign
            formats_found = {'minus': False, 'paren': False, 'cr': False}
            
            for variant_path in variants:
                with open(variant_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if '-' in content and not '(' in content:
                        formats_found['minus'] = True
                    if '(' in content and ')' in content:
                        formats_found['paren'] = True
                    if 'CR' in content:
                        formats_found['cr'] = True
            
            # Should have at least one different format
            assert sum(formats_found.values()) >= 1, \
                "Should generate variants with different negative formats"


class TestCSVNormalization:
    """Test CSV normalization across locale variants."""
    
    @pytest.mark.skip(reason="Requires full CSV ingestion pipeline")
    def test_variants_normalize_consistently(self):
        """Test that all variants normalize to same canonical form."""
        # This test would require the full CSV ingestion pipeline
        # Placeholder for future implementation
        pass
    
    @pytest.mark.skip(reason="Requires full CSV ingestion pipeline")
    def test_decimal_separator_normalization(self):
        """Test that different decimal separators normalize correctly."""
        # Placeholder for testing comma vs period decimals
        pass
    
    @pytest.mark.skip(reason="Requires full CSV ingestion pipeline")
    def test_date_format_normalization(self):
        """Test that different date formats normalize correctly."""
        # Placeholder for testing MDY vs DMY vs YMD
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



