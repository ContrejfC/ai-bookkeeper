"""
Test Crawler Configuration
===========================

Tests for config loading and validation.
"""

import pytest
from pathlib import Path
from scripts.crawler.config import CrawlerConfig, load_config


def test_crawler_config_defaults():
    """Test CrawlerConfig with defaults."""
    config = CrawlerConfig(
        allow_domains=['chase.com'],
        seed_urls=['https://www.chase.com/statements']
    )
    
    assert config.allow_domains == ['chase.com']
    assert config.pdf_max_mb == 10
    assert config.respect_robots == True
    assert config.polite_delay_ms == 1500


def test_crawler_config_validation():
    """Test config validation."""
    # Empty domains should raise
    with pytest.raises(ValueError, match="allow_domains cannot be empty"):
        CrawlerConfig(allow_domains=[], seed_urls=['https://test.com'])
    
    # Empty seeds should raise
    with pytest.raises(ValueError, match="seed_urls cannot be empty"):
        CrawlerConfig(allow_domains=['test.com'], seed_urls=[])
    
    # Negative delay should raise
    with pytest.raises(ValueError, match="polite_delay_ms must be non-negative"):
        CrawlerConfig(
            allow_domains=['test.com'],
            seed_urls=['https://test.com'],
            polite_delay_ms=-1
        )


def test_pdf_max_bytes():
    """Test PDF size calculation."""
    config = CrawlerConfig(
        allow_domains=['test.com'],
        seed_urls=['https://test.com'],
        pdf_max_mb=5
    )
    
    assert config.pdf_max_bytes == 5 * 1024 * 1024


def test_polite_delay_seconds():
    """Test delay conversion."""
    config = CrawlerConfig(
        allow_domains=['test.com'],
        seed_urls=['https://test.com'],
        polite_delay_ms=2000
    )
    
    assert config.polite_delay_seconds == 2.0


def test_timeout_tuple():
    """Test timeout tuple."""
    config = CrawlerConfig(
        allow_domains=['test.com'],
        seed_urls=['https://test.com'],
        timeout_connect_s=5,
        timeout_read_s=10
    )
    
    assert config.timeout_tuple == (5, 10)


def test_load_config_file_not_found():
    """Test loading non-existent config file."""
    with pytest.raises(FileNotFoundError):
        load_config(Path("nonexistent.yaml"))


def test_config_nested_defaults():
    """Test nested dict defaults."""
    config = CrawlerConfig(
        allow_domains=['test.com'],
        seed_urls=['https://test.com']
    )
    
    # extract_features should have defaults
    assert config.extract_features['pii_redaction'] == True
    assert config.extract_features['max_pages_to_analyze'] == 3
    
    # serp_api should have defaults
    assert config.serp_api['enabled'] == False



