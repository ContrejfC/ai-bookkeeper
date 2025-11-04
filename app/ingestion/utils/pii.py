"""
PII Redaction Utilities
=======================

Redact personally identifiable information from logs and artifacts.
"""

import re
from typing import Any, Dict, List


# PII patterns
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    re.IGNORECASE
)

PHONE_PATTERN = re.compile(
    r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
)

SSN_PATTERN = re.compile(
    r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'
)

CREDIT_CARD_PATTERN = re.compile(
    r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
)

ACCOUNT_NUMBER_PATTERN = re.compile(
    r'\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b'  # IBAN-like
)

# Redaction markers
EMAIL_REDACTED = "***EMAIL***"
PHONE_REDACTED = "***PHONE***"
SSN_REDACTED = "***SSN***"
PAN_REDACTED = "***PAN***"
ACCOUNT_REDACTED = "***ACCOUNT***"


def redact_email(text: str) -> str:
    """Redact email addresses."""
    return EMAIL_PATTERN.sub(EMAIL_REDACTED, text)


def redact_phone(text: str) -> str:
    """Redact phone numbers."""
    return PHONE_PATTERN.sub(PHONE_REDACTED, text)


def redact_ssn(text: str) -> str:
    """Redact social security numbers."""
    return SSN_PATTERN.sub(SSN_REDACTED, text)


def redact_credit_card(text: str) -> str:
    """Redact credit card numbers."""
    return CREDIT_CARD_PATTERN.sub(PAN_REDACTED, text)


def redact_account_number(text: str) -> str:
    """Redact account numbers."""
    return ACCOUNT_NUMBER_PATTERN.sub(ACCOUNT_REDACTED, text)


def redact_pii(text: str, aggressive: bool = False) -> str:
    """
    Redact all PII from text.
    
    Args:
        text: Text to redact
        aggressive: If True, also redact account numbers and other sensitive data
    
    Returns:
        Redacted text
    """
    if not text:
        return text
    
    # Always redact these
    text = redact_email(text)
    text = redact_phone(text)
    text = redact_ssn(text)
    text = redact_credit_card(text)
    
    # Optionally redact account numbers
    if aggressive:
        text = redact_account_number(text)
    
    return text


def redact_dict(data: Dict[str, Any], fields: List[str] = None, aggressive: bool = False) -> Dict[str, Any]:
    """
    Redact PII from dictionary values.
    
    Args:
        data: Dictionary to redact
        fields: Specific fields to redact (None = all string fields)
        aggressive: If True, use aggressive redaction
    
    Returns:
        New dictionary with redacted values
    """
    if not data:
        return data
    
    redacted = {}
    for key, value in data.items():
        if fields and key not in fields:
            # Skip this field
            redacted[key] = value
        elif isinstance(value, str):
            redacted[key] = redact_pii(value, aggressive=aggressive)
        elif isinstance(value, dict):
            redacted[key] = redact_dict(value, fields=fields, aggressive=aggressive)
        elif isinstance(value, list):
            redacted[key] = [
                redact_dict(item, fields=fields, aggressive=aggressive) if isinstance(item, dict)
                else redact_pii(item, aggressive=aggressive) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            redacted[key] = value
    
    return redacted


def redact_list(data: List[Any], aggressive: bool = False) -> List[Any]:
    """
    Redact PII from list of values.
    
    Args:
        data: List to redact
        aggressive: If True, use aggressive redaction
    
    Returns:
        New list with redacted values
    """
    if not data:
        return data
    
    return [
        redact_dict(item, aggressive=aggressive) if isinstance(item, dict)
        else redact_pii(item, aggressive=aggressive) if isinstance(item, str)
        else item
        for item in data
    ]


def contains_pii(text: str) -> bool:
    """
    Check if text contains PII patterns.
    
    Args:
        text: Text to check
    
    Returns:
        True if PII detected
    """
    if not text:
        return False
    
    return bool(
        EMAIL_PATTERN.search(text) or
        PHONE_PATTERN.search(text) or
        SSN_PATTERN.search(text) or
        CREDIT_CARD_PATTERN.search(text)
    )


def mask_account_number(account: str, visible_chars: int = 4) -> str:
    """
    Mask account number, showing only last N characters.
    
    Args:
        account: Account number
        visible_chars: Number of trailing characters to show
    
    Returns:
        Masked account number (e.g., "****1234")
    """
    if not account or len(account) <= visible_chars:
        return account
    
    masked_length = len(account) - visible_chars
    return "*" * masked_length + account[-visible_chars:]


def safe_sample(text: str, max_length: int = 200, redact: bool = True) -> str:
    """
    Create a safe sample of text for logging/artifacts.
    
    Args:
        text: Text to sample
        max_length: Maximum length of sample
        redact: Whether to redact PII
    
    Returns:
        Safe text sample
    """
    if not text:
        return ""
    
    # Truncate
    sample = text[:max_length]
    if len(text) > max_length:
        sample += "..."
    
    # Redact if requested
    if redact:
        sample = redact_pii(sample, aggressive=True)
    
    return sample



