#!/usr/bin/env python3
"""
Test Notification System for Pilot Tenants

Sends test notifications to verify email/Slack configuration.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.db.models import TenantNotificationSettingsDB, NotificationLogDB


def test_notification(db, tenant_id, notification_type="test", dry_run=True):
    """Send a test notification for a tenant."""
    
    print(f"\nTesting notifications for {tenant_id}...")
    
    # Get notification settings
    settings = db.query(TenantNotificationSettingsDB).filter_by(
        tenant_id=tenant_id
    ).first()
    
    if not settings:
        print(f"⚠️  No notification settings for {tenant_id}")
        return False
    
    print(f"  Email: {settings.email or 'not configured'}")
    print(f"  Slack: {'configured' if settings.slack_webhook_url else 'not configured'}")
    print(f"  Enabled: {settings.alerts_enabled}")
    
    if not settings.alerts_enabled:
        print(f"⚠️  Alerts disabled for {tenant_id}")
        return False
    
    # Log test notification
    log_entry = NotificationLogDB(
        tenant_id=tenant_id,
        notification_type=notification_type,
        channel="email" if settings.email else "slack",
        recipient=settings.email or settings.slack_webhook_url,
        payload={"test": True, "message": "Test notification"},
        status="dry_run" if dry_run else "sent",
        sent_at=datetime.utcnow()
    )
    
    db.add(log_entry)
    
    try:
        db.commit()
        status = "dry-run" if dry_run else "sent"
        print(f"✓ Test notification logged ({status})")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error logging notification: {e}")
        return False


def main():
    """Test notifications for all pilot tenants."""
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Notification Test Tool")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("Mode: DRY RUN (notifications logged but not sent)")
    print()
    
    db = SessionLocal()
    
    try:
        # Get all pilot tenants with notifications
        settings = db.query(TenantNotificationSettingsDB).filter(
            TenantNotificationSettingsDB.tenant_id.like("pilot-%")
        ).all()
        
        if not settings:
            print("⚠️  No pilot tenant notifications found.")
            print("Run: python3 scripts/create_pilot_tenants.py")
            return
        
        print(f"Found {len(settings)} pilot tenants")
        
        success_count = 0
        for tenant_settings in settings:
            if test_notification(db, tenant_settings.tenant_id, dry_run=True):
                success_count += 1
        
        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"✅ Tested {success_count}/{len(settings)} tenants")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        print("To send real notifications:")
        print("1. Configure SMTP settings in .env")
        print("2. Set valid Slack webhook URLs")
        print("3. Run with --live flag (not implemented yet)")
        print()
        print("Check notification_log table:")
        print("  SELECT * FROM notification_log WHERE tenant_id LIKE 'pilot-%';")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()

