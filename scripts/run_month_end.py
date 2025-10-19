#!/usr/bin/env python3
"""
Run month-end billing job with idempotency.

Posts usage records to Stripe for all subscriptions with positive overage.
Re-running is idempotent (won't double-bill).

Usage:
    python scripts/run_month_end.py [--dry-run]
"""
import sys
import os
from pathlib import Path
import argparse
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.session import get_db_context
from app.db.models import BillingSubscriptionDB, BillingEventDB
from app.services.usage_metering import UsageMeteringService


def run_month_end(dry_run: bool = False):
    """Run month-end billing with idempotency"""
    print(f"\n{'='*60}")
    print(f"MONTH-END BILLING JOB")
    print(f"{'='*60}")
    print(f"Time: {datetime.utcnow().isoformat()}Z")
    print(f"Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")
    print()
    
    with get_db_context() as db:
        service = UsageMeteringService(db)
        
        # Get all active subscriptions
        subscriptions = db.query(BillingSubscriptionDB).filter(
            BillingSubscriptionDB.status == "active"
        ).all()
        
        print(f"📊 Found {len(subscriptions)} active subscription(s)\n")
        
        results = {
            "total": len(subscriptions),
            "billed": 0,
            "no_overage": 0,
            "failed": 0,
            "total_amount": 0.0
        }
        
        for sub in subscriptions:
            print(f"Processing: {sub.tenant_id} (plan: {sub.plan})")
            
            # Get current usage
            from app.api.billing_v2 import PLAN_CONFIG
            plan_config = PLAN_CONFIG.get(sub.plan, {})
            quota = plan_config.get("transactions_monthly", 0)
            used = sub.metadata.get("tx_used_monthly", 0) if sub.metadata else 0
            overage_rate = plan_config.get("overage_rate", 0.0)
            overage = max(0, used - quota)
            overage_amount = overage * overage_rate
            
            print(f"  Quota: {quota}, Used: {used}, Overage: {overage} tx")
            print(f"  Amount: ${overage_amount:.2f}")
            
            if overage == 0:
                print(f"  ✅ No overage\n")
                results["no_overage"] += 1
                continue
            
            # Check if already billed this month
            current_month = datetime.utcnow().strftime("%Y-%m")
            idempotency_key = f"{sub.tenant_id}_{current_month}"
            
            existing_event = db.query(BillingEventDB).filter(
                BillingEventDB.tenant_id == sub.tenant_id,
                BillingEventDB.event_type == "overage_charged",
                BillingEventDB.metadata.contains({"month": current_month})
            ).first()
            
            if existing_event:
                print(f"  ⏭️  Already billed for {current_month} (idempotent)")
                print(f"  Event ID: {existing_event.id}\n")
                results["billed"] += 1
                results["total_amount"] += existing_event.amount
                continue
            
            if dry_run:
                print(f"  🔍 DRY RUN: Would bill ${overage_amount:.2f}\n")
                results["billed"] += 1
                results["total_amount"] += overage_amount
                continue
            
            # Bill overage
            success, error, amount = service.bill_monthly_overage(sub.tenant_id)
            
            if success:
                print(f"  ✅ Billed ${amount:.2f}\n")
                results["billed"] += 1
                results["total_amount"] += amount
            else:
                print(f"  ❌ Failed: {error}\n")
                results["failed"] += 1
        
        print(f"{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Total subscriptions: {results['total']}")
        print(f"Billed: {results['billed']}")
        print(f"No overage: {results['no_overage']}")
        print(f"Failed: {results['failed']}")
        print(f"Total amount: ${results['total_amount']:.2f}")
        print()
        
        if results['failed'] > 0:
            print(f"⚠️  {results['failed']} subscription(s) failed to bill")
            print("Check logs for details")
            return False
        
        print("✅ Month-end billing complete!")
        return True


def main():
    parser = argparse.ArgumentParser(description='Run month-end billing job')
    parser.add_argument('--dry-run', action='store_true',
                       help='Dry run mode (no actual billing)')
    
    args = parser.parse_args()
    
    try:
        success = run_month_end(dry_run=args.dry_run)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

