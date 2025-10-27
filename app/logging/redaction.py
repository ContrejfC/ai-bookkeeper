"""
PII Redaction - Sensitive Data Protection
=========================================

This module provides logging filters and functions to redact sensitive information
from logs and exports.

Redacted Patterns:
-----------------
- Email addresses → ***EMAIL***
- Credit card numbers (PAN) → ***PAN***
- OAuth tokens → ***TOKEN***
- API keys → ***APIKEY***
- Social Security Numbers → ***SSN***
- Passwords → ***PASSWORD***

Usage:
------
```python
from app.logging.redaction import RedactionFilter, redact_text

# Add to logger
handler.addFilter(RedactionFilter())

# Redact text manually
clean_text = redact_text("User email is john@example.com")
```
"""
import re
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Redaction patterns
PATTERNS = {
    'email': (
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '***EMAIL***'
    ),
    'pan': (
        r'\b[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}\b',
        '***PAN***'
    ),
    'ssn': (
        r'\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b',
        '***SSN***'
    ),
    'bearer_token': (
        r'Bearer\s+[A-Za-z0-9\-_.~+/]+=*',
        'Bearer ***TOKEN***'
    ),
    'api_key': (
        r'\b(sk|pk)_[a-z]+_[A-Za-z0-9]{24,}\b',
        '***APIKEY***'
    ),
    'password_field': (
        r'"password"\s*:\s*"[^"]*"',
        '"password": "***PASSWORD***"'
    ),
    'access_token': (
        r'"access_token"\s*:\s*"[^"]*"',
        '"access_token": "***TOKEN***"'
    ),
    'refresh_token': (
        r'"refresh_token"\s*:\s*"[^"]*"',
        '"refresh_token": "***TOKEN***"'
    ),
    'client_secret': (
        r'"client_secret"\s*:\s*"[^"]*"',
        '"client_secret": "***SECRET***"'
    ),
    'stripe_key': (
        r'(sk|pk)_live_[A-Za-z0-9]{24,}',
        '***STRIPE_KEY***'
    ),
    'jwt': (
        r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_.~+/]*',
        '***JWT***'
    )
}


def redact_text(text: str, patterns: Dict[str, tuple] = None) -> str:
    """
    Redact sensitive information from text.
    
    Args:
        text: Text to redact
        patterns: Optional custom patterns (defaults to PATTERNS)
        
    Returns:
        Redacted text
    """
    if not text:
        return text
    
    patterns = patterns or PATTERNS
    result = text
    
    for name, (pattern, replacement) in patterns.items():
        try:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        except Exception as e:
            logger.warning(f"Error applying redaction pattern {name}: {e}")
    
    return result


def redact_dict(data: Dict[str, Any], redact_keys: bool = True) -> Dict[str, Any]:
    """
    Redact sensitive information from dictionary (recursively).
    
    Args:
        data: Dictionary to redact
        redact_keys: If True, also redact known sensitive keys
        
    Returns:
        Redacted dictionary
    """
    if not isinstance(data, dict):
        return data
    
    sensitive_keys = {
        'password', 'secret', 'token', 'api_key', 'access_token',
        'refresh_token', 'client_secret', 'stripe_key', 'ssn',
        'credit_card', 'card_number', 'cvv', 'pin'
    }
    
    result = {}
    
    for key, value in data.items():
        # Check if key is sensitive
        if redact_keys and any(sk in key.lower() for sk in sensitive_keys):
            result[key] = '***REDACTED***'
        # Recursively redact nested dicts
        elif isinstance(value, dict):
            result[key] = redact_dict(value, redact_keys)
        # Recursively redact lists
        elif isinstance(value, list):
            result[key] = [
                redact_dict(item, redact_keys) if isinstance(item, dict) else redact_text(str(item))
                for item in value
            ]
        # Redact string values
        elif isinstance(value, str):
            result[key] = redact_text(value)
        else:
            result[key] = value
    
    return result


class RedactionFilter(logging.Filter):
    """
    Logging filter that redacts sensitive information from log messages.
    
    Usage:
    ------
    ```python
    handler = logging.StreamHandler()
    handler.addFilter(RedactionFilter())
    logger.addHandler(handler)
    ```
    """
    
    def filter(self, record):
        # Redact message
        if record.msg:
            record.msg = redact_text(str(record.msg))
        
        # Redact args
        if record.args:
            if isinstance(record.args, dict):
                record.args = redact_dict(record.args)
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(redact_text(str(arg)) for arg in record.args)
        
        # Redact extra fields
        if hasattr(record, '__dict__'):
            for key in list(record.__dict__.keys()):
                if key not in ('name', 'msg', 'args', 'created', 'filename', 'funcName',
                              'levelname', 'levelno', 'lineno', 'module', 'msecs',
                              'message', 'pathname', 'process', 'processName',
                              'relativeCreated', 'thread', 'threadName'):
                    value = getattr(record, key)
                    if isinstance(value, str):
                        setattr(record, key, redact_text(value))
                    elif isinstance(value, dict):
                        setattr(record, key, redact_dict(value))
        
        return True


def configure_redaction(logger_instance: logging.Logger = None):
    """
    Configure redaction filter on a logger.
    
    Args:
        logger_instance: Logger to configure (defaults to root logger)
    """
    if logger_instance is None:
        logger_instance = logging.getLogger()
    
    # Add filter to all handlers
    for handler in logger_instance.handlers:
        handler.addFilter(RedactionFilter())
    
    logger.info("PII redaction filter configured")

