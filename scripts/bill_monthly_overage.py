#!/usr/bin/env python3
"""
Monthly overage billing job.

Run this on the last day of each month at 11:59 PM UTC.
Posts usage records to Stripe for all subscriptions with overage.

Cron: 59 23 28-31 * * /path/to/python /path/to/scripts/bill_monthly_overage.py
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.session import get_db_context
from app.services.usage_metering import UsageMeteringService


def main():
    """Run monthly billing for all active subscriptions"""
    print("=" * 60)
    print("MONTHLY OVERAGE BILLING JOB")
    print("=" * 60)
    
    try:
        with get_db_context() as db:
            service = UsageMeteringService(db)
            results = service.run_monthly_billing_job()
            
            print(f"\n✅ Billing complete:")
            print(f"   Total subscriptions: {results['total']}")
            print(f"   Successful: {results['success']}")
            print(f"   Failed: {results['failed']}")
            print(f"   Total billed: ${results['total_billed']:.2f}")
            
            if results['failed'] > 0:
                print(f"\n⚠️  {results['failed']} subscriptions failed to bill")
                print("   Check logs for details")
                sys.exit(1)
            
            print("\n✅ All subscriptions billed successfully")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ Error running billing job: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

