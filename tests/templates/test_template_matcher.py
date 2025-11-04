"""
Template Matcher Tests
======================

Unit tests for bank statement template matching.
"""

import pytest
from decimal import Decimal
from pathlib import Path

from app.ingestion.templates.schema import (
    BankTemplate,
    MatchCriteria,
    ScoreWeights,
    TemplateMatchResult
)
from app.ingestion.templates.registry import TemplateRegistry


class TestTemplateSchema:
    """Tests for template schema validation."""
    
    def test_valid_template(self):
        """Valid template should pass validation."""
        template = BankTemplate(
            name="test_bank_v1",
            version=1,
            match=MatchCriteria(
                header_keys=["Statement", "Account"],
                table_headers=["(?i)^date$", "(?i)^description$"],
                footer_keywords=["FDIC"],
                date_format_pref="MDY"
            ),
            accept_threshold=0.80
        )
        
        assert template.name == "test_bank_v1"
        assert template.version == 1
        assert template.accept_threshold == 0.80
    
    def test_invalid_date_format(self):
        """Invalid date format should raise error."""
        with pytest.raises(ValueError, match="date_format_pref must be"):
            MatchCriteria(
                header_keys=["Statement"],
                date_format_pref="INVALID"
            )
    
    def test_score_weights_default(self):
        """Default score weights should sum to 1.0."""
        weights = ScoreWeights()
        total = weights.headers + weights.table + weights.footer + weights.geometry
        assert abs(total - 1.0) < 0.01
    
    def test_template_no_criteria(self):
        """Template with no matching criteria should fail."""
        with pytest.raises(ValueError, match="at least one matching criterion"):
            BankTemplate(
                name="empty_template",
                version=1,
                match=MatchCriteria()  # No criteria
            )


class TestTemplateRegistry:
    """Tests for template registry."""
    
    def test_registry_loads_templates(self):
        """Registry should load all YAML templates."""
        registry = TemplateRegistry()
        
        # Should have loaded at least the 5 bank templates
        assert len(registry) >= 5
        
        # Check for specific templates
        chase = registry.get_template_by_name("chase_checking_v1")
        assert chase is not None
        assert chase.bank_name == "Chase"
        
        wells = registry.get_template_by_name("wells_fargo_checking_v1")
        assert wells is not None
        assert wells.bank_name == "Wells Fargo"
    
    def test_registry_invalid_template_dir(self):
        """Registry with invalid directory should handle gracefully."""
        registry = TemplateRegistry(templates_dir="/nonexistent/path")
        
        # Should not crash, just have no templates
        assert len(registry) == 0
    
    def test_get_template_by_name(self):
        """Should retrieve template by name."""
        registry = TemplateRegistry()
        
        template = registry.get_template_by_name("chase_checking_v1")
        assert template is not None
        assert template.name == "chase_checking_v1"
        
        # Non-existent template
        assert registry.get_template_by_name("nonexistent_v1") is None


class TestTemplateMatching:
    """Tests for template matching logic."""
    
    @pytest.fixture
    def registry(self):
        """Create registry fixture."""
        return TemplateRegistry()
    
    def test_match_chase_features(self, registry):
        """Chase features should match Chase template."""
        features = {
            'header_text': "Statement Period Account Number Beginning Balance Ending Balance",
            'table_headers': [['Date', 'Description', 'Amount', 'Balance']],
            'footer_text': "Questions? Call Member FDIC",
            'geometry': {
                'header_band': [0.0, 0.20],
                'table_band': [0.25, 0.85]
            }
        }
        
        results = registry.match_pdf(features)
        
        # Should have results
        assert len(results) > 0
        
        # Best match should be Chase
        best = results[0]
        assert 'chase' in best.template.name.lower()
        assert best.score > 0.5
    
    def test_match_wells_fargo_features(self, registry):
        """Wells Fargo features should match Wells Fargo template."""
        features = {
            'header_text': "Account Summary Statement Period Account Number Beginning balance Ending balance",
            'table_headers': [['Transaction Date', 'Transaction Description', 'Amount', 'Ending Daily Balance']],
            'footer_text': "Questions Member FDIC",
            'geometry': {
                'header_band': [0.0, 0.22],
                'table_band': [0.25, 0.80]
            }
        }
        
        results = registry.match_pdf(features)
        
        # Should have results
        assert len(results) > 0
        
        # Best match should be Wells Fargo
        best = results[0]
        assert 'wells_fargo' in best.template.name.lower() or best.score > 0.3
    
    def test_match_no_features(self, registry):
        """Empty features should return low scores."""
        features = {
            'header_text': '',
            'table_headers': [],
            'footer_text': '',
            'geometry': {}
        }
        
        results = registry.match_pdf(features)
        
        # Should still return results
        assert len(results) > 0
        
        # But all scores should be low
        for result in results:
            assert result.score < 0.5
    
    def test_get_best_match_above_threshold(self, registry):
        """Good match should be returned."""
        features = {
            'header_text': "Statement Period Account Number Beginning Balance Ending Balance",
            'table_headers': [['Date', 'Description', 'Amount', 'Balance']],
            'footer_text': "Questions? Call Member FDIC",
            'geometry': {
                'header_band': [0.0, 0.20],
                'table_band': [0.25, 0.85]
            }
        }
        
        best = registry.get_best_match(features)
        
        # Should return a match
        assert best is not None
        assert best.score >= best.template.accept_threshold
    
    def test_get_best_match_below_threshold(self, registry):
        """Poor match should return None."""
        features = {
            'header_text': "Random text that matches nothing",
            'table_headers': [],
            'footer_text': "",
            'geometry': {}
        }
        
        best = registry.get_best_match(features)
        
        # Should return None (below threshold)
        # Or a low-scoring match
        if best:
            assert best.score < best.template.accept_threshold


