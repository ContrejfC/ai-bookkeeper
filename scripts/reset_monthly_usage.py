#!/usr/bin/env python3
"""
Monthly usage reset job.

Run this on the first day of each month at 12:01 AM UTC.
Resets usage counters for all active subscriptions.

Cron: 1 0 1 * * /path/to/python /path/to/scripts/reset_monthly_usage.py
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
    """Reset monthly usage for all active subscriptions"""
    print("=" * 60)
    print("MONTHLY USAGE RESET JOB")
    print("=" * 60)
    
    try:
        with get_db_context() as db:
            service = UsageMeteringService(db)
            results = service.run_monthly_reset_job()
            
            print(f"\n✅ Reset complete:")
            print(f"   Total subscriptions reset: {results['total']}")
            print("\n✅ All subscriptions ready for new billing period")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ Error running reset job: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

