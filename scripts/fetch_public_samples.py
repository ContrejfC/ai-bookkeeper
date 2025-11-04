#!/usr/bin/env python3
"""
Public Sample Fetcher
=====================

Download publicly available bank statement samples for template development.

Safety Features:
- Allowlist-only domains
- Size limits (10MB max)
- robots.txt compliance
- PII redaction in extracted features
- PDFs not committed to git

Usage:
    python scripts/fetch_public_samples.py --config configs/public_samples.yaml
    python scripts/fetch_public_samples.py --config configs/public_samples.yaml --delete-after-extract
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.ingestion.tools.sample_feature_extractor import extract_features

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class PublicSampleFetcher:
    """
    Fetch public bank statement samples with safety limits.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize fetcher with configuration.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config = self._load_config(config_path)
        self.allow_domains = set(self.config.get('allow_domains', []))
        self.samples = self.config.get('samples', [])
        self.fetch_settings = self.config.get('fetch_settings', {})
        self.extraction_settings = self.config.get('extraction_settings', {})
        self.output_settings = self.config.get('output', {})
        
        # Create output directories
        self._create_directories()
        
        # Session for requests
        self.session = requests.Session()
        self.session.headers['User-Agent'] = self.fetch_settings.get(
            'user_agent',
            'BankStatementTemplateBuilder/1.0'
        )
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load YAML configuration."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)
    
    def _create_directories(self):
        """Create output directories."""
        for key in ['features_dir', 'metadata_dir', 'pdf_download_dir']:
            dir_path = Path(self.output_settings.get(key, ''))
            if dir_path:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {dir_path}")
    
    def _check_domain_allowed(self, url: str) -> bool:
        """
        Check if URL domain is in allowlist.
        
        Args:
            url: URL to check
        
        Returns:
            True if domain is allowed
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check if domain or parent domain is in allowlist
        for allowed in self.allow_domains:
            if domain == allowed or domain.endswith(f'.{allowed}'):
                return True
        
        logger.warning(f"Domain not in allowlist: {domain}")
        return False
    
    def _check_robots_txt(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt.
        
        Args:
            url: URL to check
        
        Returns:
            True if allowed or robots.txt not found
        """
        if not self.fetch_settings.get('respect_robots_txt', True):
            return True
        
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            user_agent = self.session.headers.get('User-Agent', '*')
            allowed = rp.can_fetch(user_agent, url)
            
            if not allowed:
                logger.warning(f"URL blocked by robots.txt: {url}")
            
            return allowed
        
        except Exception as e:
            logger.debug(f"Could not check robots.txt: {e}")
            # If robots.txt check fails, allow (fail-open for development)
            return True
    
    def _head_check(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Perform HEAD request to check content type and size.
        
        Args:
            url: URL to check
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            response = self.session.head(
                url,
                timeout=(
                    self.fetch_settings.get('connect_timeout', 10),
                    self.fetch_settings.get('read_timeout', 10)
                ),
                allow_redirects=True
            )
            
            # Check status
            if response.status_code != 200:
                return False, f"HEAD request returned {response.status_code}"
            
            # Check content type
            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/pdf' not in content_type:
                return False, f"Content-Type is {content_type}, expected application/pdf"
            
            # Check size
            content_length = response.headers.get('Content-Length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                max_size = self.fetch_settings.get('max_size_mb', 10)
                if size_mb > max_size:
                    return False, f"File size {size_mb:.1f}MB exceeds limit of {max_size}MB"
            
            return True, None
        
        except requests.exceptions.RequestException as e:
            return False, f"HEAD request failed: {e}"
    
    def _download_file(self, url: str, output_path: Path) -> bool:
        """
        Download file with retries.
        
        Args:
            url: URL to download
            output_path: Path to save file
        
        Returns:
            True if successful
        """
        max_retries = self.fetch_settings.get('max_retries', 3)
        retry_statuses = set(self.fetch_settings.get('retry_status_codes', [429, 500, 502, 503, 504]))
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    url,
                    timeout=(
                        self.fetch_settings.get('connect_timeout', 10),
                        self.fetch_settings.get('read_timeout', 10)
                    ),
                    stream=True
                )
                
                # Check if we should retry
                if response.status_code in retry_statuses and attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Status {response.status_code}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                # Download file
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Downloaded: {output_path.name}")
                return True
            
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Download failed: {e}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Download failed after {max_retries} attempts: {e}")
                    return False
        
        return False
    
    def _compute_sha256(self, file_path: Path) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _save_metadata(self, sample: Dict[str, Any], file_path: Path, sha256: str):
        """Save metadata JSON for downloaded sample."""
        metadata_dir = Path(self.output_settings.get('metadata_dir', 'tests/fixtures/pdf/metadata'))
        metadata_path = metadata_dir / f"{sample['name']}_metadata.json"
        
        metadata = {
            'name': sample['name'],
            'url': sample['url'],
            'bank': sample.get('bank', 'Unknown'),
            'account_type': sample.get('account_type', 'Unknown'),
            'sha256': sha256,
            'download_timestamp': time.time(),
            'file_size_bytes': file_path.stat().st_size,
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.debug(f"Saved metadata: {metadata_path}")
    
    def fetch_sample(self, sample: Dict[str, Any], delete_after: bool = False) -> bool:
        """
        Fetch a single sample.
        
        Args:
            sample: Sample configuration
            delete_after: Delete PDF after feature extraction
        
        Returns:
            True if successful
        """
        name = sample.get('name', 'unknown')
        url = sample.get('url', '')
        
        logger.info(f"Processing sample: {name}")
        
        # Check if enabled
        if not sample.get('enabled', True):
            logger.info(f"Sample disabled: {name}")
            return False
        
        # Validate URL
        if not url:
            logger.error(f"No URL provided for {name}")
            return False
        
        # Check domain allowlist
        if not self._check_domain_allowed(url):
            logger.error(f"Domain not allowed for {name}: {url}")
            return False
        
        # Check robots.txt
        if not self._check_robots_txt(url):
            logger.error(f"Blocked by robots.txt: {name}")
            return False
        
        # HEAD check
        is_valid, error_msg = self._head_check(url)
        if not is_valid:
            logger.error(f"HEAD check failed for {name}: {error_msg}")
            return False
        
        # Download
        pdf_dir = Path(self.output_settings.get('pdf_download_dir', 'tests/fixtures/pdf/_public'))
        pdf_path = pdf_dir / f"{name}.pdf"
        
        if not self._download_file(url, pdf_path):
            return False
        
        # Compute hash
        sha256 = self._compute_sha256(pdf_path)
        
        # Save metadata
        self._save_metadata(sample, pdf_path, sha256)
        
        # Extract features
        try:
            features_dir = Path(self.output_settings.get('features_dir', 'tests/fixtures/pdf/features'))
            features_path = features_dir / f"{name}_features.json"
            
            features = extract_features(
                str(pdf_path),
                redact_pii=self.extraction_settings.get('redact_pii', True)
            )
            
            with open(features_path, 'w') as f:
                json.dump(features, f, indent=2)
            
            logger.info(f"Extracted features: {features_path.name}")
        
        except Exception as e:
            logger.error(f"Feature extraction failed for {name}: {e}")
            # Continue even if extraction fails
        
        # Delete PDF if requested
        if delete_after:
            try:
                pdf_path.unlink()
                logger.info(f"Deleted PDF: {pdf_path.name}")
            except Exception as e:
                logger.warning(f"Could not delete PDF: {e}")
        
        return True
    
    def fetch_all(self, delete_after: bool = False) -> Dict[str, Any]:
        """
        Fetch all configured samples.
        
        Args:
            delete_after: Delete PDFs after feature extraction
        
        Returns:
            Summary dictionary
        """
        logger.info(f"Fetching {len(self.samples)} samples...")
        
        results = {
            'total': len(self.samples),
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'samples': []
        }
        
        for sample in self.samples:
            name = sample.get('name', 'unknown')
            
            try:
                success = self.fetch_sample(sample, delete_after=delete_after)
                
                if success:
                    results['success'] += 1
                    results['samples'].append({
                        'name': name,
                        'status': 'success'
                    })
                else:
                    results['skipped'] += 1
                    results['samples'].append({
                        'name': name,
                        'status': 'skipped'
                    })
            
            except Exception as e:
                logger.error(f"Unexpected error for {name}: {e}")
                results['failed'] += 1
                results['samples'].append({
                    'name': name,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Fetch public bank statement samples for template development'
    )
    parser.add_argument(
        '--config',
        default='configs/public_samples.yaml',
        help='Path to configuration YAML'
    )
    parser.add_argument(
        '--delete-after-extract',
        action='store_true',
        help='Delete PDFs after feature extraction'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run fetcher
    fetcher = PublicSampleFetcher(args.config)
    results = fetcher.fetch_all(delete_after=args.delete_after_extract)
    
    # Print summary
    print("\n" + "=" * 60)
    print("FETCH SUMMARY")
    print("=" * 60)
    print(f"Total samples: {results['total']}")
    print(f"Success: {results['success']}")
    print(f"Skipped: {results['skipped']}")
    print(f"Failed: {results['failed']}")
    print("=" * 60 + "\n")
    
    # Exit with appropriate code
    if results['failed'] > 0:
        sys.exit(1)
    elif results['success'] == 0:
        sys.exit(2)  # No samples fetched
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()



