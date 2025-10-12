"""
Analytics Event Sink (Phase 2b).

Logs events to JSON-lines files with no PII.
"""
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
import logging


logger = logging.getLogger(__name__)


ANALYTICS_DIR = "logs/analytics"


# Event type constants
EVENT_PAGE_VIEW = "page_view"
EVENT_REVIEW_APPROVE = "review_action_approve"
EVENT_REVIEW_REJECT = "review_action_reject"
EVENT_BULK_APPROVE = "bulk_approve_count"
EVENT_EXPLAIN_OPEN = "explain_open"
EVENT_EXPORT_RUN_POSTED = "export_run_posted"
EVENT_EXPORT_RUN_SKIPPED = "export_run_skipped"
EVENT_METRICS_VIEW = "metrics_view"
EVENT_BILLING_CHECKOUT_STARTED = "billing_checkout_started"
EVENT_BILLING_CHECKOUT_COMPLETED = "billing_checkout_completed"
EVENT_NOTIFICATION_SENT = "notification_sent"


def log_event(
    event_type: str,
    tenant_id: Optional[str] = None,
    user_role: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log analytics event to JSON-lines file.
    
    Args:
        event_type: Event type (use EVENT_* constants)
        tenant_id: Tenant identifier (no PII)
        user_role: User role (owner|staff, no names/emails)
        metadata: Additional event data (no PII)
        
    Example:
        log_event(EVENT_PAGE_VIEW, tenant_id="acme", user_role="owner", metadata={"page": "/review"})
    """
    # Ensure directory exists
    os.makedirs(ANALYTICS_DIR, exist_ok=True)
    
    # File per day (YYYYMMDD)
    date_str = datetime.utcnow().strftime("%Y%m%d")
    filepath = os.path.join(ANALYTICS_DIR, f"events_{date_str}.jsonl")
    
    # Build event payload (NO PII)
    event = {
        "ts": datetime.utcnow().isoformat(),
        "event": event_type,
        "tenant_id": tenant_id,
        "user_role": user_role,
        "metadata": metadata or {}
    }
    
    # Sanitize metadata to ensure no PII
    if metadata:
        # Remove any fields that might contain PII
        pii_fields = ["email", "name", "phone", "address", "ssn", "user_name"]
        for field in pii_fields:
            if field in event["metadata"]:
                del event["metadata"][field]
    
    # Append to file
    try:
        with open(filepath, "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as e:
        logger.error(f"Failed to log event {event_type}: {e}")


def log_page_view(page: str, tenant_id: Optional[str] = None, user_role: Optional[str] = None):
    """Log page view event."""
    log_event(EVENT_PAGE_VIEW, tenant_id, user_role, {"page": page})


def log_review_action(action: str, tenant_id: Optional[str] = None, count: int = 1):
    """Log review action (approve/reject)."""
    if action == "approve":
        log_event(EVENT_REVIEW_APPROVE, tenant_id, metadata={"count": count})
    elif action == "reject":
        log_event(EVENT_REVIEW_REJECT, tenant_id, metadata={"count": count})


def log_bulk_approve(count: int, tenant_id: Optional[str] = None):
    """Log bulk approve action."""
    log_event(EVENT_BULK_APPROVE, tenant_id, metadata={"count": count})


def log_explain_open(tenant_id: Optional[str] = None):
    """Log explain drawer opened."""
    log_event(EVENT_EXPLAIN_OPEN, tenant_id)


def log_export_run(posted_count: int, skipped_count: int, tenant_id: Optional[str] = None):
    """Log export run."""
    if posted_count > 0:
        log_event(EVENT_EXPORT_RUN_POSTED, tenant_id, metadata={"count": posted_count})
    if skipped_count > 0:
        log_event(EVENT_EXPORT_RUN_SKIPPED, tenant_id, metadata={"count": skipped_count})


def log_metrics_view(tenant_id: Optional[str] = None):
    """Log metrics page view."""
    log_event(EVENT_METRICS_VIEW, tenant_id)


def log_billing_checkout(status: str, plan: Optional[str] = None, tenant_id: Optional[str] = None):
    """Log billing checkout event."""
    if status == "started":
        log_event(EVENT_BILLING_CHECKOUT_STARTED, tenant_id, metadata={"plan": plan})
    elif status == "completed":
        log_event(EVENT_BILLING_CHECKOUT_COMPLETED, tenant_id, metadata={"plan": plan})


def log_notification_sent(notification_type: str, channel: str, tenant_id: Optional[str] = None):
    """Log notification sent."""
    log_event(EVENT_NOTIFICATION_SENT, tenant_id, metadata={"type": notification_type, "channel": channel})

