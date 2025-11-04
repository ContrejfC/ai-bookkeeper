"""
Test Robots.txt and Allowlist Compliance
=========================================

Tests for robots.txt fetching and domain allowlist enforcement.
"""

import pytest
from unittest.mock import Mock, patch
from scripts.crawler.robots import RobotsChecker
from scripts.crawler.discovery import LinkDiscovery


class TestRobotsChecker:
    """Tests for RobotsChecker."""
    
    def test_robots_checker_initialization(self):
        """Test initialization."""
        checker = RobotsChecker("TestBot/1.0")
        assert checker.user_agent == "TestBot/1.0"
        assert checker._parsers == {}
        assert checker._failed_domains == set()
    
    def test_can_fetch_allowed(self):
        """Test fetching allowed URL."""
        checker = RobotsChecker("TestBot/1.0")
        
        with patch.object(checker, '_get_parser') as mock_parser:
            # Mock parser that allows all
            mock_rp = Mock()
            mock_rp.can_fetch.return_value = True
            mock_parser.return_value = mock_rp
            
            can_fetch, reason = checker.can_fetch("https://example.com/test.pdf")
            
            assert can_fetch == True
            assert "allowed" in reason.lower()
    
    def test_can_fetch_disallowed(self):
        """Test fetching disallowed URL."""
        checker = RobotsChecker("TestBot/1.0")
        
        with patch.object(checker, '_get_parser') as mock_parser:
            # Mock parser that disallows
            mock_rp = Mock()
            mock_rp.can_fetch.return_value = False
            mock_parser.return_value = mock_rp
            
            can_fetch, reason = checker.can_fetch("https://example.com/test.pdf")
            
            assert can_fetch == False
            assert "disallowed" in reason.lower()
    
    def test_can_fetch_robots_unavailable(self):
        """Test when robots.txt is unavailable."""
        checker = RobotsChecker("TestBot/1.0")
        
        with patch.object(checker, '_get_parser') as mock_parser:
            mock_parser.return_value = None
            
            can_fetch, reason = checker.can_fetch("https://example.com/test.pdf")
            
            # Should allow when robots.txt unavailable
            assert can_fetch == True
            assert "unavailable" in reason.lower()
    
    def test_clear_cache(self):
        """Test cache clearing."""
        checker = RobotsChecker("TestBot/1.0")
        checker._parsers['test.com'] = Mock()
        checker._failed_domains.add('test.com')
        
        checker.clear_cache()
        
        assert checker._parsers == {}
        assert checker._failed_domains == set()


class TestLinkDiscovery:
    """Tests for LinkDiscovery and allowlist enforcement."""
    
    def test_discovery_initialization(self):
        """Test initialization."""
        discovery = LinkDiscovery(
            allowed_domains=['chase.com', 'bankofamerica.com'],
            keyword_allow=['statement', 'sample'],
            keyword_deny=['privacy'],
            user_agent="TestBot/1.0",
            timeout=(10, 10)
        )
        
        assert 'chase.com' in discovery.allowed_domains
        assert 'bankofamerica.com' in discovery.allowed_domains
        assert 'statement' in discovery.keyword_allow
    
    def test_is_allowed_url_exact_domain(self):
        """Test URL allowed on exact domain match."""
        discovery = LinkDiscovery(
            allowed_domains=['chase.com'],
            keyword_allow=[],
            keyword_deny=[],
            user_agent="TestBot/1.0",
            timeout=(10, 10)
        )
        
        # Exact domain should be allowed
        assert discovery._is_allowed_url("https://chase.com/test.pdf") == True
        assert discovery._is_allowed_url("https://www.chase.com/test.pdf") == True
    
    def test_is_allowed_url_off_domain(self):
        """Test URL disallowed for off-domain."""
        discovery = LinkDiscovery(
            allowed_domains=['chase.com'],
            keyword_allow=[],
            keyword_deny=[],
            user_agent="TestBot/1.0",
            timeout=(10, 10)
        )
        
        # Off-domain should be disallowed
        assert discovery._is_allowed_url("https://evil.com/test.pdf") == False
        assert discovery._is_allowed_url("https://google.com/test.pdf") == False
    
    def test_check_keywords_allow(self):
        """Test keyword matching (allow)."""
        discovery = LinkDiscovery(
            allowed_domains=['chase.com'],
            keyword_allow=['sample statement', 'estatement'],
            keyword_deny=[],
            user_agent="TestBot/1.0",
            timeout=(10, 10)
        )
        
        # Should match allow keywords
        matched = discovery._check_keywords("https://chase.com/sample-statement.pdf")
        assert 'sample statement' in matched
    
    def test_check_keywords_deny(self):
        """Test keyword matching (deny)."""
        discovery = LinkDiscovery(
            allowed_domains=['chase.com'],
            keyword_allow=['statement'],
            keyword_deny=['privacy', 'terms'],
            user_agent="TestBot/1.0",
            timeout=(10, 10)
        )
        
        # Should reject if deny keyword present
        matched = discovery._check_keywords("https://chase.com/privacy-statement.pdf")
        assert matched == []  # Denied
    
    def test_normalize_url(self):
        """Test URL normalization."""
        discovery = LinkDiscovery(
            allowed_domains=['chase.com'],
            keyword_allow=[],
            keyword_deny=[],
            user_agent="TestBot/1.0",
            timeout=(10, 10)
        )
        
        # Remove fragment
        normalized = discovery._normalize_url("https://chase.com/test.pdf#section")
        assert '#section' not in normalized
        
        # Remove trailing slash
        normalized = discovery._normalize_url("https://chase.com/help/statements/")
        assert not normalized.endswith('/')
    
    def test_visited_tracking(self):
        """Test visited URL tracking."""
        discovery = LinkDiscovery(
            allowed_domains=['chase.com'],
            keyword_allow=['sample'],
            keyword_deny=[],
            user_agent="TestBot/1.0",
            timeout=(10, 10)
        )
        
        # Should track visited URLs
        assert len(discovery.visited) == 0
        
        # After visiting
        discovery.visited.add("https://chase.com/test1.html")
        discovery.visited.add("https://chase.com/test2.html")
        
        assert len(discovery.visited) == 2
        assert "https://chase.com/test1.html" in discovery.visited



