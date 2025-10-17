#!/usr/bin/env python3
"""
Monthly usage rollover script.

Resets monthly usage counters at UTC month start.
Can be run manually or by cron/Render scheduler.

Usage:
    python scripts/roll_usage_month.py

Schedule:
    Run at 0 0 1 * * (UTC) - First day of each month at midnight
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_context
from app.db.models import UsageMonthlyDB, EntitlementDB


def rollover_monthly_usage():
    """Reset monthly usage counters for all tenants."""
    
    current_month = datetime.utcnow().strftime("%Y-%m")
    
    print(f"Starting monthly usage rollover for {current_month}...")
    
    with get_db_context() as db:
        # Get all active tenants with entitlements
        active_tenants = db.query(EntitlementDB).filter(
            EntitlementDB.active == True
        ).all()
        
        print(f"Found {len(active_tenants)} active tenants")
        
        for entitlement in active_tenants:
            tenant_id = entitlement.tenant_id
            
            # Check if usage record already exists for this month
            existing = db.query(UsageMonthlyDB).filter(
                UsageMonthlyDB.tenant_id == tenant_id,
                UsageMonthlyDB.year_month == current_month
            ).first()
            
            if existing:
                # Reset existing record
                existing.tx_analyzed = 0
                existing.tx_posted = 0
                existing.last_reset_at = datetime.utcnow()
                existing.updated_at = datetime.utcnow()
                print(f"  Reset usage for tenant {tenant_id}")
            else:
                # Create new record for this month
                new_usage = UsageMonthlyDB(
                    tenant_id=tenant_id,
                    year_month=current_month,
                    tx_analyzed=0,
                    tx_posted=0,
                    last_reset_at=datetime.utcnow()
                )
                db.add(new_usage)
                print(f"  Created new usage record for tenant {tenant_id}")
        
        # Commit all changes
        db.commit()
        print(f"\n✓ Monthly usage rollover completed for {current_month}")
        print(f"  Processed {len(active_tenants)} tenants")


def cleanup_old_usage():
    """Clean up usage records older than 12 months."""
    
    print("\nCleaning up old usage records...")
    
    with get_db_context() as db:
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=365)
        cutoff_month = cutoff_date.strftime("%Y-%m")
        
        # Delete records older than 12 months
        deleted = db.query(UsageMonthlyDB).filter(
            UsageMonthlyDB.year_month < cutoff_month
        ).delete()
        
        db.commit()
        print(f"  Deleted {deleted} old usage records (older than {cutoff_month})")


def main():
    """Main function."""
    try:
        rollover_monthly_usage()
        cleanup_old_usage()
        print("\n✓ All operations completed successfully")
        return 0
    except Exception as e:
        print(f"\n✗ Error during rollover: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

