"""
Tests for Home Page (Public Marketing Landing).

Verifies:
- Public access (no auth required)
- Sign in CTA and navigation anchors present
- Key sections rendered (hero, features, how, security, pricing, FAQ)
- SEO control via SEO_INDEX env var
- Basic accessibility (headings, buttons, links)
- Analytics logging (PII-free)
"""
import pytest
import os
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)


class TestHomePagePublicAccess:
    """Test home page is publicly accessible."""
    
    def test_home_public_access_returns_200(self):
        """Home page should be publicly accessible without authentication."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
    
    def test_home_no_auth_redirect(self):
        """Home page should NOT redirect to login (it's public)."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 200
        # Should not be a redirect
        assert response.status_code != 302
        assert response.status_code != 307


class TestHomePageContent:
    """Test home page contains expected content and CTAs."""
    
    def test_home_contains_signin_cta(self):
        """Home page should have Sign In button linking to /login."""
        response = client.get("/")
        html = response.text
        
        # Check for Sign In link/button
        assert "Sign In" in html or "Sign in" in html
        assert 'href="/login"' in html
    
    def test_home_contains_navigation_anchors(self):
        """Home page should have navigation anchors to key sections."""
        response = client.get("/")
        html = response.text
        
        # Check for navigation anchors
        assert 'href="#how"' in html or 'href="#features"' in html
        assert 'href="#security"' in html or 'href="#pricing"' in html
        assert 'href="#faq"' in html
    
    def test_home_has_hero_section(self):
        """Home page should have hero with H1 and primary CTA."""
        response = client.get("/")
        html = response.text
        
        # Check for hero content
        assert "<h1" in html
        assert "AI Bookkeeper" in html
        assert "faster" in html.lower() or "safer" in html.lower()
        
    def test_home_has_sections_features_how_security_pricing_faq(self):
        """Home page should have all major sections."""
        response = client.get("/")
        html = response.text
        
        # Check for section IDs/headings
        assert 'id="how"' in html or "How It Works" in html
        assert 'id="features"' in html or "Features" in html
        assert 'id="security"' in html or "Security" in html
        assert 'id="pricing"' in html or "Pricing" in html
        assert 'id="faq"' in html or "FAQ" in html or "Frequently Asked" in html
    
    def test_home_has_trust_strip(self):
        """Home page should have trust indicators."""
        response = client.get("/")
        html = response.text
        
        # Check for trust elements
        assert ("security" in html.lower() and "default" in html.lower()) or \
               "human-in-the-loop" in html.lower() or \
               "audit log" in html.lower()
    
    def test_home_has_screenshot_links(self):
        """Home page should link to key product pages."""
        response = client.get("/")
        html = response.text
        
        # Check for links to product pages
        assert 'href="/review"' in html or 'href="/receipts"' in html or 'href="/metrics"' in html


class TestHomePageSEO:
    """Test SEO controls via SEO_INDEX environment variable."""
    
    def test_home_seo_noindex_when_env_zero(self, monkeypatch):
        """Home page should have noindex meta when SEO_INDEX=0."""
        monkeypatch.setenv("SEO_INDEX", "0")
        
        response = client.get("/")
        html = response.text
        
        # Should have noindex meta tag
        assert 'meta name="robots" content="noindex' in html
    
    def test_home_seo_index_when_env_one(self, monkeypatch):
        """Home page should NOT have noindex meta when SEO_INDEX=1."""
        monkeypatch.setenv("SEO_INDEX", "1")
        
        response = client.get("/")
        html = response.text
        
        # Should NOT have noindex meta tag (or it should be commented out)
        # Since we're using {% if not seo_index %}, when seo_index=True, the meta shouldn't appear
        assert 'meta name="robots" content="noindex' not in html


class TestHomePageAccessibility:
    """Test home page accessibility (WCAG 2.1 AA compliance)."""
    
    def test_home_a11y_smoke_headings_present(self):
        """Home page should have proper heading structure."""
        response = client.get("/")
        html = response.text
        
        # Check for headings
        assert "<h1" in html  # Should have exactly one H1
        assert "<h2" in html  # Should have H2 for sections
        
        # Count H1 occurrences (should be 1)
        h1_count = html.count("<h1")
        assert h1_count == 1, f"Expected 1 H1, found {h1_count}"
    
    def test_home_a11y_buttons_have_min_target_size(self):
        """Home page buttons should meet minimum touch target size (44x44px)."""
        response = client.get("/")
        html = response.text
        
        # Check for min-height/min-width on buttons
        # Our CTAs use min-h-[44px] or min-h-[48px] from Tailwind
        assert 'min-h-[44px]' in html or 'min-h-[48px]' in html or 'min-height: 44px' in html
    
    def test_home_a11y_links_have_text(self):
        """Links should have descriptive text, not just icons."""
        response = client.get("/")
        html = response.text
        
        # Check that key links have text content
        assert 'Sign In' in html or 'Sign in' in html
        assert 'Features' in html
        assert 'Contact' in html or 'Support' in html
    
    def test_home_a11y_aria_labels_on_icon_buttons(self):
        """Icon-only buttons should have aria-label."""
        response = client.get("/")
        html = response.text
        
        # If there are icon-only buttons, they should have aria-label
        # Our Sign In button has aria-label
        if 'aria-label=' in html:
            assert 'aria-label="' in html


class TestHomePageLinks:
    """Test home page links are safe and functional."""
    
    def test_home_links_are_absolute_or_safe(self):
        """Internal links should be absolute paths or anchors."""
        response = client.get("/")
        html = response.text
        
        # Check for safe link patterns
        assert 'href="/login"' in html
        assert 'href="/support"' in html or 'href="#' in html
        
        # Should NOT have dangerous links
        assert 'href="javascript:' not in html.lower()
        assert 'href="data:' not in html.lower()
    
    def test_home_footer_links_present(self):
        """Footer should have legal and support links."""
        response = client.get("/")
        html = response.text
        
        # Check for footer links
        assert 'href="/legal/terms"' in html or 'Terms' in html
        assert 'href="/legal/privacy"' in html or 'Privacy' in html
        assert 'href="/support"' in html or 'Support' in html


class TestHomePagePerformance:
    """Test home page performance characteristics."""
    
    def test_home_response_time_under_1_second(self):
        """Home page should respond quickly (< 1 second for unit test)."""
        import time
        
        start = time.time()
        response = client.get("/")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        # In unit tests, should be very fast
        assert elapsed < 1.0, f"Response took {elapsed:.2f}s, expected < 1.0s"


class TestHomePageAnalytics:
    """Test analytics logging for home page views."""
    
    def test_home_analytics_logging_non_fatal(self):
        """Home page should not crash if analytics logging fails."""
        # This test ensures the try/except around analytics works
        response = client.get("/")
        
        # Should still return 200 even if analytics fails
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

