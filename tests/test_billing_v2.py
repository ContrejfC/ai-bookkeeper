"""
Tests for enhanced billing API with ad-ready pricing.

Run with: pytest tests/test_billing_v2.py -v
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.api.main import app

client = TestClient(app)


class TestCSVCleaner:
    """Tests for CSV cleaner tool"""
    
    def test_csv_clean_preview_limits_to_50_rows(self):
        """Test that CSV preview returns max 50 rows"""
        # Create a CSV with 100 rows
        csv_content = "date,payee,amount\n"
        for i in range(100):
            csv_content += f"2024-01-{(i%28)+1:02d},Vendor {i},100.00\n"
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        
        response = client.post("/api/tools/csv-clean?preview=true", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["preview_rows"]) == 50
        assert data["total_rows"] == 100
        assert "Preview of first 50 rows" in data["message"]
    
    def test_csv_clean_rejects_invalid_mime_and_large_files(self):
        """Test that invalid files are rejected"""
        # Test non-CSV file
        files = {"file": ("test.txt", "not a csv", "text/plain")}
        response = client.post("/api/tools/csv-clean", files=files)
        assert response.status_code == 400
        assert "must be a CSV" in response.json()["detail"]
        
        # Test file too large (>10 MB)
        large_content = "date,payee,amount\n" * (2 * 1024 * 1024)  # >10MB
        files = {"file": ("large.csv", large_content, "text/csv")}
        response = client.post("/api/tools/csv-clean", files=files)
        assert response.status_code == 400
        assert "too large" in response.json()["detail"]


class TestCheckout:
    """Tests for checkout endpoint"""
    
    @patch('app.api.billing_v2.stripe')
    def test_checkout_creates_session_for_each_plan_and_addons(self, mock_stripe):
        """Test checkout session creation for different plans"""
        mock_stripe.checkout.Session.create.return_value = Mock(
            id="cs_test_123",
            url="https://checkout.stripe.com/test"
        )
        
        # Test Starter plan
        response = client.post("/api/billing/checkout", json={
            "plan": "starter",
            "term": "monthly",
            "addons": []
        })
        assert response.status_code == 200
        assert "url" in response.json()
        
        # Test Team plan with addon
        response = client.post("/api/billing/checkout", json={
            "plan": "team",
            "term": "annual",
            "addons": ["sso"]
        })
        assert response.status_code == 200
        
        # Test Enterprise returns contact message
        response = client.post("/api/billing/checkout", json={
            "plan": "enterprise",
            "term": "monthly",
            "addons": []
        })
        assert response.status_code == 200
        assert "message" in response.json()
        assert "contact sales" in response.json()["message"].lower()


class TestEntitlements:
    """Tests for entitlement enforcement"""
    
    @patch('app.services.usage_metering.UsageMeteringService')
    def test_entitlements_block_export_when_over_quota(self, mock_service):
        """Test that export is blocked when quota exceeded"""
        # Mock quota check failure
        mock_service.return_value.check_quota.return_value = (
            False,
            {"error": "quota_exceeded", "http_status": 402}
        )
        
        # Try to export (would require actual auth setup)
        # This is a simplified test - in practice would need full auth flow
        pass  # TODO: Implement with proper auth fixtures


class TestUsageMetering:
    """Tests for usage metering"""
    
    @patch('app.services.usage_metering.stripe')
    def test_usage_metering_records_overage_at_month_end(self, mock_stripe):
        """Test that overage is correctly calculated and posted to Stripe"""
        # This would require database fixtures
        # Simplified test structure
        pass  # TODO: Implement with database fixtures


class TestQBOExport:
    """Tests for QBO export idempotency"""
    
    def test_qbo_export_requires_idempotency_key(self):
        """Test that QBO export requires Idempotency-Key header"""
        response = client.post("/api/post/rollback", json={
            "journal_entry_id": "je_123",
            "reason": "Test rollback"
        })
        # Should fail without Idempotency-Key header
        assert response.status_code == 422  # Missing required header


# Integration tests would go here
# These require actual Stripe test mode configuration

class TestStripeWebhook:
    """Tests for Stripe webhook handling"""
    
    @patch('app.api.billing_v2.stripe.Webhook.construct_event')
    def test_webhook_handles_checkout_completed(self, mock_construct):
        """Test webhook handling for checkout.session.completed"""
        mock_construct.return_value = {
            "type": "checkout.session.completed",
            "id": "evt_test",
            "data": {
                "object": {
                    "id": "cs_test",
                    "subscription": "sub_test",
                    "customer": "cus_test",
                    "metadata": {"tenant_id": "tenant_123"}
                }
            }
        }
        
        response = client.post(
            "/api/billing/webhook",
            headers={"Stripe-Signature": "test_signature"},
            json={}
        )
        
        # Would check database for created subscription
        # Requires database fixtures
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

