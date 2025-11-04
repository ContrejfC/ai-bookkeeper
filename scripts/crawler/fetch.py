"""
Safe PDF Fetching
==================

Download PDFs with safety checks (size, type, malware resistance).
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

import httpx
from httpx import Limits

logger = logging.getLogger(__name__)


class PDFFetcher:
    """
    Safely fetch PDFs with size/type validation and rate limiting.
    """
    
    def __init__(
        self,
        user_agent: str,
        timeout: tuple,
        max_retries: int = 3,
        retry_backoff: float = 0.5,
        retry_status_codes: list = None,
        max_size_bytes: int = 10 * 1024 * 1024
    ):
        """
        Initialize PDF fetcher.
        
        Args:
            user_agent: User agent string
            timeout: (connect, read) timeout tuple
            max_retries: Maximum number of retries
            retry_backoff: Backoff factor for retries
            retry_status_codes: Status codes to retry on
            max_size_bytes: Maximum PDF size in bytes
        """
        self.user_agent = user_agent
        self.timeout_tuple = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.retry_status_codes = retry_status_codes or [429, 500, 502, 503, 504]
        self.max_size_bytes = max_size_bytes
        
        # Create httpx client with retries
        self.client = httpx.Client(
            headers={"User-Agent": user_agent},
            timeout=httpx.Timeout(timeout[0]),
            follow_redirects=True,
            limits=Limits(max_connections=10, max_keepalive_connections=5)
        )
    
    def fetch_pdf(
        self,
        url: str,
        output_path: Optional[Path] = None
    ) -> Tuple[bool, str, Optional[bytes]]:
        """
        Fetch PDF with safety checks.
        
        Args:
            url: URL to fetch
            output_path: Optional path to save PDF to disk
            
        Returns:
            Tuple of (success: bool, message: str, content: Optional[bytes])
        """
        try:
            # Step 1: HEAD request to check content type and size
            can_proceed, reason = self._check_head(url)
            
            if not can_proceed:
                return False, reason, None
            
            # Step 2: GET request to download
            logger.info(f"Downloading PDF: {url}")
            
            attempt = 0
            last_error = None
            
            while attempt <= self.max_retries:
                try:
                    response = self.client.get(url)
                    
                    if response.status_code == 200:
                        content = response.content
                        
                        # Verify size
                        if len(content) > self.max_size_bytes:
                            return False, f"PDF too large: {len(content)} bytes (max: {self.max_size_bytes})", None
                        
                        # Verify it's actually a PDF (magic bytes)
                        if not self._is_pdf(content):
                            return False, "Content is not a valid PDF (magic bytes check failed)", None
                        
                        # Save if requested
                        if output_path:
                            output_path.parent.mkdir(parents=True, exist_ok=True)
                            output_path.write_bytes(content)
                            logger.info(f"Saved PDF to {output_path}")
                        
                        # Compute hash
                        sha256 = hashlib.sha256(content).hexdigest()
                        
                        return True, f"Success (SHA256: {sha256[:16]}...)", content
                    
                    elif response.status_code in self.retry_status_codes:
                        last_error = f"HTTP {response.status_code}"
                        attempt += 1
                        if attempt <= self.max_retries:
                            import time
                            time.sleep(self.retry_backoff * (2 ** (attempt - 1)))
                            logger.warning(f"Retrying ({attempt}/{self.max_retries}): {url}")
                        continue
                    
                    else:
                        return False, f"HTTP {response.status_code}", None
                
                except httpx.TimeoutException:
                    last_error = "Timeout"
                    attempt += 1
                    if attempt <= self.max_retries:
                        logger.warning(f"Timeout, retrying ({attempt}/{self.max_retries}): {url}")
                    continue
                
                except Exception as e:
                    last_error = str(e)
                    break
            
            return False, f"Failed after {self.max_retries} retries: {last_error}", None
        
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return False, f"Error: {e}", None
    
    def _check_head(self, url: str) -> Tuple[bool, str]:
        """
        Perform HEAD request to check content type and size.
        
        Args:
            url: URL to check
            
        Returns:
            Tuple of (can_proceed: bool, reason: str)
        """
        try:
            response = self.client.head(url)
            
            if response.status_code != 200:
                return False, f"HEAD request failed: HTTP {response.status_code}"
            
            # Check content type
            content_type = response.headers.get("Content-Type", "").lower()
            
            if "pdf" not in content_type and "application/octet-stream" not in content_type:
                return False, f"Not a PDF: Content-Type is '{content_type}'"
            
            # Check content length
            content_length = response.headers.get("Content-Length")
            
            if content_length:
                size = int(content_length)
                
                if size > self.max_size_bytes:
                    return False, f"PDF too large: {size} bytes (max: {self.max_size_bytes})"
                
                if size < 100:  # Suspiciously small
                    return False, f"PDF too small: {size} bytes (likely not a real PDF)"
            
            return True, "HEAD check passed"
        
        except Exception as e:
            logger.warning(f"HEAD check failed for {url}: {e}, proceeding anyway")
            return True, "HEAD check failed (proceeding)"
    
    def _is_pdf(self, content: bytes) -> bool:
        """
        Check if content is a valid PDF by magic bytes.
        
        Args:
            content: File content
            
        Returns:
            True if content starts with PDF magic bytes
        """
        if len(content) < 5:
            return False
        
        # PDF magic bytes: %PDF-
        return content[:5] == b'%PDF-'
    
    def close(self):
        """Close HTTP client."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Example usage
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python fetch.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    
    fetcher = PDFFetcher(
        user_agent="AI-Bookkeeper-ResearchBot/1.0",
        timeout=(10, 10),
        max_size_bytes=10 * 1024 * 1024
    )
    
    success, message, content = fetcher.fetch_pdf(url)
    
    print(f"\nURL: {url}")
    print(f"Success: {success}")
    print(f"Message: {message}")
    
    if content:
        print(f"Size: {len(content)} bytes")
    
    fetcher.close()

