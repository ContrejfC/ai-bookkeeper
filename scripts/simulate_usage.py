#!/usr/bin/env python3
"""
Simulate usage for testing overage billing.

Creates a test tenant with Starter plan and processes 600 transactions
to verify overage calculation (100 tx over 500 quota = $3.00 at $0.03/tx).

Usage:
    python scripts/simulate_usage.py [--tenant-id TENANT_ID] [--count 600]
"""
import sys
import os
from pathlib import Path
import argparse
import uuid
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.session import get_db_context
from app.db.models import BillingSubscriptionDB
from app.services.usage_metering import UsageMeteringService


def create_test_subscription(db, tenant_id: str):
    """Create a test Starter subscription"""
    subscription = BillingSubscriptionDB(
        id=f"sub_test_{uuid.uuid4().hex[:8]}",
        tenant_id=tenant_id,
        stripe_customer_id=f"cus_test_{uuid.uuid4().hex[:8]}",
        stripe_subscription_id=f"sub_test_{uuid.uuid4().hex[:8]}",
        plan="starter",
        status="active",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow(),
        cancel_at_period_end=False,
        metadata={
            "tx_used_monthly": 0,
            "term": "monthly"
        },
        created_at=datetime.utcnow()
    )
    db.add(subscription)
    db.commit()
    return subscription


def simulate_transactions(tenant_id: str, count: int):
    """Simulate processing N transactions"""
    print(f"\n{'='*60}")
    print(f"USAGE SIMULATION")
    print(f"{'='*60}")
    print(f"Tenant ID: {tenant_id}")
    print(f"Transactions to process: {count}")
    print()
    
    with get_db_context() as db:
        service = UsageMeteringService(db)
        
        # Check if subscription exists
        subscription = db.query(BillingSubscriptionDB).filter(
            BillingSubscriptionDB.tenant_id == tenant_id,
            BillingSubscriptionDB.status == "active"
        ).first()
        
        if not subscription:
            print("⚠️  No active subscription found. Creating test subscription...")
            subscription = create_test_subscription(db, tenant_id)
            print(f"✅ Created test subscription: {subscription.id}")
        
        print(f"\n📊 Initial state:")
        quota, used, overage_rate = service.get_current_usage(tenant_id)
        print(f"   Plan: {subscription.plan}")
        print(f"   Quota: {quota} transactions/month")
        print(f"   Used: {used} transactions")
        print(f"   Overage rate: ${overage_rate}/tx")
        
        # Process transactions
        print(f"\n⚙️  Processing {count} transactions...")
        successes = 0
        failures = 0
        
        for i in range(count):
            tx_id = f"tx_sim_{uuid.uuid4().hex[:12]}"
            idempotency_key = f"idem_sim_{uuid.uuid4().hex[:12]}"
            
            success, error = service.increment_transaction_usage(
                tenant_id=tenant_id,
                transaction_id=tx_id,
                idempotency_key=idempotency_key
            )
            
            if success:
                successes += 1
                if (i + 1) % 100 == 0:
                    print(f"   Processed {i + 1}/{count} transactions...")
            else:
                failures += 1
                print(f"   ❌ Failed transaction {i + 1}: {error}")
        
        print(f"\n✅ Processing complete:")
        print(f"   Successes: {successes}")
        print(f"   Failures: {failures}")
        
        # Check final state
        quota, used, overage_rate = service.get_current_usage(tenant_id)
        overage = max(0, used - quota)
        overage_amount = overage * overage_rate
        
        print(f"\n📊 Final state:")
        print(f"   Quota: {quota} transactions/month")
        print(f"   Used: {used} transactions")
        print(f"   Overage: {overage} transactions")
        print(f"   Overage amount: ${overage_amount:.2f}")
        
        if subscription.plan == "starter" and count == 600:
            expected_overage = 100
            expected_amount = 3.00
            
            if overage == expected_overage and abs(overage_amount - expected_amount) < 0.01:
                print(f"\n✅ VERIFICATION PASSED")
                print(f"   Expected overage: 100 tx × $0.03 = $3.00")
                print(f"   Actual overage: {overage} tx × ${overage_rate} = ${overage_amount:.2f}")
            else:
                print(f"\n❌ VERIFICATION FAILED")
                print(f"   Expected: 100 tx × $0.03 = $3.00")
                print(f"   Got: {overage} tx × ${overage_rate} = ${overage_amount:.2f}")
                sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Simulate transaction usage for testing')
    parser.add_argument('--tenant-id', default=f'test_tenant_{uuid.uuid4().hex[:8]}',
                       help='Tenant ID (default: generates new ID)')
    parser.add_argument('--count', type=int, default=600,
                       help='Number of transactions to process (default: 600)')
    
    args = parser.parse_args()
    
    try:
        simulate_transactions(args.tenant_id, args.count)
        print(f"\n{'='*60}")
        print("✅ Simulation complete!")
        print(f"{'='*60}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

