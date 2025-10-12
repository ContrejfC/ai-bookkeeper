#!/usr/bin/env python3
"""
Seed demo data for UI assessment.

Creates demo users, tenants, and transactions covering all decision reasons:
- below_threshold
- cold_start
- imbalance
- budget_fallback
- anomaly
- rule_conflict
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import engine
from app.db.models import (
    Base, UserDB, UserTenantDB, TenantSettingsDB, TransactionDB,
    JournalEntryDB, DecisionAuditLogDB, ColdStartTrackingDB
)
from app.auth.passwords import hash_password
import json
import uuid


def seed_demo_data():
    """Seed comprehensive demo data."""
    print("🌱 Seeding demo data...")
    
    # Create tables
    Base.metadata.create_all(engine)
    
    with Session(engine) as db:
        # 1. Create demo tenant
        tenant_id = "pilot-smb-001"
        
        # Create tenant settings
        tenant_settings = db.query(TenantSettingsDB).filter_by(tenant_id=tenant_id).first()
        if not tenant_settings:
            tenant_settings = TenantSettingsDB(
                tenant_id=tenant_id,
                autopost_enabled=False,  # Assessment mode
                autopost_threshold=0.90,
                llm_tenant_cap_usd=50.0,
                updated_by="system"
            )
            db.add(tenant_settings)
            print(f"✅ Created tenant: {tenant_id}")
        
        # 2. Create demo users
        owner_email = "owner@pilot-smb-001.demo"
        staff_email = "staff@pilot-smb-001.demo"
        password = "demo-password-123"
        
        # Owner user
        owner = db.query(UserDB).filter_by(email=owner_email).first()
        if not owner:
            owner = UserDB(
                user_id=str(uuid.uuid4()),
                email=owner_email,
                password_hash=hash_password(password),
                role="owner",
                is_active=True
            )
            db.add(owner)
            print(f"✅ Created owner: {owner_email}")
        
        # Staff user
        staff = db.query(UserDB).filter_by(email=staff_email).first()
        if not staff:
            staff = UserDB(
                user_id=str(uuid.uuid4()),
                email=staff_email,
                password_hash=hash_password(password),
                role="staff",
                is_active=True
            )
            db.add(staff)
            print(f"✅ Created staff: {staff_email}")
        
        db.commit()
        
        # 3. Link users to tenant
        for user in [owner, staff]:
            link = db.query(UserTenantDB).filter_by(
                user_id=user.user_id,
                tenant_id=tenant_id
            ).first()
            if not link:
                db.add(UserTenantDB(
                    user_id=user.user_id,
                    tenant_id=tenant_id
                ))
        
        db.commit()
        print(f"✅ Linked users to tenant")
        
        # 4. Create transactions covering all decision reasons
        base_date = datetime.now() - timedelta(days=30)
        
        reasons = [
            ("below_threshold", "Starbucks", 15.50, 0.85, "Meals & Entertainment"),
            ("cold_start", "New Vendor LLC", 250.00, 0.92, "Office Supplies"),
            ("imbalance", "Consulting Co", 5000.00, 0.95, "Professional Fees"),
            ("budget_fallback", "AWS Services", 1200.00, 0.93, "Cloud Services"),
            ("anomaly", "Unusual Vendor XYZ", 9999.99, 0.88, "Miscellaneous"),
            ("rule_conflict", "Multi-Category Inc", 450.00, 0.91, "Multiple"),
            ("below_threshold", "Office Depot", 45.00, 0.88, "Office Supplies"),
            ("cold_start", "Another New Vendor", 100.00, 0.90, "Utilities"),
        ]
        
        for i, (reason, vendor, amount, confidence, account) in enumerate(reasons):
            txn_id = f"demo-txn-{i+1:03d}"
            
            # Check if transaction exists
            if not db.query(TransactionDB).filter_by(txn_id=txn_id).first():
                # Create transaction
                txn = TransactionDB(
                    txn_id=txn_id,
                    date=base_date + timedelta(days=i),
                    amount=amount,
                    currency="USD",
                    description=f"Payment to {vendor}",
                    counterparty=vendor,
                    raw=json.dumps({"vendor": vendor, "memo": f"Demo {reason}"}),
                    doc_ids=json.dumps([])
                )
                db.add(txn)
                
                # Create journal entry
                je = JournalEntryDB(
                    je_id=f"demo-je-{i+1:03d}",
                    date=txn.date,
                    lines=json.dumps([
                        {"account": account, "debit": amount, "credit": 0},
                        {"account": "Cash", "debit": 0, "credit": amount}
                    ]),
                    source_txn_id=txn_id,
                    memo=f"{vendor} - {reason}",
                    confidence=confidence,
                    status="needs_review",
                    needs_review=1
                )
                db.add(je)
                
                # Create decision audit log
                audit = DecisionAuditLogDB(
                    tenant_id=tenant_id,
                    txn_id=txn_id,
                    vendor_normalized=vendor.lower(),
                    action="review",
                    not_auto_post_reason=reason,
                    calibrated_p=confidence,
                    threshold_used=0.90,
                    cold_start_label_count=1 if reason == "cold_start" else 5,
                    cold_start_eligible=(reason == "cold_start")
                )
                db.add(audit)
                
                # Add cold start tracking for new vendors
                if reason == "cold_start":
                    cold_start = ColdStartTrackingDB(
                        tenant_id=tenant_id,
                        vendor_normalized=vendor.lower(),
                        suggested_account=account,
                        label_count=1,
                        consistent=True
                    )
                    db.add(cold_start)
        
        db.commit()
        print(f"✅ Created {len(reasons)} demo transactions with reason coverage")
        
        print("\n🎉 Demo data seeded successfully!")
        print(f"\n📋 Demo Credentials:")
        print(f"   Owner: {owner_email} / {password}")
        print(f"   Staff: {staff_email} / {password}")
        print(f"\n🏢 Tenant: {tenant_id}")
        print(f"   AUTOPOST: {tenant_settings.autopost_enabled}")
        print(f"   Threshold: {tenant_settings.autopost_threshold}")


if __name__ == "__main__":
    seed_demo_data()

