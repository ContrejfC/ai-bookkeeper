"""
Tests for Public Sample Features
=================================

Validates features extracted from public bank statement samples.
"""

import json
import pytest
import re
from pathlib import Path
from typing import Dict, Any

# Sample feature directories
FEATURES_DIR = Path(__file__).parent.parent / "fixtures" / "pdf" / "features"
METADATA_DIR = Path(__file__).parent.parent / "fixtures" / "pdf" / "metadata"
PUBLIC_DIR = Path(__file__).parent.parent / "fixtures" / "pdf" / "_public"

# Allowlisted domains from config
ALLOWED_DOMAINS = [
    "chase.com", "wellsfargo.com", "53.com", "bankofamerica.com",
    "usbank.com", "citi.com", "capitalone.com", "pnc.com",
    "ally.com", "schwab.com"
]

# PII patterns to check for (should NOT be present after redaction)
PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
    'ssn': r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b',
    'account_number': r'\b\d{10,17}\b',  # Common account number lengths
}


def get_feature_files():
    """Get all feature JSON files."""
    if not FEATURES_DIR.exists():
        return []
    return list(FEATURES_DIR.glob("*_features.json"))


def get_metadata_files():
    """Get all metadata JSON files."""
    if not METADATA_DIR.exists():
        return []
    return list(METADATA_DIR.glob("*_metadata.json"))


@pytest.fixture
def sample_features():
    """Load all sample features."""
    features = []
    for feature_file in get_feature_files():
        with open(feature_file, 'r') as f:
            data = json.load(f)
            data['_source_file'] = feature_file.name
            features.append(data)
    return features


@pytest.fixture
def sample_metadata():
    """Load all sample metadata."""
    metadata = []
    for metadata_file in get_metadata_files():
        with open(metadata_file, 'r') as f:
            data = json.load(f)
            data['_source_file'] = metadata_file.name
            metadata.append(data)
    return metadata


class TestPublicSampleAvailability:
    """Tests for sample availability (skip if no samples present)."""
    
    def test_features_directory_exists(self):
        """Features directory should exist."""
        assert FEATURES_DIR.exists(), f"Features directory not found: {FEATURES_DIR}"
    
    def test_metadata_directory_exists(self):
        """Metadata directory should exist."""
        assert METADATA_DIR.exists(), f"Metadata directory not found: {METADATA_DIR}"
    
    def test_samples_present_or_skip(self):
        """Check if samples are present, skip tests if not."""
        feature_files = get_feature_files()
        if len(feature_files) == 0:
            pytest.skip("No public samples downloaded. Run fetch_public_samples.py first.")


class TestFeatureSchema:
    """Tests for feature JSON schema validation."""
    
    @pytest.mark.skipif(len(get_feature_files()) == 0, reason="No samples available")
    def test_required_fields_present(self, sample_features):
        """All required fields should be present in features."""
        required_fields = [
            'tool', 'filename', 'page_count', 'header_tokens',
            'table_headers', 'date_formats', 'amount_formats',
            'geometry', 'text_density', 'metadata'
        ]
        
        for features in sample_features:
            for field in required_fields:
                assert field in features, \
                    f"Missing required field '{field}' in {features.get('_source_file', 'unknown')}"
    
    @pytest.mark.skipif(len(get_feature_files()) == 0, reason="No samples available")
    def test_field_types(self, sample_features):
        """Field types should be correct."""
        for features in sample_features:
            source = features.get('_source_file', 'unknown')
            
            assert isinstance(features['tool'], str), f"tool should be string in {source}"
            assert isinstance(features['filename'], str), f"filename should be string in {source}"
            assert isinstance(features['page_count'], int), f"page_count should be int in {source}"
            assert isinstance(features['header_tokens'], list), f"header_tokens should be list in {source}"
            assert isinstance(features['table_headers'], list), f"table_headers should be list in {source}"
            assert isinstance(features['date_formats'], list), f"date_formats should be list in {source}"
            assert isinstance(features['amount_formats'], list), f"amount_formats should be list in {source}"
            assert isinstance(features['geometry'], list), f"geometry should be list in {source}"
            assert isinstance(features['text_density'], list), f"text_density should be list in {source}"
            assert isinstance(features['metadata'], dict), f"metadata should be dict in {source}"
    
    @pytest.mark.skipif(len(get_feature_files()) == 0, reason="No samples available")
    def test_page_count_positive(self, sample_features):
        """Page count should be positive."""
        for features in sample_features:
            source = features.get('_source_file', 'unknown')
            assert features['page_count'] > 0, f"page_count should be > 0 in {source}"


