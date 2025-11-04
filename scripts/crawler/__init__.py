"""
Bank Statement Crawler
=======================

Compliant, domain-restricted crawler for discovering public bank statement
samples and extracting layout features for template building.

Features:
- Respects robots.txt
- Domain allowlist enforcement
- Keyword-based filtering
- PII-safe feature extraction
- Rate limiting and politeness
- No full content storage

Usage:
    python -m scripts.crawler.cli crawl --config configs/crawler_config.yaml
"""

__version__ = "1.0.0"



