"""
Usage metering service for transaction tracking and overage billing.

A billable transaction is defined as a bank/card line ingested and processed
through the propose endpoint. Idempotent retries and re-exports are NOT billed.

Monthly quota resets on the first day of each calendar month.
Overage is calculated and billed at month end via Stripe usage records.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("Stripe not installed for usage metering")


class UsageMeteringService:
    """Service for tracking and billing transaction usage"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def increment_transaction_usage(
        self,
        tenant_id: str,
        transaction_id: str,
        idempotency_key: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Increment transaction usage for tenant.
        
        Args:
            tenant_id: Tenant ID
            transaction_id: Transaction ID
            idempotency_key: Optional idempotency key to prevent double billing
        
        Returns:
            (success, error_message)
        """
        from app.db.models import BillingSubscriptionDB
        
        # Check if this is a retry (idempotent request)
        if idempotency_key:
            # Check if we've seen this key before
            # In production, use Redis or a dedicated idempotency table
            existing = self.db.query(BillingSubscriptionDB).filter(
                BillingSubscriptionDB.tenant_id == tenant_id,
                BillingSubscriptionDB.metadata.contains({"idempotency_keys": [idempotency_key]})
            ).first()
            
            if existing:
                logger.info(f"Idempotent retry detected for {idempotency_key}, not billing")
                return True, None
        
        # Get active subscription
        subscription = self.db.query(BillingSubscriptionDB).filter(
            BillingSubscriptionDB.tenant_id == tenant_id,
            BillingSubscriptionDB.status == "active"
        ).first()
        
        if not subscription:
            return False, "No active subscription"
        
        # Increment usage counter
        if not subscription.metadata:
            subscription.metadata = {}
        
        current_usage = subscription.metadata.get("tx_used_monthly", 0)
        subscription.metadata["tx_used_monthly"] = current_usage + 1
        
        # Track idempotency key
        if idempotency_key:
            keys = subscription.metadata.get("idempotency_keys", [])
            keys.append(idempotency_key)
            # Keep only last 1000 keys to prevent unbounded growth
            subscription.metadata["idempotency_keys"] = keys[-1000:]
        
        # Mark as modified for SQLAlchemy
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(subscription, "metadata")
        
        self.db.commit()
        
        logger.info(f"Incremented usage for {tenant_id}: {current_usage + 1} transactions")
        return True, None
    
    def get_current_usage(self, tenant_id: str) -> Tuple[int, int, float]:
        """
        Get current usage for tenant.
        
        Returns:
            (quota, used, overage_rate)
        """
        from app.db.models import BillingSubscriptionDB
        from app.api.billing_v2 import PLAN_CONFIG
        
        subscription = self.db.query(BillingSubscriptionDB).filter(
            BillingSubscriptionDB.tenant_id == tenant_id,
            BillingSubscriptionDB.status == "active"
        ).first()
        
        if not subscription:
            return 0, 0, 0.0
        
        plan_config = PLAN_CONFIG.get(subscription.plan, {})
        quota = plan_config.get("transactions_monthly", 0)
        used = subscription.metadata.get("tx_used_monthly", 0) if subscription.metadata else 0
        overage_rate = plan_config.get("overage_rate", 0.0)
        
        return quota, used, overage_rate
    
    def check_quota(self, tenant_id: str) -> Tuple[bool, Optional[dict]]:
        """
        Check if tenant is within quota.
        
        Returns:
            (allowed, error_dict)
        """
        quota, used, overage_rate = self.get_current_usage(tenant_id)
        
        if quota == 0:
            return False, {
                "error": "no_subscription",
                "message": "No active subscription",
                "http_status": 402
            }
        
        # Allow overage (will be billed at month end)
        # But optionally enforce hard limits here if needed
        if used >= quota * 2:  # Hard limit at 2x quota
            return False, {
                "error": "quota_exceeded",
                "message": f"Transaction quota exceeded. Used: {used}, Quota: {quota}",
                "http_status": 402,
                "used": used,
                "quota": quota
            }
        
        return True, None
    
    def reset_monthly_usage(self, tenant_id: str) -> bool:
        """
        Reset monthly usage counter (called on first of month).
        
        Returns:
            success
        """
        from app.db.models import BillingSubscriptionDB
        
        subscription = self.db.query(BillingSubscriptionDB).filter(
            BillingSubscriptionDB.tenant_id == tenant_id,
            BillingSubscriptionDB.status == "active"
        ).first()
        
        if not subscription:
            return False
        
        if not subscription.metadata:
            subscription.metadata = {}
        
        # Archive last month's usage
        subscription.metadata["tx_used_last_month"] = subscription.metadata.get("tx_used_monthly", 0)
        subscription.metadata["tx_used_monthly"] = 0
        subscription.metadata["idempotency_keys"] = []  # Clear idempotency keys
        
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(subscription, "metadata")
        
        self.db.commit()
        
        logger.info(f"Reset monthly usage for {tenant_id}")
        return True
    
    def bill_monthly_overage(self, tenant_id: str) -> Tuple[bool, Optional[str], float]:
        """
        Bill monthly overage to Stripe (called at month end).
        
        Returns:
            (success, error_message, amount_billed)
        """
        if not STRIPE_AVAILABLE:
            return False, "Stripe not available", 0.0
        
        from app.db.models import BillingSubscriptionDB, BillingEventDB
        from app.api.billing_v2 import PLAN_CONFIG, STRIPE_PRICES
        
        subscription = self.db.query(BillingSubscriptionDB).filter(
            BillingSubscriptionDB.tenant_id == tenant_id,
            BillingSubscriptionDB.status == "active"
        ).first()
        
        if not subscription:
            return False, "No active subscription", 0.0
        
        plan_config = PLAN_CONFIG.get(subscription.plan, {})
        quota = plan_config.get("transactions_monthly", 0)
        used = subscription.metadata.get("tx_used_monthly", 0) if subscription.metadata else 0
        overage_rate = plan_config.get("overage_rate", 0.0)
        
        overage = max(0, used - quota)
        
        if overage == 0:
            logger.info(f"No overage for {tenant_id}")
            return True, None, 0.0
        
        overage_amount = overage * overage_rate
        
        try:
            # Get subscription item for metered usage
            stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            
            # Find the metered price item
            metered_item_id = None
            overage_price_id = STRIPE_PRICES.get(f"overage_{subscription.plan}")
            
            for item in stripe_subscription["items"]["data"]:
                if item["price"]["id"] == overage_price_id:
                    metered_item_id = item["id"]
                    break
            
            if not metered_item_id:
                return False, "No metered price item found in subscription", 0.0
            
            # Create usage record
            stripe.SubscriptionItem.create_usage_record(
                metered_item_id,
                quantity=overage,
                timestamp=int(datetime.utcnow().timestamp()),
                action="set"  # Set total usage for the period
            )
            
            # Record billing event
            billing_event = BillingEventDB(
                id=f"evt_overage_{datetime.utcnow().timestamp()}",
                tenant_id=tenant_id,
                event_type="overage_charged",
                amount=overage_amount,
                currency="usd",
                metadata={
                    "overage_units": overage,
                    "overage_rate": overage_rate,
                    "quota": quota,
                    "used": used
                },
                created_at=datetime.utcnow()
            )
            self.db.add(billing_event)
            self.db.commit()
            
            logger.info(f"Billed overage for {tenant_id}: {overage} transactions = ${overage_amount}")
            return True, None, overage_amount
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error billing overage: {str(e)}")
            return False, str(e), 0.0
    
    def run_monthly_billing_job(self):
        """
        Run monthly billing job for all active subscriptions.
        Should be run via cron/scheduler on last day of month.
        """
        from app.db.models import BillingSubscriptionDB
        
        logger.info("Starting monthly billing job")
        
        subscriptions = self.db.query(BillingSubscriptionDB).filter(
            BillingSubscriptionDB.status == "active"
        ).all()
        
        results = {
            "total": len(subscriptions),
            "success": 0,
            "failed": 0,
            "total_billed": 0.0
        }
        
        for sub in subscriptions:
            success, error, amount = self.bill_monthly_overage(sub.tenant_id)
            if success:
                results["success"] += 1
                results["total_billed"] += amount
            else:
                results["failed"] += 1
                logger.error(f"Failed to bill {sub.tenant_id}: {error}")
        
        logger.info(f"Monthly billing complete: {results}")
        return results
    
    def run_monthly_reset_job(self):
        """
        Run monthly reset job for all active subscriptions.
        Should be run via cron/scheduler on first day of month.
        """
        from app.db.models import BillingSubscriptionDB
        
        logger.info("Starting monthly reset job")
        
        subscriptions = self.db.query(BillingSubscriptionDB).filter(
            BillingSubscriptionDB.status == "active"
        ).all()
        
        for sub in subscriptions:
            self.reset_monthly_usage(sub.tenant_id)
        
        logger.info(f"Reset monthly usage for {len(subscriptions)} subscriptions")
        return {"total": len(subscriptions)}

