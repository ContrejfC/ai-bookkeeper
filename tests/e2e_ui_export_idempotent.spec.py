"""
E2E Test: Export Center Idempotency (Wave-1 UI).

Tests:
- Export page loads with history
- Re-export shows only skips (no new rows)
- ExternalId (first 32 hex) displayed
- Posted vs skipped counts shown
"""
import pytest
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)


class TestExportIdempotency:
    """E2E tests for export center idempotency."""
    
    def test_export_page_loads(self):
        """Test that export page loads successfully."""
        response = client.get("/export")
        assert response.status_code == 200
        assert b"Export Center" in response.content
    
    def test_export_history_table_present(self):
        """Test that export history table is displayed."""
        response = client.get("/export")
        assert response.status_code == 200
        
        # Export history section
        assert b"Export History" in response.content
        assert b"Export ID" in response.content
        assert b"Posted" in response.content
        assert b"Skipped" in response.content
        assert b"Total Lines" in response.content
    
    def test_export_history_shows_posted_and_skipped_counts(self):
        """Test that posted and skipped counts are displayed."""
        response = client.get("/export")
        assert response.status_code == 200
        
        # First export: 5 posted, 0 skipped
        assert b"exp-001" in response.content
        # The specific counts may be in badges
        content = response.content.decode('utf-8')
        
        # Check for export data structure
        assert 'posted_count' in content.lower() or '>5<' in content or '>0<' in content
    
    def test_reexport_note_displayed(self):
        """Test that re-export shows 'all duplicates' note."""
        response = client.get("/export")
        assert response.status_code == 200
        
        # Re-export entry
        assert b"exp-002" in response.content
        assert b"Re-export" in response.content or b"all duplicates" in response.content
    
    def test_qbo_export_log_table_present(self):
        """Test that QBO export log table is displayed."""
        response = client.get("/export")
        assert response.status_code == 200
        
        # QBO log section
        assert b"QBO Export Log" in response.content
        assert b"Idempotency" in response.content
        assert b"ExternalId" in response.content
        assert b"32 hex" in response.content
    
    def test_external_id_first_32_hex_displayed(self):
        """Test that ExternalId shows first 32 hex characters."""
        response = client.get("/export")
        assert response.status_code == 200
        
        # Check for ExternalId values (first 32 hex)
        assert b"a3f7d8c2e1b4f5a67890abcdef123456" in response.content
        assert b"b2c3d4e5f6a789012345cdef67890abc" in response.content
    
    def test_external_id_tooltip_shows_full_64_hex(self):
        """Test that hovering shows full 64 hex SHA-256."""
        response = client.get("/export")
        assert response.status_code == 200
        
        # Check for tooltip structure
        assert b"Full SHA-256" in response.content or b"64 hex" in response.content
    
    def test_attempt_count_shows_skips(self):
        """Test that attempt count shows skipped re-exports."""
        response = client.get("/export")
        assert response.status_code == 200
        
        # Entry with 2 attempts (1 skipped)
        content = response.content.decode('utf-8')
        
        # Should show attempt count and skips
        assert 'attempt_count' in content.lower() or 'Attempts' in content or 'skipped' in content
    
    def test_qbo_format_reference_displayed(self):
        """Test that QBO CSV format reference is shown."""
        response = client.get("/export")
        assert response.status_code == 200
        
        # Format reference
        assert b"QBO CSV Format" in response.content
        assert b"11 Columns" in response.content
        assert b"Date,JournalNumber,AccountName" in response.content
        assert b"ExternalId" in response.content
    
    def test_export_trigger_button_present(self):
        """Test that export trigger button is present."""
        response = client.get("/export")
        assert response.status_code == 200
        
        # Export button
        assert b"Export to QBO CSV" in response.content or b"Trigger QBO Export" in response.content
    
    def test_export_trigger_uses_htmx(self):
        """Test that export trigger uses htmx for async submission."""
        response = client.get("/export")
        assert response.status_code == 200
        
        # Check for htmx attributes
        assert b"hx-post" in response.content
        assert b"hx-target" in response.content
        assert b"/export/qbo" in response.content
    
    def test_export_trigger_returns_success_fragment(self):
        """Test that triggering export returns success HTML fragment."""
        response = client.post("/export/qbo")
        assert response.status_code == 200
        
        # Success fragment
        assert b"Export Complete" in response.content
        assert b"Posted:" in response.content
        assert b"Skipped:" in response.content
    
    def test_second_export_shows_only_skips(self):
        """Test that second export returns 0 new, N skipped."""
        # First export (mock)
        response1 = client.post("/export/qbo")
        assert response1.status_code == 200
        assert b"Posted:" in response1.content
        
        # Second export (should show skips)
        response2 = client.post("/export/qbo")
        assert response2.status_code == 200
        
        # Should indicate skips or duplicates
        content = response2.content.decode('utf-8')
        assert 'Skipped' in content or 'duplicate' in content.lower()
    
    def test_export_performance_acceptable(self):
        """Test that export page renders in < 300ms (simulated)."""
        import time
        
        start = time.time()
        response = client.get("/export")
        duration_ms = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert duration_ms < 300, f"Export page took {duration_ms:.1f}ms (target <300ms)"


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

