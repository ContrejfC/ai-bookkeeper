"""
Tests for Centralized Logging with PII Redaction (SOC 2 Min Controls).

Tests:
- PII patterns are redacted from log strings
- PII keys are removed from structured data
- JSON formatting works correctly
- Audit events log without PII
"""
import json
import logging
from io import StringIO

import pytest

from app.ops.logging import (
    redact_pii_from_string,
    redact_pii_from_dict,
    PiiRedactingFormatter,
    log_audit_event,
    get_logger
)


def test_redact_email_from_string():
    """Test email addresses are redacted."""
    text = "User john.doe@example.com logged in"
    redacted = redact_pii_from_string(text)
    
    assert "[EMAIL_REDACTED]" in redacted
    assert "john.doe@example.com" not in redacted


def test_redact_ssn_from_string():
    """Test SSN is redacted."""
    text = "SSN: 123-45-6789 for verification"
    redacted = redact_pii_from_string(text)
    
    assert "[SSN_REDACTED]" in redacted
    assert "123-45-6789" not in redacted


def test_redact_card_number_from_string():
    """Test credit card numbers are redacted."""
    text = "Card 4532-1234-5678-9010 charged"
    redacted = redact_pii_from_string(text)
    
    assert "[CARD_REDACTED]" in redacted
    assert "4532" not in redacted


def test_redact_phone_from_string():
    """Test phone numbers are redacted."""
    text = "Contact: 555-123-4567"
    redacted = redact_pii_from_string(text)
    
    assert "[PHONE_REDACTED]" in redacted
    assert "555-123-4567" not in redacted


def test_redact_secrets_from_string():
    """Test API keys and secrets are redacted."""
    test_cases = [
        ('api_key="sk_live_12345"', "[REDACTED]"),
        ("password=mysecretpass", "[REDACTED]"),
        ("Authorization: Bearer token123", "[REDACTED]"),
    ]
    
    for text, expected_marker in test_cases:
        redacted = redact_pii_from_string(text)
        assert expected_marker in redacted
        # Check that actual secret values are removed
        assert "sk_live_12345" not in redacted
        assert "mysecretpass" not in redacted
        assert "token123" not in redacted


def test_redact_pii_from_dict():
    """Test PII keys are removed and values are redacted."""
    data = {
        "tenant_id": "test-tenant",
        "count": 42,
        "email": "user@example.com",  # Should be removed
        "name": "John Doe",  # Should be removed
        "message": "Contact user@example.com for details",  # Should be redacted
        "api_key": "secret123"  # Should be removed
    }
    
    safe_data = redact_pii_from_dict(data)
    
    # Should keep safe fields
    assert safe_data["tenant_id"] == "test-tenant"
    assert safe_data["count"] == 42
    
    # Should remove PII keys
    assert "email" not in safe_data
    assert "name" not in safe_data
    assert "api_key" not in safe_data
    
    # Should redact PII in string values
    assert "[EMAIL_REDACTED]" in safe_data["message"]
    assert "user@example.com" not in safe_data["message"]


def test_json_formatter_with_pii():
    """Test JSON formatter redacts PII from log records."""
    formatter = PiiRedactingFormatter()
    
    # Create log record with PII
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="User alice@example.com performed action",
        args=(),
        exc_info=None
    )
    record.extra = {
        "email": "alice@example.com",  # Should be removed
        "action": "login",  # Should be kept
    }
    
    formatted = formatter.format(record)
    log_entry = json.loads(formatted)
    
    # Check structure
    assert "timestamp" in log_entry
    assert log_entry["level"] == "INFO"
    assert log_entry["logger"] == "test.logger"
    
    # Check PII redaction
    assert "[EMAIL_REDACTED]" in log_entry["message"]
    assert "alice@example.com" not in formatted
    
    # Check extra fields (email key removed)
    assert "email" not in log_entry
    assert log_entry.get("action") == "login"


def test_json_formatter_with_exception():
    """Test JSON formatter includes redacted exception info."""
    formatter = PiiRedactingFormatter()
    
    try:
        raise ValueError("Invalid email: bad@example.com")
    except ValueError:
        import sys
        exc_info = sys.exc_info()
    
    record = logging.LogRecord(
        name="test.logger",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="An error occurred",
        args=(),
        exc_info=exc_info
    )
    
    formatted = formatter.format(record)
    log_entry = json.loads(formatted)
    
    # Check exception is included
    assert "exception" in log_entry
    assert "ValueError" in log_entry["exception"]
    
    # Check email is redacted
    assert "[EMAIL_REDACTED]" in log_entry["exception"]
    assert "bad@example.com" not in formatted


def test_audit_event_logging(caplog):
    """Test audit events log without PII."""
    with caplog.at_level(logging.INFO):
        log_audit_event(
            event_type="transaction_approved",
            user_id="user-123",
            tenant_id="tenant-abc",
            metadata={
                "amount": 150.00,
                "vendor": "Office Supplies",
                "email": "vendor@example.com",  # Should be stripped
                "card_number": "4532123456789010"  # Should be redacted
            }
        )
    
    # Check log was written
    assert len(caplog.records) > 0
    
    # Check message
    assert "AUDIT: transaction_approved" in caplog.text
    
    # Verify no PII in logs
    assert "vendor@example.com" not in caplog.text
    assert "4532123456789010" not in caplog.text


def test_logger_with_safe_data():
    """Test logger preserves safe data while redacting PII."""
    logger = get_logger("test.app")
    
    # Create string buffer to capture logs
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(PiiRedactingFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Log with mixed data
    logger.info("Processing transaction", extra={
        "transaction_id": "txn-12345",
        "amount": 250.50,
        "category": "Office Supplies",
        "email": "should-be-removed@example.com"
    })
    
    log_output = stream.getvalue()
    log_entry = json.loads(log_output)
    
    # Safe fields should be present
    assert log_entry.get("transaction_id") == "txn-12345"
    assert log_entry.get("amount") == 250.50
    assert log_entry.get("category") == "Office Supplies"
    
    # PII should be removed
    assert "email" not in log_entry
    assert "should-be-removed@example.com" not in log_output
    
    # Clean up
    logger.removeHandler(handler)


def test_redact_authorization_headers():
    """Test authorization headers and tokens are redacted."""
    text = 'Request with header Authorization: Bearer sk_live_1234567890abcdef'
    redacted = redact_pii_from_string(text)
    
    assert "[REDACTED]" in redacted
    assert "sk_live_1234567890abcdef" not in redacted
    assert "Authorization" in redacted  # Key preserved


def test_no_redaction_for_safe_content():
    """Test that safe content is not modified."""
    text = "Transaction processed successfully with amount $150.00"
    redacted = redact_pii_from_string(text)
    
    assert redacted == text  # Should be unchanged


def test_multiple_pii_patterns_in_one_string():
    """Test multiple PII patterns are all redacted."""
    text = "Contact john@example.com at 555-123-4567 with card 4532-1234-5678-9010"
    redacted = redact_pii_from_string(text)
    
    assert "[EMAIL_REDACTED]" in redacted
    assert "[PHONE_REDACTED]" in redacted
    assert "[CARD_REDACTED]" in redacted
    
    assert "john@example.com" not in redacted
    assert "555-123-4567" not in redacted
    assert "4532-1234-5678-9010" not in redacted

