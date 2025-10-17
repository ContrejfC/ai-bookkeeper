"""
Tests for API key authentication middleware.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.api.main import app
from app.services.api_key import APIKeyService


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_api_key_service():
    """Mock API key service."""
    return Mock(spec=APIKeyService)


def test_request_without_auth_header(client):
    """Request without Authorization header should proceed normally."""
    # Health check doesn't require auth
    response = client.get("/healthz")
    assert response.status_code == 200


def test_request_with_valid_api_key(client, mock_api_key_service):
    """Valid API key should set tenant_id in request state."""
    # Mock the API key verification
    mock_api_key_service.verify_token.return_value = "tenant_123"
    
    with patch("app.services.api_key.APIKeyService", return_value=mock_api_key_service):
        # Make request with Bearer token
        headers = {"Authorization": "Bearer ak_test_valid_token_abc123"}
        response = client.get("/actions", headers=headers)
        
        # Should succeed (actions endpoint doesn't require auth)
        assert response.status_code == 200
        
        # Verify service was called
        mock_api_key_service.verify_token.assert_called_once()


def test_request_with_invalid_api_key(client, mock_api_key_service):
    """Invalid API key should not block request (falls back to other auth)."""
    # Mock failed verification
    mock_api_key_service.verify_token.return_value = None
    
    with patch("app.services.api_key.APIKeyService", return_value=mock_api_key_service):
        headers = {"Authorization": "Bearer ak_test_invalid_token"}
        response = client.get("/actions", headers=headers)
        
        # Should still work (actions doesn't require auth)
        assert response.status_code == 200


def test_non_api_key_bearer_token(client):
    """Bearer token that doesn't start with ak_ should be ignored."""
    # Use a JWT-style token (not an API key)
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    response = client.get("/actions", headers=headers)
    
    # Should proceed (API key middleware ignores non-ak_ tokens)
    assert response.status_code == 200


def test_api_key_service_hash_determinism():
    """API key hashing should be deterministic."""
    token = "ak_test_example_token_123"
    
    hash1 = APIKeyService.hash_token(token)
    hash2 = APIKeyService.hash_token(token)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex


def test_api_key_service_hash_different_tokens():
    """Different tokens should produce different hashes."""
    token1 = "ak_test_token_1"
    token2 = "ak_test_token_2"
    
    hash1 = APIKeyService.hash_token(token1)
    hash2 = APIKeyService.hash_token(token2)
    
    assert hash1 != hash2


def test_api_key_generation_format():
    """Generated API keys should follow expected format."""
    token = APIKeyService.generate_token()
    
    # Should start with ak_test_ or ak_live_
    assert token.startswith("ak_test_") or token.startswith("ak_live_")
    
    # Should have reasonable length (at least 20 chars)
    assert len(token) > 20


def test_api_key_generation_uniqueness():
    """Generated API keys should be unique."""
    tokens = [APIKeyService.generate_token() for _ in range(100)]
    
    # All should be unique
    assert len(set(tokens)) == 100

