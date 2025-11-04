"""
Robots.txt Compliance
=====================

Fetch, parse, and enforce robots.txt rules per domain.
"""

import logging
from typing import Dict, Optional
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import httpx

logger = logging.getLogger(__name__)


class RobotsChecker:
    """
    Manages robots.txt compliance across multiple domains.
    """
    
    def __init__(self, user_agent: str, timeout: tuple = (10, 10)):
        """
        Initialize robots checker.
        
        Args:
            user_agent: User agent string to identify as
            timeout: (connect, read) timeout tuple
        """
        self.user_agent = user_agent
        self.timeout = timeout
        self._parsers: Dict[str, Optional[RobotFileParser]] = {}
        self._failed_domains: set = set()
    
    def can_fetch(self, url: str) -> tuple[bool, str]:
        """
        Check if URL can be fetched according to robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            Tuple of (can_fetch: bool, reason: str)
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # If we already failed to fetch robots.txt for this domain, allow
        if domain in self._failed_domains:
            return True, "robots.txt unavailable (allowing)"
        
        # Get or fetch parser for this domain
        parser = self._get_parser(domain)
        
        if parser is None:
            # Failed to fetch robots.txt, allow but record
            self._failed_domains.add(domain)
            return True, "robots.txt unavailable (allowing)"
        
        # Check if URL is allowed
        can_fetch = parser.can_fetch(self.user_agent, url)
        
        if can_fetch:
            return True, "allowed by robots.txt"
        else:
            return False, f"disallowed by robots.txt for {self.user_agent}"
    
    def _get_parser(self, domain: str) -> Optional[RobotFileParser]:
        """
        Get RobotFileParser for domain (cached).
        
        Args:
            domain: Domain to get parser for
            
        Returns:
            RobotFileParser or None if fetch failed
        """
        if domain in self._parsers:
            return self._parsers[domain]
        
        # Fetch and parse robots.txt
        robots_url = f"https://{domain}/robots.txt"
        
        try:
            logger.info(f"Fetching robots.txt from {robots_url}")
            
            with httpx.Client(
                timeout=httpx.Timeout(self.timeout[0]),
                follow_redirects=True
            ) as client:
                response = client.get(robots_url)
                
                if response.status_code == 200:
                    # Parse robots.txt
                    parser = RobotFileParser()
                    parser.parse(response.text.splitlines())
                    
                    self._parsers[domain] = parser
                    logger.info(f"Successfully parsed robots.txt for {domain}")
                    return parser
                    
                elif response.status_code == 404:
                    # No robots.txt = allow all
                    logger.info(f"No robots.txt found for {domain} (404) - allowing all")
                    parser = RobotFileParser()
                    parser.parse([])  # Empty = allow all
                    self._parsers[domain] = parser
                    return parser
                    
                else:
                    logger.warning(f"Failed to fetch robots.txt from {domain}: HTTP {response.status_code}")
                    self._parsers[domain] = None
                    return None
                    
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching robots.txt from {domain}")
            self._parsers[domain] = None
            return None
            
        except Exception as e:
            logger.error(f"Error fetching robots.txt from {domain}: {e}")
            self._parsers[domain] = None
            return None
    
    def get_crawl_delay(self, domain: str) -> Optional[float]:
        """
        Get crawl delay for domain from robots.txt.
        
        Args:
            domain: Domain to check
            
        Returns:
            Crawl delay in seconds, or None if not specified
        """
        parser = self._get_parser(domain)
        
        if parser is None:
            return None
        
        try:
            delay = parser.crawl_delay(self.user_agent)
            return float(delay) if delay else None
        except:
            return None
    
    def clear_cache(self):
        """Clear cached robots.txt parsers."""
        self._parsers.clear()
        self._failed_domains.clear()


# Example usage
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    checker = RobotsChecker("AI-Bookkeeper-ResearchBot/1.0")
    
    test_urls = [
        "https://www.chase.com/content/dam/chase-ux/documents/personal/sample-statement.pdf",
        "https://www.bankofamerica.com/online-banking/estatements.go",
        "https://www.wellsfargo.com/help/online-banking/statements/",
    ]
    
    for url in test_urls:
        can_fetch, reason = checker.can_fetch(url)
        print(f"\n{url}")
        print(f"  Can fetch: {can_fetch}")
        print(f"  Reason: {reason}")
        
        domain = urlparse(url).netloc
        delay = checker.get_crawl_delay(domain)
        if delay:
            print(f"  Crawl delay: {delay}s")

