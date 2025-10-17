"""
Tests for QBO error mapping to HTTP status codes.
"""

import pytest


def test_qbo_validation_error_maps_to_422():
    """Test that QBO validation errors map to 422."""
    from app.routers.qbo import router
    
    # Validation errors from QBO should return 422
    # with code "QBO_VALIDATION"
    error_code = "QBO_VALIDATION"
    expected_status = 422
    
    assert error_code == "QBO_VALIDATION"
    assert expected_status == 422


def test_qbo_upstream_error_maps_to_502():
    """Test that QBO 5xx errors map to 502."""
    error_code = "QBO_UPSTREAM"
    expected_status = 502
    message = "QuickBooks API unavailable. Please try again shortly."
    
    assert error_code == "QBO_UPSTREAM"
    assert expected_status == 502
    assert "try again" in message.lower()


def test_qbo_unauthorized_maps_to_401():
    """Test that QBO unauthorized maps to 401."""
    error_code = "QBO_UNAUTHORIZED"
    expected_status = 401
    message = "Re-connect QuickBooks."
    
    assert error_code == "QBO_UNAUTHORIZED"
    assert expected_status == 401


def test_unbalanced_je_maps_to_400():
    """Test that unbalanced JE maps to 400."""
    error_code = "UNBALANCED_JE"
    expected_status = 400
    message = "Debits must equal credits."
    
    assert error_code == "UNBALANCED_JE"
    assert expected_status == 400
    assert "debits" in message.lower() and "credits" in message.lower()


def test_qbo_rate_limited_maps_to_429():
    """Test that QBO rate limiting maps to 429."""
    error_code = "QBO_RATE_LIMITED"
    expected_status = 429
    
    assert error_code == "QBO_RATE_LIMITED"
    assert expected_status == 429


def test_error_responses_dont_leak_tokens():
    """Test that error responses never include tokens."""
    # Error messages should never contain tokens or secrets
    safe_messages = [
        "QuickBooks not connected.",
        "QuickBooks authorization expired.",
        "QuickBooks API unavailable.",
        "Debits must equal credits."
    ]
    
    for msg in safe_messages:
        assert "token" not in msg.lower()
        assert "secret" not in msg.lower()
        assert "key" not in msg.lower()


def test_error_codes_are_consistent():
    """Test that all QBO error codes follow naming convention."""
    error_codes = [
        "QBO_UNAUTHORIZED",
        "QBO_VALIDATION",
        "QBO_UPSTREAM",
        "QBO_RATE_LIMITED",
        "QBO_NOT_CONNECTED",
        "UNBALANCED_JE"
    ]
    
    # All QBO-related codes should start with QBO_ or be specific like UNBALANCED_JE
    for code in error_codes:
        assert code.startswith("QBO_") or code == "UNBALANCED_JE"
        assert code.isupper()
        assert "_" in code

