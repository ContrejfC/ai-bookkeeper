#!/usr/bin/env python3
"""
Seed default entitlements/plans into the database.

This script is idempotent - running it multiple times is safe.
It will create missing plans or update existing ones.

Usage:
    python scripts/seed_entitlements.py
    python scripts/seed_entitlements.py --reset  # Recreate all plans
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, EntitlementDB
from config.stripe_plans import load_stripe_plans, get_entitlements


def seed_default_entitlements(db_session, reset=False):
    """
    Seed default entitlements based on stripe_price_map.json.
    
    Args:
        db_session: SQLAlchemy session
        reset: If True, delete existing entitlements first
    """
    
    if reset:
        print("🗑️  Resetting existing entitlements...")
        db_session.query(EntitlementDB).delete()
        db_session.commit()
    
    # Load plan configurations
    plans_config = load_stripe_plans()
    plans = plans_config.get("plans", {})
    
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    # Create a default tenant for demo/testing if none exists
    # (In production, entitlements are created per tenant via billing webhooks)
    demo_tenants = [
        {
            "tenant_id": "tenant_demo_starter",
            "plan": "starter",
            "display_name": "Demo Starter Account"
        },
        {
            "tenant_id": "tenant_demo_team",
            "plan": "team",
            "display_name": "Demo Team Account"
        },
        {
            "tenant_id": "tenant_demo_firm",
            "plan": "firm",
            "display_name": "Demo Firm Account"
        }
    ]
    
    for demo_tenant in demo_tenants:
        tenant_id = demo_tenant["tenant_id"]
        plan_code = demo_tenant["plan"]
        
        # Get entitlement config for this plan
        plan_config = plans.get(plan_code)
        if not plan_config:
            print(f"⚠️  Warning: Plan '{plan_code}' not found in config, skipping")
            skipped_count += 1
            continue
        
        entitlements_config = plan_config.get("entitlements", {})
        
        # Check if entitlement exists
        existing = db_session.query(EntitlementDB).filter(
            EntitlementDB.tenant_id == tenant_id
        ).first()
        
        if existing:
            # Update existing
            existing.plan = plan_code
            existing.active = True
            existing.tx_cap = entitlements_config.get("monthly_tx_cap", 2000)
            existing.bulk_approve = "bulk_approve" in entitlements_config.get("features", [])
            existing.included_companies = entitlements_config.get("entity_limit", 1)
            existing.trial_ends_at = None  # No trial for demo accounts
            existing.subscription_status = "active"
            existing.updated_at = datetime.utcnow()
            
            print(f"✅ Updated entitlement for {demo_tenant['display_name']} ({plan_code})")
            updated_count += 1
        else:
            # Create new
            entitlement = EntitlementDB(
                tenant_id=tenant_id,
                plan=plan_code,
                active=True,
                tx_cap=entitlements_config.get("monthly_tx_cap", 2000),
                bulk_approve="bulk_approve" in entitlements_config.get("features", []),
                included_companies=entitlements_config.get("entity_limit", 1),
                trial_ends_at=None,
                subscription_status="active"
            )
            db_session.add(entitlement)
            
            print(f"✅ Created entitlement for {demo_tenant['display_name']} ({plan_code})")
            created_count += 1
    
    # Commit all changes
    db_session.commit()
    
    print()
    print("━" * 60)
    print(f"📊 Summary:")
    print(f"   Created:  {created_count}")
    print(f"   Updated:  {updated_count}")
    print(f"   Skipped:  {skipped_count}")
    print("━" * 60)


def main():
    parser = argparse.ArgumentParser(description="Seed default entitlements")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing entitlements before seeding"
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="Database URL (overrides DATABASE_URL env var)"
    )
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ Error: DATABASE_URL not set")
        print("   Set it in your environment or pass --database-url")
        sys.exit(1)
    
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  🌱 AI Bookkeeper - Seed Entitlements".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    print(f"📦 Database: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    print()
    
    if args.reset:
        print("⚠️  WARNING: --reset flag set. All existing entitlements will be deleted!")
        confirm = input("   Type 'yes' to continue: ")
        if confirm.lower() != "yes":
            print("❌ Aborted")
            sys.exit(0)
        print()
    
    # Create engine and session
    try:
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Run seed
        seed_default_entitlements(db, reset=args.reset)
        
        db.close()
        
        print()
        print("✅ Entitlements seeded successfully!")
        print()
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()

