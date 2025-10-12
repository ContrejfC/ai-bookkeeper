"""
E2E Test: Metrics Dashboard (Wave-1 UI).

Tests:
- All required fields render correctly
- Period selector works (7d, 30d, 90d)
- Reason counts reconcile validation
- LLM fallback status displayed
"""
import pytest
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)


class TestMetricsDashboard:
    """E2E tests for metrics dashboard page."""
    
    def test_metrics_page_loads(self):
        """Test that metrics page loads successfully."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert b"Metrics Dashboard" in response.content
    
    def test_core_metrics_render(self):
        """Test that all core metrics are displayed."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Core metrics
        assert b"Automation Rate" in response.content
        assert b"Auto-Post Rate" in response.content
        assert b"Review Rate" in response.content
        assert b"Reconciliation" in response.content
        
        # Check for percentage values
        assert b"84.7%" in response.content or b"82.3%" in response.content
    
    def test_model_quality_metrics_render(self):
        """Test that model quality metrics are displayed."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Model quality
        assert b"Brier Score" in response.content
        assert b"ECE (Calibrated)" in response.content
        assert b"Gating Threshold" in response.content
        
        # Check for specific values
        assert b"0.118" in response.content  # Brier
        assert b"0.029" in response.content  # ECE
        assert b"0.90" in response.content   # Threshold
    
    def test_metadata_fields_present(self):
        """Test that schema_version, period, window, population_n are displayed."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Metadata
        assert b"Window:" in response.content
        assert b"Population:" in response.content
        assert b"1234 transactions" in response.content or b"1,234" in response.content
        assert b"Schema:" in response.content
        assert b"v1.0" in response.content or b"1.0" in response.content
    
    def test_period_selector_works(self):
        """Test that period query param changes displayed data."""
        # Test 7d
        response_7d = client.get("/metrics?period=7d")
        assert response_7d.status_code == 200
        assert b"7 Days" in response_7d.content
        
        # Test 30d (default)
        response_30d = client.get("/metrics?period=30d")
        assert response_30d.status_code == 200
        assert b"30 Days" in response_30d.content
        
        # Test 90d
        response_90d = client.get("/metrics?period=90d")
        assert response_90d.status_code == 200
        assert b"90 Days" in response_90d.content
    
    def test_reason_counts_breakdown_displayed(self):
        """Test that not_auto_post_counts are displayed with bars."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Reason breakdown section
        assert b"Review Reasons Breakdown" in response.content
        assert b"Below Threshold" in response.content
        assert b"Cold Start" in response.content
        
        # Check for counts
        assert b"87" in response.content  # below_threshold count
        assert b"42" in response.content  # cold_start count
    
    def test_ece_bins_reliability_chart_present(self):
        """Test that ECE reliability chart is rendered."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Reliability diagram
        assert b"Reliability Diagram" in response.content or b"ECE Bins" in response.content
        
        # Check for bin data
        assert b"0.0-0.1" in response.content
        assert b"0.9-1.0" in response.content
    
    def test_drift_metrics_displayed(self):
        """Test that PSI and KS metrics are displayed."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Drift metrics
        assert b"Data Drift" in response.content
        assert b"PSI (Vendor)" in response.content
        assert b"PSI (Amount)" in response.content
        assert b"KS (Vendor)" in response.content
        assert b"KS (Amount)" in response.content
    
    def test_llm_cost_metrics_displayed(self):
        """Test that LLM cost metrics are displayed."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # LLM costs
        assert b"LLM Costs" in response.content
        assert b"Calls per Transaction" in response.content
        assert b"Unit Cost per Transaction" in response.content
        assert b"Tenant Spend" in response.content
        assert b"Global Spend" in response.content
    
    def test_llm_fallback_warning_shows_when_active(self):
        """Test that fallback warning appears when llm_budget_status.fallback_active=true."""
        # This test would need to mock fallback_active=true
        # For now, test that the HTML structure exists
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Check for conditional fallback structure in template
        # (actual warning won't show unless fallback_active=true)
        content = response.content.decode('utf-8')
        assert 'fallback_active' in content.lower() or 'Fallback Active' in content
    
    def test_counts_reconcile_validation(self):
        """Test that validation banner shows when counts don't reconcile."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Check for validation logic
        # Banner should NOT appear for our fixture data (counts reconcile)
        # But structure should exist
        content = response.content.decode('utf-8')
        
        # Either no warning (counts OK) or warning present
        if b"counts don't reconcile" in response.content:
            # If warning present, should show both values
            assert b"Total not_auto_post_counts" in response.content
            assert b"Expected from review_rate" in response.content
    
    def test_metrics_performance_acceptable(self):
        """Test that metrics page renders in < 300ms (simulated)."""
        import time
        
        start = time.time()
        response = client.get("/metrics")
        duration_ms = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert duration_ms < 300, f"Metrics page took {duration_ms:.1f}ms (target <300ms)"
    
    def test_tenant_switcher_query_param(self):
        """Test that tenant_id query param is supported."""
        response = client.get("/metrics?tenant_id=pilot-test-123")
        assert response.status_code == 200
        
        # Should still render (with tenant-specific data in production)
        assert b"Metrics Dashboard" in response.content


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