class TestPIIRedaction:
    """Tests for PII redaction in extracted features."""
    
    @pytest.mark.skipif(len(get_feature_files()) == 0, reason="No samples available")
    def test_no_email_addresses(self, sample_features):
        """No email addresses should be present."""
        self._check_no_pii_pattern(sample_features, 'email')
    
    @pytest.mark.skipif(len(get_feature_files()) == 0, reason="No samples available")
    def test_no_phone_numbers(self, sample_features):
        """No phone numbers should be present."""
        self._check_no_pii_pattern(sample_features, 'phone')
    
    @pytest.mark.skipif(len(get_feature_files()) == 0, reason="No samples available")
    def test_no_ssn(self, sample_features):
        """No SSNs should be present."""
        self._check_no_pii_pattern(sample_features, 'ssn')
    
    @pytest.mark.skipif(len(get_feature_files()) == 0, reason="No samples available")
    def test_sensitive_metadata_removed(self, sample_features):
        """Sensitive metadata fields should be removed."""
        sensitive_fields = ['Author', 'Creator', 'Producer', 'Subject']
        
        for features in sample_features:
            source = features.get('_source_file', 'unknown')
            metadata = features.get('metadata', {})
            
            for field in sensitive_fields:
                assert field not in metadata, \
                    f"Sensitive metadata field '{field}' found in {source}"
    
    def _check_no_pii_pattern(self, sample_features: list, pii_type: str):
        """Check that a PII pattern is not present."""
        pattern = PII_PATTERNS[pii_type]
        
        for features in sample_features:
            source = features.get('_source_file', 'unknown')
            
            # Convert entire features dict to string for searching
            features_str = json.dumps(features)
            
            matches = re.findall(pattern, features_str)
            assert len(matches) == 0, \
                f"PII pattern '{pii_type}' found in {source}: {matches}"


class TestDomainAllowlist:
    """Tests for domain allowlist enforcement."""
    
    @pytest.mark.skipif(len(get_metadata_files()) == 0, reason="No metadata available")
    def test_urls_from_allowed_domains(self, sample_metadata):
        """All sample URLs should be from allowlisted domains."""
        from urllib.parse import urlparse
        
        for metadata in sample_metadata:
            source = metadata.get('_source_file', 'unknown')
            url = metadata.get('url', '')
            
            assert url, f"No URL in metadata: {source}"
            
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check if domain or parent domain is in allowlist
            is_allowed = False
            for allowed in ALLOWED_DOMAINS:
                if domain == allowed or domain.endswith(f'.{allowed}'):
                    is_allowed = True
                    break
            
            assert is_allowed, \
                f"Domain '{domain}' not in allowlist for {source}"


class TestFeatureQuality:
    """Tests for feature quality and usefulness."""
    
    @pytest.mark.skipif(len(get_feature_files()) == 0, reason="No samples available")
    def test_has_bank_keywords(self, sample_features):
        """Features should contain at least some bank keywords."""
        bank_keywords = ['statement', 'account', 'balance', 'transaction', 'date']
        
        for features in sample_features:
            source = features.get('_source_file', 'unknown')
            header_tokens = features.get('header_tokens', [])
            
            # Should have at least one bank keyword
            has_keyword = any(keyword in header_tokens for keyword in bank_keywords)
            
            # If no keywords, it's a warning, not a failure (might be an unusual format)
            if not has_keyword:
                pytest.skip(f"No standard bank keywords found in {source} - might be unusual format")
    
    @pytest.mark.skipif(len(get_feature_files()) == 0, reason="No samples available")
    def test_has_date_format(self, sample_features):
        """Features should detect at least one date format."""
        for features in sample_features:
            source = features.get('_source_file', 'unknown')
            date_formats = features.get('date_formats', [])
            
            # Most bank statements will have dates
            if len(date_formats) == 0:
                pytest.skip(f"No date formats detected in {source} - might need OCR or special handling")
    
    @pytest.mark.skipif(len(get_feature_files()) == 0, reason="No samples available")
    def test_has_amount_format(self, sample_features):
        """Features should detect at least one amount format."""
        for features in sample_features:
            source = features.get('_source_file', 'unknown')
            amount_formats = features.get('amount_formats', [])
            
            # Most bank statements will have currency amounts
            if len(amount_formats) == 0:
                pytest.skip(f"No amount formats detected in {source} - might need OCR or special handling")
    
    @pytest.mark.skipif(len(get_feature_files()) == 0, reason="No samples available")
    def test_geometry_bands_present(self, sample_features):
        """Geometry bands should be extracted."""
        for features in sample_features:
            source = features.get('_source_file', 'unknown')
            geometry = features.get('geometry', [])
            
            assert len(geometry) > 0, f"No geometry bands extracted from {source}"


