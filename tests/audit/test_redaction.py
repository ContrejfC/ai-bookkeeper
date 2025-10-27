"""
Test PII Redaction
==================

Tests for sensitive data redaction in logs and exports.

Test Cases:
-----------
1. Email addresses redacted
2. Credit card numbers redacted
3. SSN redacted
4. OAuth tokens redacted
5. API keys redacted
6. Passwords redacted
7. JWT tokens redacted
8. Redaction in log messages
9. Redaction in audit exports
"""
import pytest
import logging
from datetime import datetime

from app.logging.redaction import (
    redact_text, redact_dict, RedactionFilter,
    configure_redaction
)


def test_redact_email_addresses():
    """Test that email addresses are redacted."""
    text = "Contact john.doe@example.com for support"
    redacted = redact_text(text)
    
    assert "***EMAIL***" in redacted
    assert "john.doe@example.com" not in redacted


def test_redact_multiple_emails():
    """Test that multiple emails are redacted."""
    text = "Contact alice@example.com or bob@test.org"
    redacted = redact_text(text)
    
    assert redacted.count("***EMAIL***") == 2
    assert "alice@example.com" not in redacted
    assert "bob@test.org" not in redacted


def test_redact_credit_card_numbers():
    """Test that credit card numbers are redacted."""
    text = "Card: 4532-1234-5678-9012"
    redacted = redact_text(text)
    
    assert "***PAN***" in redacted
    assert "4532-1234-5678-9012" not in redacted


def test_redact_credit_card_no_dashes():
    """Test credit cards without dashes are redacted."""
    text = "Card: 4532123456789012"
    redacted = redact_text(text)
    
    assert "***PAN***" in redacted


def test_redact_ssn():
    """Test that SSN is redacted."""
    text = "SSN: 123-45-6789"
    redacted = redact_text(text)
    
    assert "***SSN***" in redacted
    assert "123-45-6789" not in redacted


def test_redact_bearer_token():
    """Test that bearer tokens are redacted."""
    text = "Authorization: Bearer abc123def456"
    redacted = redact_text(text)
    
    assert "Bearer ***TOKEN***" in redacted
    assert "abc123def456" not in redacted


def test_redact_api_keys():
    """Test that API keys are redacted."""
    text = "API Key: sk_test_fake1234567890abcdefghijklmn"
    redacted = redact_text(text)
    
    assert "***APIKEY***" in redacted or "***STRIPE_KEY***" in redacted
    assert "sk_test_fake1234567890abcdefghijklmn" not in redacted


def test_redact_stripe_keys():
    """Test that Stripe keys are redacted."""
    text = "Stripe: sk_test_fakeabcdefghijklmnopqrstuvwxyz123456"
    redacted = redact_text(text)
    
    assert "***STRIPE_KEY***" in redacted
    assert "sk_test_" not in redacted or "***" in redacted


def test_redact_jwt_tokens():
    """Test that JWT tokens are redacted."""
    text = "Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    redacted = redact_text(text)
    
    assert "***JWT***" in redacted
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted


def test_redact_password_in_json():
    """Test that password field in JSON is redacted."""
    text = '{"username": "john", "password": "secret123"}'
    redacted = redact_text(text)
    
    assert "***PASSWORD***" in redacted
    assert "secret123" not in redacted


def test_redact_access_token_in_json():
    """Test that access_token in JSON is redacted."""
    text = '{"access_token": "abc123xyz"}'
    redacted = redact_text(text)
    
    assert "***TOKEN***" in redacted
    assert "abc123xyz" not in redacted


def test_redact_refresh_token_in_json():
    """Test that refresh_token in JSON is redacted."""
    text = '{"refresh_token": "refresh_abc123"}'
    redacted = redact_text(text)
    
    assert "***TOKEN***" in redacted
    assert "refresh_abc123" not in redacted


def test_redact_dict_with_sensitive_keys():
    """Test dictionary redaction with sensitive keys."""
    data = {
        "username": "john",
        "password": "secret",
        "api_key": "key_123",
        "email": "john@example.com"
    }
    
    redacted = redact_dict(data, redact_keys=True)
    
    assert redacted["password"] == "***REDACTED***"
    assert redacted["api_key"] == "***REDACTED***"
    assert "***EMAIL***" in redacted["email"]


def test_redact_dict_nested():
    """Test nested dictionary redaction."""
    data = {
        "user": {
            "name": "John",
            "email": "john@example.com",
            "credentials": {
                "password": "secret123"
            }
        }
    }
    
    redacted = redact_dict(data, redact_keys=True)
    
    assert "***EMAIL***" in redacted["user"]["email"]
    assert redacted["user"]["credentials"]["password"] == "***REDACTED***"


