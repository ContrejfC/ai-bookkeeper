"""
Notifications API (Phase 2a).

Endpoints:
- GET /api/notifications/settings
- POST /api/notifications/settings
- POST /api/notifications/test
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.db.models import TenantNotificationDB, DecisionAuditLogDB
from app.ui.rbac import User, get_current_user, Role, require_role
from app.notifications.sender import send_email_notification, send_slack_notification


router = APIRouter(prefix="/api/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)


class NotificationSettings(BaseModel):
    """Notification settings request/response."""
    tenant_id: str
    email: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    psi_alert: bool = False
    budget_fallback: bool = False
    je_imbalance: bool = False
    export_completed: bool = False
    coldstart_graduated: bool = False


class TestNotificationRequest(BaseModel):
    """Test notification request."""
    tenant_id: str
    channel: str  # 'email' or 'slack'


@router.get("/settings", response_model=NotificationSettings)
async def get_notification_settings(
    tenant_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get notification settings for tenant.
    
    RBAC: Owner and Staff can read.
    """
    # Get settings
    settings = db.query(TenantNotificationDB).filter_by(
        tenant_id=tenant_id
    ).first()
    
    if not settings:
        # Return defaults
        return NotificationSettings(
            tenant_id=tenant_id,
            email=None,
            slack_webhook_url=None,
            psi_alert=False,
            budget_fallback=False,
            je_imbalance=False,
            export_completed=False,
            coldstart_graduated=False
        )
    
    # Parse alerts_json
    alerts = settings.alerts_json or {}
    
    return NotificationSettings(
        tenant_id=tenant_id,
        email=settings.email,
        slack_webhook_url=settings.slack_webhook_url,
        psi_alert=alerts.get("psi_alert", False),
        budget_fallback=alerts.get("budget_fallback", False),
        je_imbalance=alerts.get("je_imbalance", False),
        export_completed=alerts.get("export_completed", False),
        coldstart_graduated=alerts.get("coldstart_graduated", False)
    )


@router.post("/settings")
async def update_notification_settings(
    settings: NotificationSettings,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update notification settings.
    
    RBAC: Owner only.
    """
    # RBAC: Owner only
    require_role(Role.OWNER, user)
    
    # Build alerts_json
    alerts_json = {
        "psi_alert": settings.psi_alert,
        "budget_fallback": settings.budget_fallback,
        "je_imbalance": settings.je_imbalance,
        "export_completed": settings.export_completed,
        "coldstart_graduated": settings.coldstart_graduated
    }
    
    # Get or create settings
    existing = db.query(TenantNotificationDB).filter_by(
        tenant_id=settings.tenant_id
    ).first()
    
    if existing:
        # Update
        existing.email = settings.email
        existing.slack_webhook_url = settings.slack_webhook_url
        existing.alerts_json = alerts_json
        existing.updated_at = datetime.utcnow()
        existing.updated_by = user.user_id
    else:
        # Create
        new_settings = TenantNotificationDB(
            tenant_id=settings.tenant_id,
            email=settings.email,
            slack_webhook_url=settings.slack_webhook_url,
            alerts_json=alerts_json,
            updated_by=user.user_id
        )
        db.add(new_settings)
    
    # Audit entry
    audit = DecisionAuditLogDB(
        timestamp=datetime.utcnow(),
        tenant_id=settings.tenant_id,
        action="notification_settings_updated",
        user_id=user.user_id
    )
    db.add(audit)
    
    db.commit()
    
    logger.info(f"Notification settings updated for tenant {settings.tenant_id} by {user.user_id}")
    
    return {"success": True, "message": "Settings updated"}


@router.post("/test")
async def test_notification(
    request: TestNotificationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send test notification.
    
    RBAC: Owner only.
    """
    # RBAC: Owner only
    require_role(Role.OWNER, user)
    
    # Get settings
    settings = db.query(TenantNotificationDB).filter_by(
        tenant_id=request.tenant_id
    ).first()
    
    if not settings:
        raise HTTPException(status_code=404, detail="Notification settings not found")
    
    # Send test notification
    if request.channel == "email":
        if not settings.email:
            raise HTTPException(status_code=400, detail="Email not configured")
        
        sent = send_email_notification(
            tenant_id=request.tenant_id,
            notification_type="test",
            subject="Test Notification from AI Bookkeeper",
            body="This is a test notification. Your email alerts are working correctly.",
            to_email=settings.email,
            db=db
        )
        
        if not sent:
            return {
                "success": False,
                "message": "Dry-run: SMTP not configured. Email logged but not sent."
            }
        
        return {"success": True, "message": f"Test email sent to {settings.email}"}
    
    elif request.channel == "slack":
        if not settings.slack_webhook_url:
            raise HTTPException(status_code=400, detail="Slack webhook not configured")
        
        sent = send_slack_notification(
            tenant_id=request.tenant_id,
            notification_type="test",
            message="*Test Notification*\n\nThis is a test notification. Your Slack alerts are working correctly.",
            webhook_url=settings.slack_webhook_url,
            db=db
        )
        
        if not sent:
            return {
                "success": False,
                "message": "Dry-run: Slack webhook logged but not sent."
            }
        
        return {"success": True, "message": "Test Slack message sent"}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid channel. Use 'email' or 'slack'.")

