"""
Product Analytics Event Sink (Phase 2b - Restored after module rename).

Logs events to JSON-lines format without PII for daily rollup aggregation.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Event log directory
EVENTS_DIR = Path("logs/analytics")
EVENTS_DIR.mkdir(parents=True, exist_ok=True)

# Event type constants (for tests and consistency)
EVENT_PAGE_VIEW = "page_view"
EVENT_REVIEW_APPROVE = "transaction_reviewed"
EVENT_REVIEW_REJECT = "transaction_rejected"
EVENT_RULE_CREATED = "rule_created"
EVENT_RULE_DELETED = "rule_deleted"
EVENT_EXPORT_STARTED = "export_started"
EVENT_EXPORT_COMPLETED = "export_completed"


def log_event(
    event_type: str,
    tenant_id: Optional[str] = None,
    user_role: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a product analytics event (NO PII).
    
    Args:
        event_type: Type of event (e.g., "transaction_reviewed", "rule_created")
        tenant_id: Tenant identifier (hashed/anonymized)
        user_role: User role (owner/staff, no email/name)
        metadata: Additional context (counts, durations, no PII)
    """
    # Strip PII from metadata
    safe_metadata = _strip_pii(metadata or {})
    
    event = {
        "event": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "tenant_id": tenant_id,
        "user_role": user_role,
        "metadata": safe_metadata
    }
    
    # Write to daily JSON-lines file
    date_str = datetime.utcnow().strftime("%Y%m%d")
    log_file = EVENTS_DIR / f"events_{date_str}.jsonl"
    
    try:
        with open(log_file, "a") as f:
            f.write(json.dumps(event) + "\n")
        logger.debug(f"Logged event: {event_type} for tenant={tenant_id}")
    except Exception as e:
        logger.error(f"Failed to log event {event_type}: {e}")


def log_page_view(
    path: str,
    tenant_id: Optional[str] = None,
    user_role: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a page view event (convenience helper).
    
    Args:
        path: Page path (e.g., "/review", "/metrics")
        tenant_id: Tenant identifier (hashed/anonymized)
        user_role: User role (owner/staff)
        metadata: Additional context (e.g., filters applied, load time)
    """
    combined_metadata = {"path": path}
    if metadata:
        combined_metadata.update(metadata)
    
    log_event(
        event_type=EVENT_PAGE_VIEW,
        tenant_id=tenant_id,
        user_role=user_role,
        metadata=combined_metadata
    )


def _strip_pii(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove PII fields from metadata.
    
    Strips: email, name, address, phone, ssn, account_number, etc.
    Keeps: counts, durations, status, confidence, reason codes
    """
    pii_keys = {
        "email", "name", "first_name", "last_name", "full_name",
        "address", "phone", "phone_number", "ssn", "social_security",
        "account_number", "routing_number", "card_number", "cvv",
        "password", "token", "secret", "api_key"
    }
    
    return {
        k: v for k, v in metadata.items()
        if k.lower() not in pii_keys and not _contains_email(str(v))
    }


def _contains_email(value: str) -> bool:
    """Check if value looks like an email address."""
    return "@" in value and "." in value.split("@")[-1]


# Convenience functions for common events

def log_transaction_reviewed(tenant_id: str, user_role: str, action: str, reason: str):
    """Log a transaction review event."""
    log_event(
        "transaction_reviewed",
        tenant_id=tenant_id,
        user_role=user_role,
        metadata={"action": action, "reason": reason}
    )


def log_rule_created(tenant_id: str, user_role: str, rule_type: str):
    """Log a rule creation event."""
    log_event(
        "rule_created",
        tenant_id=tenant_id,
        user_role=user_role,
        metadata={"rule_type": rule_type}
    )


def log_export_started(tenant_id: str, user_role: str, export_type: str, count: int):
    """Log an export operation."""
    log_event(
        "export_started",
        tenant_id=tenant_id,
        user_role=user_role,
        metadata={"export_type": export_type, "record_count": count}
    )


def log_page_view(tenant_id: str, user_role: str, page: str):
    """Log a page view event."""
    log_event(
        "page_view",
        tenant_id=tenant_id,
        user_role=user_role,
        metadata={"page": page}
    )


def log_onboarding_completed(tenant_id: str, user_role: str, duration_seconds: int):
    """Log onboarding completion."""
    log_event(
        "onboarding_completed",
        tenant_id=tenant_id,
        user_role=user_role,
        metadata={"duration_seconds": duration_seconds}
    )
