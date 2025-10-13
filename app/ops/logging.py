"""
Centralized Logging with PII Redaction & External Drain (SOC 2 Min Controls).

Provides:
- JSON structured logging with configurable levels
- PII redaction (reuses analytics PII stripper for consistency)
- Optional external log drain (HTTPS endpoint with retry/jitter)
- Graceful degradation to stdout when drain unavailable

Environment:
- LOG_LEVEL: DEBUG|INFO|WARNING|ERROR (default=INFO)
- LOG_DRAIN_URL: Optional HTTPS endpoint for log shipping
- LOG_DRAIN_API_KEY: Optional API key for drain authentication
"""
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, Any, Optional
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
import threading

# Import existing PII stripper for consistency
from app.analytics.sink import _strip_pii, _contains_email

# Configuration from environment
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DRAIN_URL = os.getenv("LOG_DRAIN_URL", "").strip()
LOG_DRAIN_API_KEY = os.getenv("LOG_DRAIN_API_KEY", "").strip()

# Additional PII patterns for log redaction (beyond analytics metadata)
PII_PATTERNS = [
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL_REDACTED]'),
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[SSN_REDACTED]'),
    (re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'), '[CARD_REDACTED]'),
    (re.compile(r'\b\d{3}-\d{3}-\d{4}\b'), '[PHONE_REDACTED]'),
    (re.compile(r'(password|secret|api_key|token|authorization)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), r'\1=[REDACTED]'),
]


def redact_pii_from_string(text: str) -> str:
    """
    Redact PII patterns from log strings.
    
    Covers: emails, SSN, card numbers, phone numbers, secrets/tokens.
    """
    if not isinstance(text, str):
        return text
    
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    
    return text


def redact_pii_from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redact PII from dictionary keys/values (reuses analytics stripper + string redaction).
    """
    # First pass: remove PII keys (reuse analytics logic)
    safe_data = _strip_pii(data)
    
    # Second pass: redact PII patterns in string values
    return {
        k: redact_pii_from_string(v) if isinstance(v, str) else v
        for k, v in safe_data.items()
    }


class PiiRedactingFormatter(logging.Formatter):
    """
    JSON log formatter with PII redaction.
    
    Outputs structured JSON with timestamp, level, message, and extra fields.
    Redacts PII from all string fields.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": redact_pii_from_string(record.getMessage()),
        }
        
        # Add extra fields (e.g., tenant_id, user_role, request_id)
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_entry.update(redact_pii_from_dict(record.extra))
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = redact_pii_from_string(self.formatException(record.exc_info))
        
        return json.dumps(log_entry)


class LogDrainHandler(logging.Handler):
    """
    Asynchronous log handler that ships logs to external HTTPS drain.
    
    Features:
    - Batch sending (accumulate up to 100 logs or 5 seconds)
    - Retry with exponential backoff + jitter
    - Graceful degradation (logs to stderr on failure)
    """
    
    def __init__(self, drain_url: str, api_key: Optional[str] = None, batch_size: int = 100, flush_interval: float = 5.0):
        super().__init__()
        self.drain_url = drain_url
        self.api_key = api_key
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer = []
        self.lock = threading.Lock()
        self.last_flush = time.time()
        self._start_flush_thread()
    
    def emit(self, record: logging.LogRecord):
        """Add log to buffer and flush if needed."""
        try:
            log_entry = self.format(record)
            
            with self.lock:
                self.buffer.append(log_entry)
                
                # Flush if batch full
                if len(self.buffer) >= self.batch_size:
                    self._flush()
        
        except Exception:
            self.handleError(record)
    
    def _start_flush_thread(self):
        """Start background thread to flush logs periodically."""
        def flush_periodically():
            while True:
                time.sleep(self.flush_interval)
                with self.lock:
                    if time.time() - self.last_flush >= self.flush_interval and self.buffer:
                        self._flush()
        
        thread = threading.Thread(target=flush_periodically, daemon=True)
        thread.start()
    
    def _flush(self):
        """Send buffered logs to drain with retry."""
        if not self.buffer:
            return
        
        batch = self.buffer[:]
        self.buffer.clear()
        self.last_flush = time.time()
        
        # Try to send (with basic retry)
        for attempt in range(3):
            try:
                import requests
                
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                response = requests.post(
                    self.drain_url,
                    data="\n".join(batch),
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code < 400:
                    return  # Success
                
                # Log drain rejected
                if attempt == 2:  # Last attempt
                    print(f"[LogDrain] Failed after 3 attempts: {response.status_code}", file=os.sys.stderr)
                    # Degrade to stderr
                    for entry in batch:
                        print(entry, file=os.sys.stderr)
                    return
            
            except Exception as e:
                if attempt == 2:  # Last attempt
                    print(f"[LogDrain] Error shipping logs: {e}", file=os.sys.stderr)
                    # Degrade to stderr
                    for entry in batch:
                        print(entry, file=os.sys.stderr)
                    return
                
                # Exponential backoff with jitter
                time.sleep((2 ** attempt) * 0.1 + (time.time() % 0.1))
    
    def close(self):
        """Flush remaining logs before closing."""
        with self.lock:
            self._flush()
        super().close()


def configure_logging() -> logging.Logger:
    """
    Configure centralized structured logging with PII redaction.
    
    Returns root logger configured with:
    - JSON formatter with PII redaction
    - Console handler (stdout)
    - Optional external drain handler
    
    Call once at application startup.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler (stdout) with JSON + PII redaction
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(PiiRedactingFormatter())
    root_logger.addHandler(console_handler)
    
    # Optional drain handler
    if LOG_DRAIN_URL:
        try:
            drain_handler = LogDrainHandler(LOG_DRAIN_URL, LOG_DRAIN_API_KEY)
            drain_handler.setFormatter(PiiRedactingFormatter())
            root_logger.addHandler(drain_handler)
            root_logger.info(f"Log drain enabled: {LOG_DRAIN_URL[:40]}...")
        except Exception as e:
            root_logger.warning(f"Failed to configure log drain: {e}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with PII redaction configured.
    
    Usage:
        from app.ops.logging import get_logger
        logger = get_logger(__name__)
        logger.info("User logged in", extra={"tenant_id": "abc", "user_role": "owner"})
    """
    return logging.getLogger(name)


def log_audit_event(event_type: str, user_id: Optional[str] = None, tenant_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
    """
    Log an audit event (decision, export, settings change).
    
    Args:
        event_type: Type of audit event (e.g., "transaction_approved", "export_started")
        user_id: User identifier (hashed/anonymized)
        tenant_id: Tenant identifier
        metadata: Additional context (will be PII-redacted)
    """
    logger = get_logger("audit")
    
    safe_metadata = redact_pii_from_dict(metadata or {})
    
    audit_log = {
        "event_type": event_type,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "metadata": safe_metadata
    }
    
    logger.info(f"AUDIT: {event_type}", extra=audit_log)


# Initialize logging on module import (can be reconfigured later)
if __name__ != "__main__":
    configure_logging()

