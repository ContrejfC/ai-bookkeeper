"""
Tests for /actions discovery endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from app.api.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def test_actions_discovery_without_tenant(client):
    """Actions discovery without authentication should return defaults."""
    response = client.get("/actions")
    
    assert response.status_code == 200
    
    data = response.json()
    
    # Check structure
    assert "version" in data
    assert "links" in data
    assert "paywall_md" in data
    assert "cap" in data
    assert "connected" in data
    assert "entitlement" in data
    
    # Check links
    links = data["links"]
    assert "openapi" in links
    assert "billing_portal" in links
    assert "connect_quickbooks" in links
    assert "qbo_status" in links
    assert "post_commit" in links
    
    # Without tenant, should show disconnected/no plan
    assert data["connected"]["qbo"] == False
    assert data["entitlement"]["active"] == False
    assert data["entitlement"]["plan"] == "none"
    
    # Should include cap
    assert data["cap"]["free_daily_analyze"] == 50
    
    # Should include paywall text
    assert "To post to QuickBooks" in data["paywall_md"]


def test_actions_discovery_with_connected_qbo(client):
    """Actions discovery with QBO connected should reflect status."""
    # Mock QBO service to return connected
    mock_qbo_status = {"connected": True, "realm_id": "123456"}
    
    with patch("app.services.qbo.QBOService") as mock_qbo_service_class:
        mock_qbo_service = Mock()
        mock_qbo_service.get_connection_status.return_value = mock_qbo_status
        mock_qbo_service_class.return_value = mock_qbo_service
        
        # Mock tenant_id in request state
        with patch("app.services.api_key.APIKeyService") as mock_api_key_service_class:
            mock_api_key_service = Mock()
            mock_api_key_service.verify_token.return_value = "tenant_123"
            mock_api_key_service_class.return_value = mock_api_key_service
            
            # Mock billing service
            with patch("app.services.billing.BillingService") as mock_billing_service_class:
                mock_billing_service = Mock()
                mock_billing_service.get_billing_status.return_value = {
                    "active": False,
                    "plan": "none"
                }
                mock_billing_service_class.return_value = mock_billing_service
                
                headers = {"Authorization": "Bearer ak_test_token_123"}
                response = client.get("/actions", headers=headers)
                
                assert response.status_code == 200
                data = response.json()
                
                # Should show QBO connected
                assert data["connected"]["qbo"] == True


def test_actions_discovery_with_active_plan(client):
    """Actions discovery with active plan should show entitlement."""
    # Mock billing service to return active plan
    mock_billing_status = {
        "active": True,
        "plan": "starter"
    }
    
    with patch("app.services.billing.BillingService") as mock_billing_service_class:
        mock_billing_service = Mock()
        mock_billing_service.get_billing_status.return_value = mock_billing_status
        mock_billing_service_class.return_value = mock_billing_service
        
        # Mock QBO service
        with patch("app.services.qbo.QBOService") as mock_qbo_service_class:
            mock_qbo_service = Mock()
            mock_qbo_service.get_connection_status.return_value = {"connected": False}
            mock_qbo_service_class.return_value = mock_qbo_service
            
            # Mock tenant_id
            with patch("app.services.api_key.APIKeyService") as mock_api_key_service_class:
                mock_api_key_service = Mock()
                mock_api_key_service.verify_token.return_value = "tenant_123"
                mock_api_key_service_class.return_value = mock_api_key_service
                
                headers = {"Authorization": "Bearer ak_test_token_123"}
                response = client.get("/actions", headers=headers)
                
                assert response.status_code == 200
                data = response.json()
                
                # Should show active plan
                assert data["entitlement"]["active"] == True
                assert data["entitlement"]["plan"] == "starter"


def test_actions_discovery_links_format(client):
    """Actions discovery links should have correct format."""
    response = client.get("/actions")
    
    assert response.status_code == 200
    data = response.json()
    
    links = data["links"]
    
    # All links should be strings starting with /
    for key, value in links.items():
        assert isinstance(value, str)
        assert value.startswith("/"), f"Link {key} should start with /: {value}"


def test_actions_discovery_version_format(client):
    """Actions discovery version should be a string."""
    response = client.get("/actions")
    
    assert response.status_code == 200
    data = response.json()
    
    version = data["version"]
    assert isinstance(version, str)
    assert len(version) > 0


def test_actions_discovery_handles_service_errors(client):
    """Actions discovery should handle service errors gracefully."""
    # Mock QBO service to raise error
    with patch("app.services.qbo.QBOService") as mock_qbo_service_class:
        mock_qbo_service = Mock()
        mock_qbo_service.get_connection_status.side_effect = Exception("QBO service error")
        mock_qbo_service_class.return_value = mock_qbo_service
        
        # Mock billing service to raise error
        with patch("app.services.billing.BillingService") as mock_billing_service_class:
            mock_billing_service = Mock()
            mock_billing_service.get_billing_status.side_effect = Exception("Billing service error")
            mock_billing_service_class.return_value = mock_billing_service
            
            # Mock tenant_id
            with patch("app.services.api_key.APIKeyService") as mock_api_key_service_class:
                mock_api_key_service = Mock()
                mock_api_key_service.verify_token.return_value = "tenant_123"
                mock_api_key_service_class.return_value = mock_api_key_service
                
                headers = {"Authorization": "Bearer ak_test_token_123"}
                response = client.get("/actions", headers=headers)
                
                # Should still return 200 with defaults
                assert response.status_code == 200
                data = response.json()
                
                # Should fall back to disconnected/no plan
                assert data["connected"]["qbo"] == False
                assert data["entitlement"]["active"] == False
                assert data["entitlement"]["plan"] == "none"

