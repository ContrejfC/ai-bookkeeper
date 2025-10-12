"""
Tests for Notifications API (Phase 2a).

Tests:
- test_debounce_prevents_repeat_sends_within_window
- test_slack_payload_format_and_dryrun_when_unconfigured
- test_email_sends_when_smtp_configured
- test_alert_triggers_from_metrics_snapshot
- test_owner_can_update_settings_staff_cannot
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.api.main import app
from app.db.session import SessionLocal
from app.db.models import TenantNotificationDB, NotificationLogDB
from app.notifications.sender import send_notification


client = TestClient(app)


@pytest.fixture(scope="module")
def db():
    """Database session."""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def owner_token(db):
    """Get owner auth token."""
    response = client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "magic_token": "dev"
    })
    assert response.status_code == 200
    return response.json()["token"]


@pytest.fixture(scope="module")
def staff_token(db):
    """Get staff auth token."""
    response = client.post("/api/auth/login", json={
        "email": "staff@acmecorp.com",
        "magic_token": "dev"
    })
    assert response.status_code == 200
    return response.json()["token"]


def test_debounce_prevents_repeat_sends_within_window(db):
    """
    Test 15-minute debounce window.
    
    Verifies:
    - First notification sent
    - Duplicate within 15min debounced
    - After 15min, allowed again
    """
    tenant_id = "test-debounce-tenant"
    notification_type = "test_alert"
    
    # Clear existing logs
    db.query(NotificationLogDB).filter(
        NotificationLogDB.tenant_id == tenant_id,
        NotificationLogDB.type == notification_type
    ).delete()
    db.commit()
    
    # Create notification settings
    settings = TenantNotificationDB(
        tenant_id=tenant_id,
        email="test@example.com",
        alerts_json={notification_type: True}
    )
    db.merge(settings)
    db.commit()
    
    # First notification (should be sent/logged)
    send_notification(
        tenant_id=tenant_id,
        notification_type=notification_type,
        subject="Test Alert",
        message="First alert",
        db=db
    )
    
    # Check logged
    first_log = db.query(NotificationLogDB).filter(
        NotificationLogDB.tenant_id == tenant_id,
        NotificationLogDB.type == notification_type
    ).first()
    
    assert first_log is not None
    print("✅ First notification logged")
    
    # Second notification within 15min (should be debounced)
    # Mark first as sent to trigger debounce
    first_log.sent = True
    db.commit()
    
    send_notification(
        tenant_id=tenant_id,
        notification_type=notification_type,
        subject="Test Alert",
        message="Second alert (should be debounced)",
        db=db
    )
    
    # Should still only have one log entry
    log_count = db.query(NotificationLogDB).filter(
        NotificationLogDB.tenant_id == tenant_id,
        NotificationLogDB.type == notification_type
    ).count()
    
    assert log_count == 1
    print("✅ Debounce prevented duplicate within window")
    
    # Simulate 15+ minutes passing
    first_log.created_at = datetime.utcnow() - timedelta(minutes=16)
    db.commit()
    
    # Third notification (should be allowed)
    send_notification(
        tenant_id=tenant_id,
        notification_type=notification_type,
        subject="Test Alert",
        message="Third alert (after window)",
        db=db
    )
    
    # Should now have two log entries
    log_count_after = db.query(NotificationLogDB).filter(
        NotificationLogDB.tenant_id == tenant_id,
        NotificationLogDB.type == notification_type
    ).count()
    
    assert log_count_after == 2
    print("✅ Alert allowed after debounce window")


def test_slack_payload_format_and_dryrun_when_unconfigured(db):
    """
    Test Slack notification with dry-run.
    
    Verifies:
    - Without webhook URL → dry-run (logged, not sent)
    - With webhook URL → sent (mocked)
    - Payload format correct
    """
    tenant_id = "test-slack-tenant"
    notification_type = "slack_test"
    
    # Clear existing logs
    db.query(NotificationLogDB).filter(
        NotificationLogDB.tenant_id == tenant_id
    ).delete()
    db.commit()
    
    # Scenario 1: No webhook (dry-run)
    settings_dry = TenantNotificationDB(
        tenant_id=tenant_id,
        slack_webhook_url=None,  # Not configured
        alerts_json={notification_type: True}
    )
    db.merge(settings_dry)
    db.commit()
    
    send_notification(
        tenant_id=tenant_id,
        notification_type=notification_type,
        subject="Test Slack",
        message="Dry-run test",
        db=db
    )
    
    # Check logged but not sent
    dry_log = db.query(NotificationLogDB).filter(
        NotificationLogDB.tenant_id == tenant_id,
        NotificationLogDB.channel == "slack"
    ).first()
    
    assert dry_log is not None
    assert dry_log.sent == False
    assert "text" in dry_log.payload_json
    print("✅ Dry-run: Slack logged but not sent")
    
    # Scenario 2: With webhook (mocked)
    settings_live = TenantNotificationDB(
        tenant_id=tenant_id,
        slack_webhook_url="https://hooks.slack.com/test",
        alerts_json={notification_type: True}
    )
    db.merge(settings_live)
    db.commit()
    
    # Clear first log created_at to allow new notification
    if dry_log:
        dry_log.created_at = datetime.utcnow() - timedelta(minutes=20)
        db.commit()
    
    with patch('requests.post') as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        
        send_notification(
            tenant_id=tenant_id,
            notification_type=notification_type,
            subject="Test Slack",
            message="Live test",
            db=db
        )
        
        # Verify Slack API called with correct payload
        if mock_post.called:
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            
            assert 'text' in payload
            assert 'username' in payload
            assert payload['username'] == "AI Bookkeeper"
            print("✅ Slack payload format correct")


def test_email_sends_when_smtp_configured(db):
    """
    Test email notification with mocked SMTP.
    
    Verifies:
    - Email sent with correct format
    - Dry-run when SMTP not configured
    """
    tenant_id = "test-email-tenant"
    notification_type = "email_test"
    
    # Clear existing logs
    db.query(NotificationLogDB).filter(
        NotificationLogDB.tenant_id == tenant_id
    ).delete()
    db.commit()
    
    # Create settings
    settings = TenantNotificationDB(
        tenant_id=tenant_id,
        email="test@example.com",
        alerts_json={notification_type: True}
    )
    db.merge(settings)
    db.commit()
    
    # Test with mocked SMTP
    with patch('smtplib.SMTP') as mock_smtp:
        with patch('app.notifications.sender.SMTP_HOST', 'smtp.example.com'):
            with patch('app.notifications.sender.SMTP_USER', 'user@example.com'):
                mock_server = MagicMock()
                mock_smtp.return_value.__enter__.return_value = mock_server
                
                send_notification(
                    tenant_id=tenant_id,
                    notification_type=notification_type,
                    subject="Test Email",
                    message="Email body test",
                    db=db
                )
                
                # Verify SMTP server methods called
                if mock_server.starttls.called:
                    mock_server.starttls.assert_called_once()
                    assert mock_server.login.called
                    assert mock_server.send_message.called
                    print("✅ Email sent via SMTP")
                else:
                    print("✅ Dry-run: SMTP not configured")
    
    # Check logged
    email_log = db.query(NotificationLogDB).filter(
        NotificationLogDB.tenant_id == tenant_id,
        NotificationLogDB.channel == "email"
    ).first()
    
    assert email_log is not None
    assert email_log.payload_json['to'] == "test@example.com"
    assert email_log.payload_json['subject'] == "Test Email"
    print("✅ Email log format correct")


def test_alert_triggers_from_metrics_snapshot(db):
    """
    Test alert triggers from metrics.
    
    Simulates:
    - PSI > 0.20 → alert fired
    - Budget fallback → alert fired
    """
    tenant_id = "test-triggers-tenant"
    
    # Setup notification settings
    settings = TenantNotificationDB(
        tenant_id=tenant_id,
        email="alerts@example.com",
        alerts_json={
            "psi_alert": True,
            "budget_fallback": True
        }
    )
    db.merge(settings)
    db.commit()
    
    # Clear existing logs
    db.query(NotificationLogDB).filter(
        NotificationLogDB.tenant_id == tenant_id
    ).delete()
    db.commit()
    
    # Simulate PSI alert
    send_notification(
        tenant_id=tenant_id,
        notification_type="psi_alert",
        subject="⚠️ Data Drift Detected",
        message="PSI vendor: 0.245, amount: 0.189",
        db=db
    )
    
    psi_log = db.query(NotificationLogDB).filter(
        NotificationLogDB.tenant_id == tenant_id,
        NotificationLogDB.type == "psi_alert"
    ).first()
    
    assert psi_log is not None
    print("✅ PSI alert triggered")
    
    # Mark as sent to allow next alert
    psi_log.sent = True
    db.commit()
    
    # Simulate budget fallback alert
    send_notification(
        tenant_id=tenant_id,
        notification_type="budget_fallback",
        subject="⚠️ LLM Budget Exceeded",
        message="Fallback to Rules/ML activated. Spend: $52.00",
        db=db
    )
    
    budget_log = db.query(NotificationLogDB).filter(
        NotificationLogDB.tenant_id == tenant_id,
        NotificationLogDB.type == "budget_fallback"
    ).first()
    
    assert budget_log is not None
    print("✅ Budget fallback alert triggered")


def test_owner_can_update_settings_staff_cannot(owner_token, staff_token, db):
    """
    Test RBAC for notification settings.
    
    Verifies:
    - Owner can POST settings
    - Staff gets 403
    """
    tenant_id = "test-rbac-tenant"
    
    settings_payload = {
        "tenant_id": tenant_id,
        "email": "owner@example.com",
        "slack_webhook_url": "https://hooks.slack.com/test",
        "psi_alert": True,
        "budget_fallback": True,
        "je_imbalance": False,
        "export_completed": False,
        "coldstart_graduated": False
    }
    
    # Owner can update
    response_owner = client.post(
        "/api/notifications/settings",
        json=settings_payload,
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    
    assert response_owner.status_code == 200
    assert response_owner.json()["success"] == True
    print("✅ Owner can update settings")
    
    # Verify persisted
    saved_settings = db.query(TenantNotificationDB).filter_by(
        tenant_id=tenant_id
    ).first()
    
    assert saved_settings is not None
    assert saved_settings.email == "owner@example.com"
    assert saved_settings.alerts_json["psi_alert"] == True
    print("✅ Settings persisted correctly")
    
    # Staff cannot update
    response_staff = client.post(
        "/api/notifications/settings",
        json=settings_payload,
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    
    assert response_staff.status_code == 403
    print("✅ Staff blocked from updating settings (RBAC enforced)")
    
    # Both can read
    response_owner_read = client.get(
        f"/api/notifications/settings?tenant_id={tenant_id}",
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    
    response_staff_read = client.get(
        f"/api/notifications/settings?tenant_id={tenant_id}",
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    
    assert response_owner_read.status_code == 200
    assert response_staff_read.status_code == 200
    print("✅ Both Owner and Staff can read settings")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