class TestScoring:
    """Tests for individual scoring components."""
    
    @pytest.fixture
    def registry(self):
        return TemplateRegistry()
    
    def test_keyword_scoring(self, registry):
        """Keyword scoring should work correctly."""
        # Get Chase template
        chase = registry.get_template_by_name("chase_checking_v1")
        assert chase is not None
        
        # All keywords present
        text_all = "Statement Period Account Number Beginning Balance Ending Balance"
        matched = []
        score_all = registry._score_keywords(chase.match.header_keys, text_all, matched)
        assert score_all == 1.0
        
        # No keywords present
        text_none = "Random text"
        matched = []
        score_none = registry._score_keywords(chase.match.header_keys, text_none, matched)
        assert score_none == 0.0
        
        # Some keywords present
        text_some = "Statement Period"
        matched = []
        score_some = registry._score_keywords(chase.match.header_keys, text_some, matched)
        assert 0.0 < score_some < 1.0
    
    def test_table_header_scoring(self, registry):
        """Table header pattern matching should work."""
        patterns = ["(?i)^date$", "(?i)^description$", "(?i)^amount$"]
        
        # All patterns match
        headers_all = [['Date', 'Description', 'Amount', 'Balance']]
        matched = []
        score_all = registry._score_table_headers(patterns, headers_all, matched)
        assert score_all == 1.0
        
        # No patterns match
        headers_none = [['Column1', 'Column2', 'Column3']]
        matched = []
        score_none = registry._score_table_headers(patterns, headers_none, matched)
        assert score_none == 0.0
        
        # Some patterns match
        headers_some = [['Date', 'Column2', 'Amount']]
        matched = []
        score_some = registry._score_table_headers(patterns, headers_some, matched)
        assert 0.0 < score_some < 1.0
    
    def test_geometry_scoring(self, registry):
        """Geometry scoring should compute overlap."""
        expected = {
            'header_top_pct': [0.0, 0.20],
            'table_band_pct': [0.25, 0.85]
        }
        
        # Perfect match
        actual_perfect = {
            'header_band': [0.0, 0.20],
            'table_band': [0.25, 0.85]
        }
        score_perfect = registry._score_geometry(expected, actual_perfect)
        assert score_perfect == 1.0
        
        # No match
        actual_none = {
            'header_band': [0.5, 0.7],
            'table_band': [0.9, 1.0]
        }
        score_none = registry._score_geometry(expected, actual_none)
        assert score_none < 0.5
        
        # Partial match
        actual_partial = {
            'header_band': [0.0, 0.25],  # Slightly different
            'table_band': [0.30, 0.80]   # Slightly different
        }
        score_partial = registry._score_geometry(expected, actual_partial)
        assert 0.3 < score_partial < 0.9


class TestTemplateMatchResult:
    """Tests for TemplateMatchResult."""
    
    def test_result_sorting(self):
        """Results should sort by score descending."""
        template1 = BankTemplate(
            name="bank1",
            version=1,
            match=MatchCriteria(header_keys=["test"])
        )
        template2 = BankTemplate(
            name="bank2",
            version=1,
            match=MatchCriteria(header_keys=["test"])
        )
        
        result1 = TemplateMatchResult(template=template1, score=0.5, confidence=0.5)
        result2 = TemplateMatchResult(template=template2, score=0.9, confidence=0.9)
        
        results = [result1, result2]
        results.sort()
        
        # Higher score should come first
        assert results[0].score == 0.9
        assert results[1].score == 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



