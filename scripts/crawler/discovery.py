"""
Discovery Engine
================

BFS crawler for discovering PDF links from bank website help pages.
"""

import re
import logging
from typing import Set, List, Dict, Optional, Tuple
from urllib.parse import urlparse, urljoin, urlunparse
from collections import deque
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredURL:
    """A discovered URL with metadata."""
    url: str
    source_url: str
    depth: int
    url_type: str  # 'pdf' or 'html'
    matched_keywords: List[str]


class LinkDiscovery:
    """
    Discovers PDF links from HTML pages using BFS.
    """
    
    def __init__(
        self,
        allowed_domains: List[str],
        keyword_allow: List[str],
        keyword_deny: List[str],
        user_agent: str,
        timeout: tuple,
        max_depth: int = 3,
        max_pages_per_domain: int = 50
    ):
        """
        Initialize discovery engine.
        
        Args:
            allowed_domains: List of allowed domains
            keyword_allow: List of keywords to match for relevance
            keyword_deny: List of keywords to exclude
            user_agent: User agent string
            timeout: (connect, read) timeout tuple
            max_depth: Maximum crawl depth
            max_pages_per_domain: Maximum pages to visit per domain
        """
        self.allowed_domains = set(allowed_domains)
        self.keyword_allow = [kw.lower() for kw in keyword_allow]
        self.keyword_deny = [kw.lower() for kw in keyword_deny]
        self.user_agent = user_agent
        self.timeout = timeout
        self.max_depth = max_depth
        self.max_pages_per_domain = max_pages_per_domain
        
        # Tracking
        self.visited: Set[str] = set()
        self.pages_per_domain: Dict[str, int] = {}
        
        # HTTP client
        self.client = httpx.Client(
            headers={"User-Agent": user_agent},
            timeout=httpx.Timeout(timeout[0]),
            follow_redirects=True
        )
    
    def _domain_matches_allowed(self, url_domain: str) -> bool:
        """
        Check if a domain matches any allowed domain, handling subdomains.
        
        Examples:
            www.chase.com matches chase.com
            www.bankofamerica.com matches bankofamerica.com
            subdomain.example.com matches example.com
        """
        for allowed_domain in self.allowed_domains:
            # Exact match
            if url_domain == allowed_domain:
                return True
            # Subdomain match (www.example.com matches example.com)
            if url_domain.endswith('.' + allowed_domain):
                return True
        return False
    
    def discover_from_seeds(self, seed_urls: List[str]) -> Dict[str, List[DiscoveredURL]]:
        """
        Discover PDFs starting from seed URLs using BFS.
        
        Args:
            seed_urls: List of seed URLs to start from
            
        Returns:
            Dict mapping domain to list of discovered URLs
        """
        results: Dict[str, List[DiscoveredURL]] = {}
        
        # Initialize BFS queue
        queue = deque()
        
        for seed_url in seed_urls:
            parsed = urlparse(seed_url)
            domain = parsed.netloc
            
            if not self._domain_matches_allowed(domain):
                logger.warning(f"Skipping seed URL from non-allowed domain: {seed_url}")
                continue
            
            queue.append((seed_url, seed_url, 0))  # (url, source, depth)
        
        logger.info(f"Starting BFS from {len(queue)} seed URLs")
        
        # BFS
        while queue:
            url, source_url, depth = queue.popleft()
            
            # Skip if already visited
            if url in self.visited:
                continue
            
            # Check depth limit
            if depth > self.max_depth:
                logger.debug(f"Skipping {url} - exceeds max depth {self.max_depth}")
                continue
            
            # Parse URL
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Check domain limit
            if self.pages_per_domain.get(domain, 0) >= self.max_pages_per_domain:
                logger.debug(f"Skipping {url} - domain {domain} hit page limit")
                continue
            
            # Mark as visited
            self.visited.add(url)
            self.pages_per_domain[domain] = self.pages_per_domain.get(domain, 0) + 1
            
            # Determine URL type
            if url.lower().endswith('.pdf'):
                url_type = 'pdf'
            else:
                url_type = 'html'
            
            # Check keywords
            matched_keywords = self._check_keywords(url)
            is_relevant = bool(matched_keywords)
            
            # If PDF, add to results
            if url_type == 'pdf' and is_relevant:
                if domain not in results:
                    results[domain] = []
                
                results[domain].append(DiscoveredURL(
                    url=url,
                    source_url=source_url,
                    depth=depth,
                    url_type='pdf',
                    matched_keywords=matched_keywords
                ))
                
                logger.info(f"Found PDF: {url} (keywords: {matched_keywords})")
                continue  # Don't fetch PDFs for link extraction
            
            # If HTML, fetch and extract links
            if url_type == 'html':
                try:
                    logger.info(f"Fetching HTML: {url} (depth {depth})")
                    
                    response = self.client.get(url)
                    
                    if response.status_code != 200:
                        logger.warning(f"Failed to fetch {url}: HTTP {response.status_code}")
                        continue
                    
                    # Parse HTML and extract links
                    links = self._extract_links(url, response.text)
                    
                    logger.info(f"Found {len(links)} links on {url}")
                    
                    # Add links to queue
                    for link in links:
                        if link not in self.visited:
                            queue.append((link, url, depth + 1))
                
                except httpx.TimeoutException:
                    logger.warning(f"Timeout fetching {url}")
                except Exception as e:
                    logger.error(f"Error fetching {url}: {e}")
        
        # Summary
        total_pdfs = sum(len(urls) for urls in results.values())
        logger.info(f"Discovery complete: {total_pdfs} PDFs found across {len(results)} domains")
        
        return results
    
    def _extract_links(self, base_url: str, html: str) -> List[str]:
        """
        Extract links from HTML.
        
        Args:
            base_url: Base URL for resolving relative links
            html: HTML content
            
        Returns:
            List of absolute URLs
        """
        links = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            for anchor in soup.find_all('a', href=True):
                href = anchor['href']
                
                # Resolve relative URLs
                absolute_url = urljoin(base_url, href)
                
                # Normalize URL
                absolute_url = self._normalize_url(absolute_url)
                
                # Check if allowed
                if self._is_allowed_url(absolute_url):
                    links.append(absolute_url)
        
        except Exception as e:
            logger.error(f"Error parsing HTML from {base_url}: {e}")
        
        return links
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL (remove fragments, trailing slashes, etc.).
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
        """
        parsed = urlparse(url)
        
        # Remove fragment
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            ''  # No fragment
        ))
        
        # Remove trailing slash (except for domain root)
        if normalized.endswith('/') and normalized.count('/') > 3:
            normalized = normalized[:-1]
        
        return normalized
    
    def _is_allowed_url(self, url: str) -> bool:
        """
        Check if URL is allowed based on domain allowlist.
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Check if domain is allowed (handles subdomains)
        return self._domain_matches_allowed(domain)
    
    def _check_keywords(self, url: str) -> List[str]:
        """
        Check if URL matches any allowed keywords and doesn't match deny keywords.
        
        Args:
            url: URL to check
            
        Returns:
            List of matched keywords (empty if no match or denied)
        """
        url_lower = url.lower()
        
        # Check deny keywords first
        for deny_keyword in self.keyword_deny:
            if deny_keyword in url_lower:
                logger.debug(f"URL {url} matches deny keyword: {deny_keyword}")
                return []
        
        # Check allow keywords
        matched = []
        for allow_keyword in self.keyword_allow:
            if allow_keyword in url_lower:
                matched.append(allow_keyword)
        
        return matched
    
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
    
    discovery = LinkDiscovery(
        allowed_domains=['wellsfargo.com', 'chase.com'],
        keyword_allow=['sample statement', 'estatement'],
        keyword_deny=['privacy', 'terms'],
        user_agent='AI-Bookkeeper-ResearchBot/1.0',
        timeout=(10, 10),
        max_depth=2,
        max_pages_per_domain=10
    )
    
    seed_urls = [
        'https://www.wellsfargo.com/help/online-banking/statements/',
    ]
    
    results = discovery.discover_from_seeds(seed_urls)
    
    print(f"\n{'='*80}")
    print("DISCOVERY RESULTS")
    print(f"{'='*80}\n")
    
    for domain, urls in results.items():
        print(f"\n{domain}: {len(urls)} PDFs")
        for discovered_url in urls[:5]:  # Show first 5
            print(f"  - {discovered_url.url}")
            print(f"    Keywords: {discovered_url.matched_keywords}")
            print(f"    Depth: {discovered_url.depth}")
    
    discovery.close()