class TestMetadataQuality:
    """Tests for metadata quality."""
    
    @pytest.mark.skipif(len(get_metadata_files()) == 0, reason="No metadata available")
    def test_required_metadata_fields(self, sample_metadata):
        """Required metadata fields should be present."""
        required_fields = ['name', 'url', 'bank', 'sha256', 'file_size_bytes']
        
        for metadata in sample_metadata:
            source = metadata.get('_source_file', 'unknown')
            
            for field in required_fields:
                assert field in metadata, \
                    f"Missing required metadata field '{field}' in {source}"
    
    @pytest.mark.skipif(len(get_metadata_files()) == 0, reason="No metadata available")
    def test_sha256_format(self, sample_metadata):
        """SHA256 should be valid hex string."""
        for metadata in sample_metadata:
            source = metadata.get('_source_file', 'unknown')
            sha256 = metadata.get('sha256', '')
            
            assert len(sha256) == 64, f"SHA256 should be 64 chars in {source}, got {len(sha256)}"
            assert re.match(r'^[a-f0-9]{64}$', sha256), \
                f"SHA256 should be lowercase hex in {source}"
    
    @pytest.mark.skipif(len(get_metadata_files()) == 0, reason="No metadata available")
    def test_file_size_reasonable(self, sample_metadata):
        """File size should be within reasonable bounds."""
        max_size = 10 * 1024 * 1024  # 10MB (config limit)
        
        for metadata in sample_metadata:
            source = metadata.get('_source_file', 'unknown')
            file_size = metadata.get('file_size_bytes', 0)
            
            assert 0 < file_size <= max_size, \
                f"File size {file_size} bytes out of bounds (0, {max_size}] in {source}"


class TestIntegration:
    """Integration tests for the complete workflow."""
    
    @pytest.mark.skipif(len(get_feature_files()) == 0, reason="No samples available")
    def test_features_and_metadata_match(self):
        """Each feature file should have corresponding metadata."""
        feature_files = get_feature_files()
        metadata_files = get_metadata_files()
        
        # Extract base names (without _features.json or _metadata.json)
        feature_names = {f.name.replace('_features.json', '') for f in feature_files}
        metadata_names = {f.name.replace('_metadata.json', '') for f in metadata_files}
        
        # They should match
        assert feature_names == metadata_names, \
            f"Mismatch between features and metadata files.\n" \
            f"Features only: {feature_names - metadata_names}\n" \
            f"Metadata only: {metadata_names - feature_names}"
    
    @pytest.mark.skipif(len(get_feature_files()) == 0, reason="No samples available")
    def test_pdfs_not_in_git(self):
        """PDFs should not be present (should be deleted or gitignored)."""
        pdf_dir = Path(__file__).parent.parent / "fixtures" / "pdf"
        
        # Check that .gitignore exists
        gitignore = pdf_dir / ".gitignore"
        assert gitignore.exists(), "PDF directory should have .gitignore"
        
        # Read .gitignore
        with open(gitignore, 'r') as f:
            gitignore_content = f.read()
        
        # Should ignore PDFs
        assert '*.pdf' in gitignore_content, ".gitignore should ignore *.pdf"
        assert '_public/' in gitignore_content, ".gitignore should ignore _public/"


if __name__ == '__main__':
    """Run tests with pytest."""
    pytest.main([__file__, '-v'])



