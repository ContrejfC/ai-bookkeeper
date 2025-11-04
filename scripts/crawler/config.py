"""
Crawler Configuration
=====================

Load and validate crawler configuration from YAML.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

import yaml


@dataclass
class CrawlerConfig:
    """Crawler configuration."""
    
    # Domain restrictions
    allow_domains: List[str] = field(default_factory=list)
    seed_urls: List[str] = field(default_factory=list)
    
    # Keyword filtering
    keyword_allow: List[str] = field(default_factory=list)
    keyword_deny: List[str] = field(default_factory=list)
    
    # Content restrictions
    content_type_whitelist: List[str] = field(default_factory=list)
    pdf_max_mb: int = 10
    csv_max_mb: int = 5
    xml_max_mb: int = 5
    txt_max_mb: int = 2
    
    # Crawl limits
    html_max_pages_per_domain: int = 50
    max_pdfs_per_domain: int = 25
    max_csvs_per_domain: int = 15
    max_xmls_per_domain: int = 15
    max_txts_per_domain: int = 10
    max_depth: int = 3
    max_total_pdfs: int = 200
    max_total_files: int = 250
    
    # Politeness
    respect_robots: bool = True
    polite_delay_ms: int = 1500
    timeout_connect_s: int = 10
    timeout_read_s: int = 10
    max_retries: int = 3
    retry_backoff_factor: float = 0.5
    retry_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    user_agent: str = "AI-Bookkeeper-ResearchBot/1.0"
    
    # Storage
    save_pdfs: bool = False
    save_files: bool = False
    delete_after_extract: bool = True
    output_features_dir: str = "tests/fixtures/pdf/features/crawled"
    output_pdf_features_dir: str = "tests/fixtures/pdf/features/crawled"
    output_csv_features_dir: str = "tests/fixtures/csv/features/crawled"
    output_xml_features_dir: str = "tests/fixtures/xml/features/crawled"
    output_txt_features_dir: str = "tests/fixtures/txt/features/crawled"
    output_pdfs_dir: str = "tests/fixtures/pdf/_public/crawled"
    output_files_dir: str = "tests/fixtures/_public/crawled"
    output_report_path: str = "out/crawler_report.json"
    
    # Feature extraction
    extract_features: Dict[str, Any] = field(default_factory=dict)
    
    # Search API (optional)
    serp_api: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.allow_domains:
            raise ValueError("allow_domains cannot be empty")
        
        if not self.seed_urls:
            raise ValueError("seed_urls cannot be empty")
        
        if self.pdf_max_mb <= 0:
            raise ValueError("pdf_max_mb must be positive")
        
        if self.polite_delay_ms < 0:
            raise ValueError("polite_delay_ms must be non-negative")
        
        # Set defaults for nested dicts
        if not self.extract_features:
            self.extract_features = {
                "pii_redaction": True,
                "max_pages_to_analyze": 3,
                "extract_text_sample": False,
                "hash_sample_rows": True
            }
        
        if not self.serp_api:
            self.serp_api = {
                "enabled": False,
                "api_key": "",
                "queries_per_bank": [],
                "max_results_per_query": 10
            }
    
    @property
    def pdf_max_bytes(self) -> int:
        """PDF size limit in bytes."""
        return self.pdf_max_mb * 1024 * 1024
    
    @property
    def csv_max_bytes(self) -> int:
        """CSV size limit in bytes."""
        return self.csv_max_mb * 1024 * 1024
    
    @property
    def xml_max_bytes(self) -> int:
        """XML size limit in bytes."""
        return self.xml_max_mb * 1024 * 1024
    
    @property
    def txt_max_bytes(self) -> int:
        """TXT size limit in bytes."""
        return self.txt_max_mb * 1024 * 1024
    
    @property
    def polite_delay_seconds(self) -> float:
        """Polite delay in seconds."""
        return self.polite_delay_ms / 1000.0
    
    @property
    def timeout_tuple(self) -> tuple:
        """Timeout as (connect, read) tuple for httpx."""
        return (self.timeout_connect_s, self.timeout_read_s)


def load_config(config_path: Path) -> CrawlerConfig:
    """
    Load crawler configuration from YAML file.
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        CrawlerConfig instance
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If configuration is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    if not data:
        raise ValueError("Config file is empty")
    
    # Convert to dataclass
    config = CrawlerConfig(**data)
    
    return config


def get_default_config_path() -> Path:
    """Get default config path."""
    return Path(__file__).parent.parent.parent / "configs" / "crawler_config.yaml"

