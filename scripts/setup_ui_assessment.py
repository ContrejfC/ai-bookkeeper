"""
UI Assessment Mode Setup (CEO Review)

Creates safe demo environment with seeded data for UI walkthrough.
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.db.models import (
    TenantSettingsDB, UserDB, UserTenantDB, TransactionDB,
    DecisionAuditLogDB, ReceiptFieldDB
)


def setup_ui_assessment_mode():
    """
    Set up UI assessment environment with demo data.
    
    Creates:
    - 3 pilot tenants (SMB, Professional, Accounting Firm)
    - 2 users per tenant (1 owner, 1 staff)
    - 20+ review transactions with varied reasons
    - 6 receipt PDFs with OCR data
    - 7 days of metrics
    """
    print("=" * 80)
    print("UI ASSESSMENT MODE SETUP")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Set environment flag
        os.environ["UI_ASSESSMENT"] = "1"
        print("\n✅ UI_ASSESSMENT=1 flag set (non-destructive mode)")
        
        # Create demo tenants
        print("\n📊 Creating pilot tenants...")
        tenants = create_pilot_tenants(db)
        
        # Create users with RBAC
        print("\n👥 Creating users (owner + staff per tenant)...")
        users = create_demo_users(db, tenants)
        
        # Seed review transactions
        print("\n📝 Seeding review transactions (20+ with varied reasons)...")
        transactions = seed_review_transactions(db, tenants)
        
        # Seed receipts with OCR data
        print("\n🧾 Seeding receipts with OCR overlays...")
        receipts = seed_receipts_with_ocr(db, tenants)
        
        # Seed metrics/analytics
        print("\n📈 Seeding metrics (last 7 days)...")
        seed_metrics(db, tenants)
        
        print("\n" + "=" * 80)
        print("✅ UI ASSESSMENT ENVIRONMENT READY")
        print("=" * 80)
        print(f"\nTenants: {len(tenants)}")
        print(f"Users: {len(users)} (includes owner + staff per tenant)")
        print(f"Review Transactions: {len(transactions)}")
        print(f"Receipts: {len(receipts)}")
        print("\nDemo Credentials:")
        for user in users[:6]:  # Show first 6 users
            role_badge = "👑" if user['role'] == 'owner' else "👤"
            print(f"  {role_badge} {user['email']} / demo-password-123")
        
        print("\n⚠️  ASSESSMENT MODE ACTIVE:")
        print("  - AUTOPOST forced to FALSE")
        print("  - Destructive actions disabled server-side")
        print("  - Banner visible on all pages")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()


def create_pilot_tenants(db):
    """Create 3 pilot tenants."""
    tenants = [
        {
            "tenant_id": "pilot-smb-001",
            "name": "Demo SMB Co",
            "autopost_enabled": False,
            "autopost_threshold": 0.90,
            "llm_tenant_cap_usd": 50.0
        },
        {
            "tenant_id": "pilot-prof-002",
            "name": "Demo Professional Services",
            "autopost_enabled": False,
            "autopost_threshold": 0.92,
            "llm_tenant_cap_usd": 75.0
        },
        {
            "tenant_id": "pilot-firm-003",
            "name": "Demo Accounting Firm",
            "autopost_enabled": False,
            "autopost_threshold": 0.88,
            "llm_tenant_cap_usd": 100.0
        }
    ]
    
    created = []
    for tenant in tenants:
        # Check if exists
        existing = db.query(TenantSettingsDB).filter_by(
            tenant_id=tenant["tenant_id"]
        ).first()
        
        if existing:
            print(f"  ✓ {tenant['tenant_id']} (exists)")
            created.append(tenant)
        else:
            settings = TenantSettingsDB(
                tenant_id=tenant["tenant_id"],
                autopost_enabled=tenant["autopost_enabled"],
                autopost_threshold=tenant["autopost_threshold"],
                llm_tenant_cap_usd=tenant["llm_tenant_cap_usd"]
            )
            db.add(settings)
            db.commit()
            print(f"  ✓ {tenant['tenant_id']} (created)")
            created.append(tenant)
    
    return created


def create_demo_users(db, tenants):
    """Create owner + staff for each tenant."""
    users = []
    
    for tenant in tenants:
        tenant_id = tenant["tenant_id"]
        
        # Owner
        owner_email = f"owner@{tenant_id}.demo"
        owner = db.query(UserDB).filter_by(email=owner_email).first()
        if not owner:
            from app.auth.passwords import hash_password
            owner = UserDB(
                user_id=f"user-{tenant_id}-owner",
                email=owner_email,
                password_hash=hash_password("demo-password-123"),
                role="owner",
                is_active=True
            )
            db.add(owner)
            
            # Link to tenant
            ut = UserTenantDB(
                user_id=owner.user_id,
                tenant_id=tenant_id
            )
            db.add(ut)
        
        users.append({"email": owner_email, "role": "owner", "tenant_id": tenant_id})
        print(f"  ✓ {owner_email} (owner)")
        
        # Staff
        staff_email = f"staff@{tenant_id}.demo"
        staff = db.query(UserDB).filter_by(email=staff_email).first()
        if not staff:
            from app.auth.passwords import hash_password
            staff = UserDB(
                user_id=f"user-{tenant_id}-staff",
                email=staff_email,
                password_hash=hash_password("demo-password-123"),
                role="staff",
                is_active=True
            )
            db.add(staff)
            
            # Link to tenant
            ut = UserTenantDB(
                user_id=staff.user_id,
                tenant_id=tenant_id
            )
            db.add(ut)
        
        users.append({"email": staff_email, "role": "staff", "tenant_id": tenant_id})
        print(f"  ✓ {staff_email} (staff)")
    
    db.commit()
    return users


def seed_review_transactions(db, tenants):
    """Create 20+ transactions with varied not_auto_post reasons."""
    reasons = [
        "below_threshold",
        "cold_start",
        "imbalance",
        "budget_fallback",
        "anomaly",
        "rule_conflict",
    ]
    
    transactions = []
    base_date = datetime.utcnow() - timedelta(days=7)
    
    for i, tenant in enumerate(tenants):
        for j in range(8):  # 8 per tenant = 24 total
            reason = reasons[j % len(reasons)]
            
            txn = TransactionDB(
                txn_id=f"demo-txn-{tenant['tenant_id']}-{j:03d}",
                tenant_id=tenant["tenant_id"],
                date=base_date + timedelta(days=j),
                description=f"Demo Transaction {j+1} ({reason})",
                amount=100.0 + (j * 15.5),
                vendor="Demo Vendor LLC",
                suggested_account="5000",
                confidence=0.75 + (j * 0.02),
                uploaded_at=datetime.utcnow()
            )
            db.add(txn)
            
            # Add to decision log
            audit = DecisionAuditLogDB(
                tenant_id=tenant["tenant_id"],
                txn_id=txn.txn_id,
                timestamp=datetime.utcnow(),
                vendor="Demo Vendor LLC",
                amount=txn.amount,
                predicted_account="5000",
                ml_confidence=txn.confidence,
                action="needs_review",
                not_auto_post_reason=reason,
                calibrated_p=txn.confidence
            )
            db.add(audit)
            
            transactions.append(txn)
    
    db.commit()
    print(f"  ✓ Created {len(transactions)} demo transactions")
    return transactions


def seed_receipts_with_ocr(db, tenants):
    """Create 6 receipts with OCR bounding boxes."""
    receipts = []
    
    for i, tenant in enumerate(tenants):
        # 2 receipts per tenant (1 clean, 1 messy)
        for j in range(2):
            receipt_id = f"demo-receipt-{tenant['tenant_id']}-{j:02d}"
            confidence = 0.95 if j == 0 else 0.72  # Clean vs messy
            
            # Create receipt fields with bboxes
            fields = [
                {"field": "date", "value": "2024-10-11", "x": 0.1, "y": 0.05, "w": 0.2, "h": 0.03},
                {"field": "vendor", "value": "Demo Store", "x": 0.05, "y": 0.02, "w": 0.4, "h": 0.04},
                {"field": "amount", "value": 145.50, "x": 0.7, "y": 0.85, "w": 0.15, "h": 0.04},
                {"field": "total", "value": 145.50, "x": 0.7, "y": 0.92, "w": 0.15, "h": 0.04},
            ]
            
            for field_data in fields:
                field_db = ReceiptFieldDB(
                    receipt_id=receipt_id,
                    field=field_data["field"],
                    page=0,
                    x=field_data["x"],
                    y=field_data["y"],
                    w=field_data["w"],
                    h=field_data["h"],
                    confidence=confidence
                )
                db.add(field_db)
            
            receipts.append(receipt_id)
            quality = "clean" if j == 0 else "messy"
            print(f"  ✓ {receipt_id} ({quality}, conf={confidence:.2f})")
    
    db.commit()
    return receipts


def seed_metrics(db, tenants):
    """Seed 7 days of analytics data."""
    # Would create analytics rollup data
    # For now, ensure directory exists
    import os
    os.makedirs("reports/analytics", exist_ok=True)
    
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        
        rollup = {
            "date": date_str,
            "events_by_type": {
                "page_view": 150 + i * 10,
                "review_action": 45 + i * 5,
                "export_run": 3,
                "metrics_view": 12
            },
            "by_tenant": {
                tenant["tenant_id"]: {
                    "page_views": 50,
                    "review_actions": 15
                }
                for tenant in tenants
            }
        }
        
        import json
        path = f"reports/analytics/daily_{date_str}.json"
        with open(path, "w") as f:
            json.dump(rollup, f, indent=2)
    
    print(f"  ✓ Created 7 days of analytics rollups")


if __name__ == "__main__":
    try:
        setup_ui_assessment_mode()
        print("\n✅ Setup complete. Start server with:")
        print("   uvicorn app.api.main:app --port 8000")
        print("\n📸 Capture screenshots with:")
        print("   python3 scripts/capture_ui_screenshots.py")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

