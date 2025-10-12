"""
Notification Sender Layer (Phase 2a).

Sends alerts via Email and Slack with 15-minute debounce.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session

from app.db.models import NotificationLogDB, TenantNotificationDB


logger = logging.getLogger(__name__)


# SMTP Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@ai-bookkeeper.com")

# Debounce window (15 minutes)
DEBOUNCE_MINUTES = 15


def should_send_notification(
    tenant_id: str,
    notification_type: str,
    db: Session
) -> bool:
    """
    Check if notification should be sent (debounce).
    
    Returns False if same {tenant, type} sent within last 15 minutes.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=DEBOUNCE_MINUTES)
    
    recent = db.query(NotificationLogDB).filter(
        NotificationLogDB.tenant_id == tenant_id,
        NotificationLogDB.type == notification_type,
        NotificationLogDB.created_at >= cutoff,
        NotificationLogDB.sent == True
    ).first()
    
    return recent is None


def send_email_notification(
    tenant_id: str,
    notification_type: str,
    subject: str,
    body: str,
    to_email: str,
    db: Session
) -> bool:
    """
    Send email notification.
    
    Returns True if sent, False if dry-run or failed.
    """
    payload = {
        "to": to_email,
        "subject": subject,
        "body": body
    }
    
    # Log entry
    log_entry = NotificationLogDB(
        tenant_id=tenant_id,
        channel="email",
        type=notification_type,
        payload_json=payload,
        sent=False
    )
    db.add(log_entry)
    db.commit()
    
    # Check if SMTP configured
    if not SMTP_HOST or not SMTP_USER:
        logger.info(f"Dry-run: Email notification ({notification_type}) to {to_email}")
        return False
    
    # Send email
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        
        # Mark as sent
        log_entry.sent = True
        db.commit()
        
        logger.info(f"Email sent: {notification_type} to {to_email}")
        return True
    
    except Exception as e:
        log_entry.error_message = str(e)
        db.commit()
        logger.error(f"Email send failed: {e}")
        return False


def send_slack_notification(
    tenant_id: str,
    notification_type: str,
    message: str,
    webhook_url: str,
    db: Session
) -> bool:
    """
    Send Slack notification.
    
    Returns True if sent, False if dry-run or failed.
    """
    try:
        import requests
    except ImportError:
        logger.warning("requests library not installed, Slack disabled")
        return False
    
    payload = {
        "text": message,
        "username": "AI Bookkeeper",
        "icon_emoji": ":robot_face:"
    }
    
    # Log entry
    log_entry = NotificationLogDB(
        tenant_id=tenant_id,
        channel="slack",
        type=notification_type,
        payload_json=payload,
        sent=False
    )
    db.add(log_entry)
    db.commit()
    
    # Check if webhook configured
    if not webhook_url:
        logger.info(f"Dry-run: Slack notification ({notification_type})")
        return False
    
    # Send Slack message
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=5
        )
        response.raise_for_status()
        
        # Mark as sent
        log_entry.sent = True
        db.commit()
        
        logger.info(f"Slack sent: {notification_type}")
        return True
    
    except Exception as e:
        log_entry.error_message = str(e)
        db.commit()
        logger.error(f"Slack send failed: {e}")
        return False


def send_notification(
    tenant_id: str,
    notification_type: str,
    subject: str,
    message: str,
    db: Session
):
    """
    Send notification via all configured channels.
    
    Applies 15-minute debounce.
    """
    # Check debounce
    if not should_send_notification(tenant_id, notification_type, db):
        logger.info(f"Debounced: {notification_type} for tenant {tenant_id}")
        return
    
    # Get notification settings
    settings = db.query(TenantNotificationDB).filter_by(
        tenant_id=tenant_id
    ).first()
    
    if not settings:
        logger.warning(f"No notification settings for tenant {tenant_id}")
        return
    
    # Check if alert enabled
    alerts = settings.alerts_json or {}
    if not alerts.get(notification_type, False):
        logger.info(f"Alert {notification_type} disabled for tenant {tenant_id}")
        return
    
    # Send email
    if settings.email:
        send_email_notification(
            tenant_id=tenant_id,
            notification_type=notification_type,
            subject=subject,
            body=message,
            to_email=settings.email,
            db=db
        )
    
    # Send Slack
    if settings.slack_webhook_url:
        send_slack_notification(
            tenant_id=tenant_id,
            notification_type=notification_type,
            message=f"*{subject}*\n\n{message}",
            webhook_url=settings.slack_webhook_url,
            db=db
        )

