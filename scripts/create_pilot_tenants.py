#!/usr/bin/env python3
"""
Create Pilot Tenants for Phase 2b

Programmatically creates pilot tenants with safety settings.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.db.models import TenantSettingsDB, TenantNotificationSettingsDB, DecisionAuditLogDB


PILOT_CONFIGS = [
    {
        "name": "Pilot 1: Standard Small Business",
        "tenant_id": "pilot-smb-001",
        "industry": "Retail",
        "coa_template": "standard_small_business",
        "autopost_enabled": False,
        "autopost_threshold": 0.90,
        "llm_tenant_cap_usd": 50,
        "notification_email": "pilot1@example.com",
        "notification_triggers": ["psi_alert", "budget_fallback", "je_imbalance"],
    },
    {
        "name": "Pilot 2: Professional Services",
        "tenant_id": "pilot-prof-002",
        "industry": "Consulting",
        "coa_template": "professional_services",
        "autopost_enabled": False,
        "autopost_threshold": 0.92,
        "llm_tenant_cap_usd": 75,
        "notification_email": "pilot2@example.com",
        "notification_slack": "https://hooks.slack.com/services/EXAMPLE",
        "notification_triggers": ["psi_alert", "budget_fallback", "je_imbalance", "export_completed"],
    },
    {
        "name": "Pilot 3: GAAP Accounting Firm",
        "tenant_id": "pilot-firm-003",
        "industry": "Accounting",
        "coa_template": "gaap_accounting_firm",
        "autopost_enabled": False,
        "autopost_threshold": 0.88,
        "llm_tenant_cap_usd": 100,
        "notification_email": "pilot3@example.com",
        "notification_slack": "https://hooks.slack.com/services/EXAMPLE2",
        "notification_triggers": ["psi_alert", "budget_fallback", "je_imbalance", "export_completed", "cold_start_graduated"],
    },
]


def create_pilot_tenant(db, config):
    """Create a single pilot tenant."""
    
    tenant_id = config["tenant_id"]
    
    print(f"\n{'='*60}")
    print(f"Creating: {config['name']}")
    print(f"Tenant ID: {tenant_id}")
    print(f"{'='*60}")
    
    # Check if tenant already exists
    existing = db.query(TenantSettingsDB).filter_by(tenant_id=tenant_id).first()
    if existing:
        print(f"⚠️  Tenant {tenant_id} already exists. Skipping.")
        return existing
    
    # Create tenant settings
    settings = TenantSettingsDB(
        tenant_id=tenant_id,
        autopost_enabled=config["autopost_enabled"],
        autopost_threshold=config["autopost_threshold"],
        llm_tenant_cap_usd=config["llm_tenant_cap_usd"],
        updated_by="system",
        updated_at=datetime.utcnow()
    )
    
    db.add(settings)
    print(f"✓ Tenant settings created")
    print(f"  - AUTOPOST: {config['autopost_enabled']}")
    print(f"  - Threshold: {config['autopost_threshold']}")
    print(f"  - LLM Budget: ${config['llm_tenant_cap_usd']}/month")
    
    # Create notification settings
    notification_config = {
        "email": config.get("notification_email"),
        "slack_webhook_url": config.get("notification_slack"),
        "triggers": config.get("notification_triggers", [])
    }
    
    notifications = TenantNotificationSettingsDB(
        tenant_id=tenant_id,
        email=notification_config["email"],
        slack_webhook_url=notification_config.get("slack_webhook_url"),
        alerts_enabled=True,
        alert_triggers=",".join(notification_config["triggers"]),
        created_at=datetime.utcnow()
    )
    
    db.add(notifications)
    print(f"✓ Notifications configured")
    print(f"  - Email: {notification_config['email']}")
    if notification_config.get("slack_webhook_url"):
        print(f"  - Slack: enabled")
    print(f"  - Triggers: {', '.join(notification_config['triggers'])}")
    
    # Create audit log entry
    audit = DecisionAuditLogDB(
        tenant_id=tenant_id,
        txn_id=None,
        action="pilot_tenant_created",
        user_id="system",
        summary=f"Pilot tenant created: {config['name']}",
        metadata={
            "coa_template": config["coa_template"],
            "industry": config["industry"],
            "threshold": config["autopost_threshold"],
            "budget": config["llm_tenant_cap_usd"]
        },
        timestamp=datetime.utcnow()
    )
    
    db.add(audit)
    print(f"✓ Audit entry created")
    
    try:
        db.commit()
        print(f"✅ Pilot tenant {tenant_id} created successfully")
        return settings
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating tenant: {e}")
        raise


def main():
    """Create all pilot tenants."""
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Pilot Tenant Creation Script")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    db = SessionLocal()
    
    try:
        created_tenants = []
        
        for config in PILOT_CONFIGS:
            try:
                tenant = create_pilot_tenant(db, config)
                created_tenants.append(tenant)
            except Exception as e:
                print(f"⚠️  Failed to create {config['tenant_id']}: {e}")
                continue
        
        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"✅ Created {len(created_tenants)} pilot tenants")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        print("Next steps:")
        print("1. Verify tenants in database:")
        print("   SELECT * FROM tenant_settings WHERE tenant_id LIKE 'pilot-%';")
        print()
        print("2. Generate shadow reports:")
        print("   python3 scripts/generate_shadow_reports.py")
        print()
        print("3. Test notifications:")
        print("   python3 scripts/test_notifications.py")
        print()
        print("4. Capture screenshots:")
        print("   Follow SCREENSHOT_CAPTURE_GUIDE.md")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()

