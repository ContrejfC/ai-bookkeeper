"""
Main Crawler Orchestration
===========================

Ties together discovery, fetching, and feature extraction.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from scripts.crawler.config import CrawlerConfig
from scripts.crawler.robots import RobotsChecker
from scripts.crawler.discovery import LinkDiscovery
from scripts.crawler.fetch import PDFFetcher
from scripts.crawler.pdf_features import extract_safe_features, save_features
from scripts.crawler.content_types import detect_content_type, is_statement_like, get_file_size_limit
from scripts.crawler.csv_xml_features import extract_features as extract_non_pdf_features

logger = logging.getLogger(__name__)


class CrawlReport:
    """Tracks crawl statistics and results for multi-format crawler."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.domains_crawled = set()
        self.html_pages_visited = 0
        
        # Multi-format tracking
        self.files_discovered = {"pdf": 0, "csv": 0, "xml": 0, "txt": 0}
        self.files_downloaded = {"pdf": 0, "csv": 0, "xml": 0, "txt": 0}
        self.files_failed = {"pdf": 0, "csv": 0, "xml": 0, "txt": 0}
        self.features_extracted = {"pdf": 0, "csv": 0, "xml": 0, "txt": 0}
        
        self.robots_disallows = 0
        self.off_domain_skips = 0
        self.keyword_filtered = 0
        self.errors = []
        self.successes = []
        self.skips = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        end_time = datetime.now()
        duration_seconds = (end_time - self.start_time).total_seconds()
        
        total_discovered = sum(self.files_discovered.values())
        total_downloaded = sum(self.files_downloaded.values())
        total_failed = sum(self.files_failed.values())
        total_features = sum(self.features_extracted.values())
        
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": round(duration_seconds, 2),
            "summary": {
                "domains_crawled": len(self.domains_crawled),
                "html_pages_visited": self.html_pages_visited,
                "total_files_discovered": total_discovered,
                "total_files_downloaded": total_downloaded,
                "total_files_failed": total_failed,
                "total_features_extracted": total_features,
                "robots_disallows": self.robots_disallows,
                "off_domain_skips": self.off_domain_skips,
                "keyword_filtered": self.keyword_filtered,
                "success_rate": round(
                    total_downloaded / total_discovered * 100 if total_discovered > 0 else 0,
                    1
                )
            },
            "by_format": {
                "pdf": {
                    "discovered": self.files_discovered["pdf"],
                    "downloaded": self.files_downloaded["pdf"],
                    "failed": self.files_failed["pdf"],
                    "features_extracted": self.features_extracted["pdf"]
                },
                "csv": {
                    "discovered": self.files_discovered["csv"],
                    "downloaded": self.files_downloaded["csv"],
                    "failed": self.files_failed["csv"],
                    "features_extracted": self.features_extracted["csv"]
                },
                "xml": {
                    "discovered": self.files_discovered["xml"],
                    "downloaded": self.files_downloaded["xml"],
                    "failed": self.files_failed["xml"],
                    "features_extracted": self.features_extracted["xml"]
                },
                "txt": {
                    "discovered": self.files_discovered["txt"],
                    "downloaded": self.files_downloaded["txt"],
                    "failed": self.files_failed["txt"],
                    "features_extracted": self.features_extracted["txt"]
                }
            },
            "successes": self.successes,
            "errors": self.errors,
            "skips": self.skips
        }
    
    def save(self, output_path: Path):
        """Save report to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        
        logger.info(f"Saved crawl report to {output_path}")


class Crawler:
    """
    Main crawler orchestrator.
    """
    
    def __init__(self, config: CrawlerConfig):
        """
        Initialize crawler.
        
        Args:
            config: Crawler configuration
        """
        self.config = config
        self.report = CrawlReport()
        
        # Initialize components
        self.robots_checker = RobotsChecker(
            user_agent=config.user_agent,
            timeout=config.timeout_tuple
        )
        
        self.discovery = LinkDiscovery(
            allowed_domains=config.allow_domains,
            keyword_allow=config.keyword_allow,
            keyword_deny=config.keyword_deny,
            user_agent=config.user_agent,
            timeout=config.timeout_tuple,
            max_depth=config.max_depth,
            max_pages_per_domain=config.html_max_pages_per_domain
        )
        
        self.fetcher = PDFFetcher(
            user_agent=config.user_agent,
            timeout=config.timeout_tuple,
            max_retries=config.max_retries,
            retry_backoff=config.retry_backoff_factor,
            retry_status_codes=config.retry_status_codes,
            max_size_bytes=config.pdf_max_bytes
        )
        
        # Per-domain rate limiting
        self.last_request_time: Dict[str, float] = {}
    
    def run(self) -> CrawlReport:
        """
        Run the crawler.
        
        Returns:
            CrawlReport with results
        """
        logger.info("="*80)
        logger.info("STARTING CRAWLER")
        logger.info("="*80)
        logger.info(f"Allowed domains: {len(self.config.allow_domains)}")
        logger.info(f"Seed URLs: {len(self.config.seed_urls)}")
        logger.info(f"Max PDFs: {self.config.max_total_pdfs}")
        
        # Step 1: Discovery
        logger.info("\n--- STEP 1: DISCOVERY ---")
        discovered_urls = self.discovery.discover_from_seeds(self.config.seed_urls)
        
        self.report.html_pages_visited = len(self.discovery.visited)
        
        # Flatten discovered URLs
        all_pdfs = []
        for domain, urls in discovered_urls.items():
            self.report.domains_crawled.add(domain)
            for discovered_url in urls:
                all_pdfs.append(discovered_url)
        
        self.report.files_discovered["pdf"] = len(all_pdfs)
        
        logger.info(f"Discovered {len(all_pdfs)} PDFs across {len(discovered_urls)} domains")
        
        # Step 2: Fetch and Extract
        logger.info("\n--- STEP 2: FETCH & EXTRACT ---")
        
        pdfs_processed = 0
        
        for discovered_url in all_pdfs:
            # Check PDF limit
            if pdfs_processed >= self.config.max_total_pdfs:
                logger.info(f"Reached max PDF limit ({self.config.max_total_pdfs})")
                break
            
            # Check domain PDF limit
            domain_pdfs = sum(1 for s in self.report.successes if s['domain'] == discovered_url.url.split('/')[2])
            if domain_pdfs >= self.config.max_pdfs_per_domain:
                self.report.skips.append({
                    "url": discovered_url.url,
                    "reason": f"domain {discovered_url.url.split('/')[2]} reached PDF limit"
                })
                continue
            
            # Check robots.txt
            if self.config.respect_robots:
                can_fetch, reason = self.robots_checker.can_fetch(discovered_url.url)
                
                if not can_fetch:
                    self.report.robots_disallows += 1
                    self.report.skips.append({
                        "url": discovered_url.url,
                        "reason": reason
                    })
                    logger.debug(f"Skipping {discovered_url.url}: {reason}")
                    continue
            
            # Rate limiting
            self._rate_limit(discovered_url.url)
            
            # Fetch PDF
            pdf_filename = f"{discovered_url.url.split('/')[-1]}"
            temp_pdf_path = Path(self.config.output_pdfs_dir) / discovered_url.url.split('/')[2] / pdf_filename
            
            success, message, content = self.fetcher.fetch_pdf(
                discovered_url.url,
                temp_pdf_path if self.config.save_pdfs else None
            )
            
            if not success:
                self.report.files_failed["pdf"] += 1
                self.report.errors.append({
                    "url": discovered_url.url,
                    "error": message
                })
                logger.warning(f"Failed to fetch {discovered_url.url}: {message}")
                continue
            
            self.report.files_downloaded["pdf"] += 1
            pdfs_processed += 1
            
            # Extract features
            try:
                if content:
                    # Write to temp file for extraction
                    temp_path = Path("/tmp") / f"crawler_temp_{time.time()}.pdf"
                    temp_path.write_bytes(content)
                    
                    features = extract_safe_features(
                        temp_path,
                        max_pages=self.config.extract_features.get('max_pages_to_analyze', 3),
                        pii_redaction=self.config.extract_features.get('pii_redaction', True)
                    )
                    
                    # Add metadata
                    features['source_url'] = discovered_url.url
                    features['discovered_from'] = discovered_url.source_url
                    features['matched_keywords'] = discovered_url.matched_keywords
                    features['crawl_timestamp'] = datetime.now().isoformat()
                    
                    # Save features
                    domain = discovered_url.url.split('/')[2]
                    file_hash = features['file_hash'][:16]
                    features_path = Path(self.config.output_features_dir) / domain / f"{file_hash}.json"
                    
                    save_features(features, features_path)
                    
                    self.report.features_extracted["pdf"] += 1
                    self.report.successes.append({
                        "url": discovered_url.url,
                        "domain": domain,
                        "features_path": str(features_path),
                        "keywords": discovered_url.matched_keywords
                    })
                    
                    # Clean up temp file
                    temp_path.unlink(missing_ok=True)
                    
                    # Delete PDF if configured
                    if self.config.delete_after_extract and temp_pdf_path.exists():
                        temp_pdf_path.unlink()
                    
                    logger.info(f"✅ Processed {discovered_url.url}")
                
            except Exception as e:
                self.report.errors.append({
                    "url": discovered_url.url,
                    "error": f"Feature extraction failed: {e}"
                })
                logger.error(f"Failed to extract features from {discovered_url.url}: {e}")
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("CRAWLER COMPLETE")
        logger.info("="*80)
        logger.info(f"HTML pages visited: {self.report.html_pages_visited}")
        logger.info(f"Files discovered: {sum(self.report.files_discovered.values())}")
        logger.info(f"  PDFs: {self.report.files_discovered['pdf']}")
        logger.info(f"  CSVs: {self.report.files_discovered['csv']}")
        logger.info(f"  XMLs: {self.report.files_discovered['xml']}")
        logger.info(f"  TXTs: {self.report.files_discovered['txt']}")
        logger.info(f"Files downloaded: {sum(self.report.files_downloaded.values())}")
        logger.info(f"Features extracted: {sum(self.report.features_extracted.values())}")
        logger.info(f"Errors: {sum(self.report.files_failed.values())}")
        
        return self.report
    
    def _rate_limit(self, url: str):
        """
        Apply rate limiting per domain.
        
        Args:
            url: URL being fetched
        """
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc
        
        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            sleep_time = self.config.polite_delay_seconds - elapsed
            
            if sleep_time > 0:
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s for {domain}")
                time.sleep(sleep_time)
        
        self.last_request_time[domain] = time.time()
    
    def cleanup(self):
        """Cleanup resources."""
        self.discovery.close()
        self.fetcher.close()


def run_crawler(config: CrawlerConfig) -> CrawlReport:
    """
    Run crawler with given configuration.
    
    Args:
        config: Crawler configuration
        
    Returns:
        CrawlReport
    """
    crawler = Crawler(config)
    
    try:
        report = crawler.run()
        
        # Save report
        report.save(Path(config.output_report_path))
        
        return report
    
    finally:
        crawler.cleanup()

