"""
Tests for CSRF Protection (P1.1 Security Patch).
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.api.main import app
from app.auth.csrf import generate_csrf_token, verify_csrf_token, get_csrf_token


client = TestClient(app)


def test_post_without_csrf_rejected():
    """
    Verify POST without CSRF token is rejected with 403.
    """
    # Login to get session
    login_response = client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "magic_token": "dev"
    })
    
    assert login_response.status_code == 200
    cookies = login_response.cookies
    
    # Try POST without CSRF header (should fail)
    response = client.post(
        "/api/tenants/pilot-acme-corp-082aceed/settings",
        json={"autopost_threshold": 0.95},
        cookies=cookies
        # No X-CSRF-Token header!
    )
    
    assert response.status_code == 403
    assert "CSRF" in response.json()["detail"]
    
    print("✅ POST without CSRF rejected")


def test_post_with_valid_csrf_succeeds():
    """
    Verify POST with valid CSRF token succeeds.
    """
    # Login to get session and CSRF token
    login_response = client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "magic_token": "dev"
    })
    
    assert login_response.status_code == 200
    cookies = login_response.cookies
    csrf_token = cookies.get("csrf_token")
    
    assert csrf_token is not None, "CSRF token should be set in cookie"
    
    # POST with valid CSRF header (should succeed)
    response = client.post(
        "/api/tenants/pilot-acme-corp-082aceed/settings",
        json={"autopost_threshold": 0.95},
        cookies=cookies,
        headers={"X-CSRF-Token": csrf_token}
    )
    
    assert response.status_code == 200
    print("✅ POST with valid CSRF succeeds")


def test_csrf_rotates_daily():
    """
    Verify CSRF token expires after 24 hours.
    """
    session_id = "test-session-123"
    
    # Generate token
    token1 = generate_csrf_token(session_id=session_id)
    
    # Get token immediately (should be valid)
    token_cached = get_csrf_token(session_id)
    assert token_cached == token1
    
    # Simulate expiry by manipulating cache
    from app.auth.csrf import _csrf_tokens
    old_token, old_expiry = _csrf_tokens[session_id]
    expired_time = datetime.utcnow() - timedelta(days=1, hours=1)
    _csrf_tokens[session_id] = (old_token, expired_time)
    
    # Try to get expired token (should return None)
    token_expired = get_csrf_token(session_id)
    assert token_expired is None
    
    print("✅ CSRF rotates daily (expires after 24h)")


def test_verify_csrf_token():
    """Test CSRF token verification logic."""
    token = generate_csrf_token()
    
    # Valid match
    assert verify_csrf_token(token, token) == True
    
    # Invalid match
    assert verify_csrf_token(token, "wrong-token") == False
    
    # Empty tokens
    assert verify_csrf_token("", token) == False
    assert verify_csrf_token(token, "") == False
    assert verify_csrf_token(None, token) == False
    
    print("✅ CSRF verification logic correct")


def test_csrf_exempt_routes():
    """Verify exempt routes don't require CSRF."""
    # Login endpoint should work without CSRF (exempt)
    response = client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "magic_token": "dev"
    })
    
    assert response.status_code == 200
    print("✅ Exempt routes work without CSRF")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

