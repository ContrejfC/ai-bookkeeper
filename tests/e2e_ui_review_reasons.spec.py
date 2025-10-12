"""
E2E Test: Review Page with Reason Filters (Wave-1 UI).

Tests:
- Reason filter chips work correctly
- Disabled Post button when not_auto_post_reason is present
- Tooltips show correct reason text with threshold
"""
import pytest
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)


class TestReviewReasons:
    """E2E tests for reason-aware review page."""
    
    def test_review_page_loads(self):
        """Test that review page loads successfully."""
        response = client.get("/review")
        assert response.status_code == 200
        assert b"Review Inbox" in response.content
    
    def test_reason_filter_chips_present(self):
        """Test that reason filter chips are displayed."""
        response = client.get("/review")
        assert response.status_code == 200
        
        # Check for reason chips
        assert b"Below Threshold" in response.content
        assert b"Cold Start" in response.content
        assert b"Imbalance" in response.content
        
    def test_reason_filter_applies_correctly(self):
        """Test that reason filter query param filters transactions."""
        # Filter by below_threshold
        response = client.get("/review?reason_filter=below_threshold")
        assert response.status_code == 200
        
        # Should only show transactions with that reason
        assert b"txn-001" in response.content  # Has below_threshold
        assert b"txn-002" not in response.content  # Has cold_start
    
    def test_post_button_disabled_for_blocked_reasons(self):
        """Test that Post button is disabled when not_auto_post_reason is present."""
        response = client.get("/review")
        assert response.status_code == 200
        
        # Check for disabled Post button with tooltip
        assert b'disabled' in response.content
        assert b"Cannot post:" in response.content
    
    def test_post_button_enabled_when_eligible(self):
        """Test that Post button is enabled when auto_post_eligible=true."""
        response = client.get("/review")
        assert response.status_code == 200
        
        # Should have at least one enabled Post button
        content = response.content.decode('utf-8')
        
        # Count disabled vs enabled Post buttons
        disabled_count = content.count('disabled')
        enabled_post_count = content.count('text-blue-600 hover:text-blue-900')
        
        assert enabled_post_count >= 1, "Should have at least one enabled Post button"
    
    def test_tooltip_shows_threshold_info(self):
        """Test that tooltips show calibrated_p and threshold_used."""
        response = client.get("/review")
        assert response.status_code == 200
        
        # Check for threshold info in tooltip
        assert b"p=" in response.content
        assert b"threshold=" in response.content
        assert b"0.86" in response.content  # calibrated_p for txn-001
        assert b"0.90" in response.content  # threshold_used
    
    def test_cold_start_tooltip_shows_label_count(self):
        """Test that cold-start tooltip shows label count."""
        response = client.get("/review?reason_filter=cold_start")
        assert response.status_code == 200
        
        # Check for label count in tooltip
        assert b"label(s)" in response.content or b"consistent labels" in response.content
    
    def test_multiple_filters_work_together(self):
        """Test that vendor and reason filters can be combined."""
        response = client.get("/review?reason_filter=below_threshold&vendor_filter=Office")
        assert response.status_code == 200
        
        # Should show Office Depot with below_threshold
        assert b"Office Depot" in response.content
        assert b"txn-001" in response.content
    
    def test_clear_filters_link_present(self):
        """Test that clear filters link appears when filter is active."""
        # With filter
        response = client.get("/review?reason_filter=below_threshold")
        assert response.status_code == 200
        assert b"Clear Filters" in response.content
        
        # Without filter
        response = client.get("/review")
        # May or may not have "Clear Filters" depending on implementation
    
    def test_explain_drawer_shows_decision_trace(self):
        """Test that explain drawer contains full decision trace."""
        response = client.get("/review")
        assert response.status_code == 200
        
        # Check for explain drawer structure
        assert b"Decision Explanation" in response.content
        assert b"Full Decision Trace" in response.content
    
    def test_review_performance_acceptable(self):
        """Test that review page renders in < 300ms (simulated)."""
        import time
        
        start = time.time()
        response = client.get("/review")
        duration_ms = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert duration_ms < 300, f"Review page took {duration_ms:.1f}ms (target <300ms)"


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