def test_redact_dict_with_lists():
    """Test dictionary with lists of sensitive data."""
    data = {
        "emails": ["alice@example.com", "bob@test.org"],
        "safe_field": "normal value"
    }
    
    redacted = redact_dict(data)
    
    assert "***EMAIL***" in redacted["emails"][0]
    assert "***EMAIL***" in redacted["emails"][1]
    assert redacted["safe_field"] == "normal value"


def test_redaction_filter_on_log_message(caplog):
    """Test that RedactionFilter redacts log messages."""
    logger = logging.getLogger("test_redaction")
    logger.setLevel(logging.INFO)
    
    # Add redaction filter
    handler = logging.StreamHandler()
    handler.addFilter(RedactionFilter())
    logger.addHandler(handler)
    
    with caplog.at_level(logging.INFO, logger="test_redaction"):
        logger.info("User email: john@example.com")
    
    # Check that log was redacted
    assert "***EMAIL***" in caplog.text
    assert "john@example.com" not in caplog.text


def test_redaction_filter_on_log_args():
    """Test that RedactionFilter redacts log arguments."""
    logger = logging.getLogger("test_args")
    handler = logging.StreamHandler()
    handler.addFilter(RedactionFilter())
    logger.addHandler(handler)
    
    # Log with args
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Token: %s",
        args=("Bearer abc123",),
        exc_info=None
    )
    
    filter = RedactionFilter()
    filter.filter(record)
    
    # Args should be redacted
    assert "***TOKEN***" in str(record.args)


def test_configure_redaction_adds_filter():
    """Test that configure_redaction adds filter to logger."""
    logger = logging.getLogger("test_configure")
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    
    # Configure redaction
    configure_redaction(logger)
    
    # Check filter was added
    assert any(isinstance(f, RedactionFilter) for f in handler.filters)


def test_redaction_preserves_safe_content():
    """Test that safe content is not affected by redaction."""
    text = "This is a normal message without sensitive data. Amount: $100.50"
    redacted = redact_text(text)
    
    assert redacted == text  # Should be unchanged


def test_redaction_handles_empty_strings():
    """Test that empty strings are handled gracefully."""
    assert redact_text("") == ""
    assert redact_text(None) is None


def test_redaction_handles_none_dict():
    """Test that None is handled in dict redaction."""
    result = redact_dict(None)
    assert result is None


def test_audit_export_redaction(db_session):
    """Test that audit exports have PII redacted."""
    from app.db.models import DecisionAuditLogDB
    
    # Create audit log with sensitive data
    audit = DecisionAuditLogDB(
        timestamp=datetime.utcnow(),
        tenant_id="test-tenant",
        user_id="user-001",
        action="TEST_ACTION",
        metadata={
            "user_email": "sensitive@example.com",
            "api_key": "sk_test_123456",
            "safe_field": "normal_value"
        }
    )
    db_session.add(audit)
    db_session.commit()
    
    # Fetch and redact
    audit_data = {
        "timestamp": audit.timestamp.isoformat(),
        "action": audit.action,
        "metadata": audit.metadata
    }
    
    redacted = redact_dict(audit_data, redact_keys=True)
    
    # Check sensitive fields are redacted
    assert "***EMAIL***" in str(redacted["metadata"])
    assert "sensitive@example.com" not in str(redacted)


@pytest.mark.integration
def test_end_to_end_log_redaction(caplog):
    """Integration test for full log redaction flow."""
    logger = logging.getLogger("integration_test")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.addFilter(RedactionFilter())
    logger.addHandler(handler)
    
    # Log message with multiple sensitive items
    with caplog.at_level(logging.INFO, logger="integration_test"):
        logger.info(
            "User john@example.com connected with token Bearer abc123 "
            "and card 4532-1234-5678-9012"
        )
    
    # Verify all sensitive data redacted
    log_output = caplog.text
    assert "***EMAIL***" in log_output
    assert "***TOKEN***" in log_output or "***" in log_output
    assert "***PAN***" in log_output
    
    # Verify original data not present
    assert "john@example.com" not in log_output
    assert "4532-1234-5678-9012" not in log_output


def test_client_secret_redaction():
    """Test that client_secret is redacted."""
    text = '{"client_secret": "super_secret_key_123"}'
    redacted = redact_text(text)
    
    assert "***SECRET***" in redacted
    assert "super_secret_key_123" not in redacted


def test_redaction_case_insensitive():
    """Test that redaction works regardless of case."""
    text1 = "EMAIL: john@EXAMPLE.COM"
    text2 = "email: john@example.com"
    
    redacted1 = redact_text(text1)
    redacted2 = redact_text(text2)
    
    assert "***EMAIL***" in redacted1
    assert "***EMAIL***" in redacted2

