"""
Billing service for entitlement management and usage tracking.
"""

import os
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models import (
    EntitlementDB,
    UsageMonthlyDB,
    UsageDailyDB,
    TenantSettingsDB,
    BillingEventDB
)
from app.config.limits import (
    PLAN_FEATURES,
    FREE_DAILY_ANALYZE_CAP,
    FREE_DAILY_EXPLAIN_CAP,
    ERROR_CODES
)


class BillingService:
    """Service for managing billing entitlements and usage tracking."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_entitlement(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get active entitlement for tenant."""
        entitlement = self.db.query(EntitlementDB).filter(
            EntitlementDB.tenant_id == tenant_id
        ).first()
        
        if not entitlement:
            return None
        
        return {
            "active": entitlement.active,
            "plan": entitlement.plan,
            "tx_cap": entitlement.tx_cap,
            "bulk_approve": entitlement.bulk_approve,
            "included_companies": entitlement.included_companies,
            "trial_ends_at": entitlement.trial_ends_at.isoformat() if entitlement.trial_ends_at else None,
            "subscription_status": entitlement.subscription_status
        }
    
    def create_or_update_entitlement(
        self,
        tenant_id: str,
        plan: str,
        active: bool,
        subscription_status: str,
        trial_ends_at: Optional[datetime] = None
    ) -> EntitlementDB:
        """Create or update entitlement based on subscription."""
        
        # Get plan features
        features = PLAN_FEATURES.get(plan, PLAN_FEATURES["starter"])
        
        # Check for existing entitlement
        entitlement = self.db.query(EntitlementDB).filter(
            EntitlementDB.tenant_id == tenant_id
        ).first()
        
        if entitlement:
            # Update existing
            entitlement.plan = plan
            entitlement.active = active
            entitlement.tx_cap = features["tx_cap"]
            entitlement.bulk_approve = features["bulk_approve"]
            entitlement.included_companies = features["included_companies"]
            entitlement.trial_ends_at = trial_ends_at
            entitlement.subscription_status = subscription_status
            entitlement.updated_at = datetime.utcnow()
        else:
            # Create new
            entitlement = EntitlementDB(
                tenant_id=tenant_id,
                plan=plan,
                active=active,
                tx_cap=features["tx_cap"],
                bulk_approve=features["bulk_approve"],
                included_companies=features["included_companies"],
                trial_ends_at=trial_ends_at,
                subscription_status=subscription_status
            )
            self.db.add(entitlement)
        
        self.db.commit()
        self.db.refresh(entitlement)
        
        return entitlement
    
    def map_entitlement_from_price(
        self,
        tenant_id: str,
        price_id: str,
        price_metadata: Dict[str, str],
        subscription_status: str,
        trial_end: Optional[datetime] = None
    ) -> EntitlementDB:
        """Map Stripe price to entitlement using metadata."""
        
        # Extract plan from metadata
        plan = price_metadata.get("plan", "starter")
        tx_cap = int(price_metadata.get("tx_cap", "300"))
        bulk_approve = price_metadata.get("bulk_approve", "false").lower() == "true"
        included_companies = int(price_metadata.get("included_companies", "1"))
        
        # Determine if active based on subscription status
        active = subscription_status in ["active", "trialing"]
        
        # Check for existing entitlement
        entitlement = self.db.query(EntitlementDB).filter(
            EntitlementDB.tenant_id == tenant_id
        ).first()
        
        if entitlement:
            # Update existing
            entitlement.plan = plan
            entitlement.active = active
            entitlement.tx_cap = tx_cap
            entitlement.bulk_approve = bulk_approve
            entitlement.included_companies = included_companies
            entitlement.trial_ends_at = trial_end
            entitlement.subscription_status = subscription_status
            entitlement.updated_at = datetime.utcnow()
        else:
            # Create new
            entitlement = EntitlementDB(
                tenant_id=tenant_id,
                plan=plan,
                active=active,
                tx_cap=tx_cap,
                bulk_approve=bulk_approve,
                included_companies=included_companies,
                trial_ends_at=trial_end,
                subscription_status=subscription_status
            )
            self.db.add(entitlement)
        
        self.db.commit()
        self.db.refresh(entitlement)
        
        return entitlement
    
    def get_monthly_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get current month's usage for tenant."""
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        usage = self.db.query(UsageMonthlyDB).filter(
            and_(
                UsageMonthlyDB.tenant_id == tenant_id,
                UsageMonthlyDB.year_month == current_month
            )
        ).first()
        
        if not usage:
            # Create new usage record for this month
            usage = UsageMonthlyDB(
                tenant_id=tenant_id,
                year_month=current_month,
                tx_analyzed=0,
                tx_posted=0,
                last_reset_at=datetime.utcnow()
            )
            self.db.add(usage)
            self.db.commit()
            self.db.refresh(usage)
        
        return {
            "tx_analyzed": usage.tx_analyzed,
            "tx_posted": usage.tx_posted,
            "last_reset_at": usage.last_reset_at.isoformat()
        }
    
    def increment_analyzed(self, tenant_id: str, count: int = 1):
        """Increment analyzed transaction count."""
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        usage = self.db.query(UsageMonthlyDB).filter(
            and_(
                UsageMonthlyDB.tenant_id == tenant_id,
                UsageMonthlyDB.year_month == current_month
            )
        ).first()
        
        if not usage:
            usage = UsageMonthlyDB(
                tenant_id=tenant_id,
                year_month=current_month,
                tx_analyzed=count,
                tx_posted=0
            )
            self.db.add(usage)
        else:
            usage.tx_analyzed += count
            usage.updated_at = datetime.utcnow()
        
        self.db.commit()
    
    def increment_posted(self, tenant_id: str, count: int = 1):
        """Increment posted transaction count."""
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        usage = self.db.query(UsageMonthlyDB).filter(
            and_(
                UsageMonthlyDB.tenant_id == tenant_id,
                UsageMonthlyDB.year_month == current_month
            )
        ).first()
        
        if not usage:
            usage = UsageMonthlyDB(
                tenant_id=tenant_id,
                year_month=current_month,
                tx_analyzed=0,
                tx_posted=count
            )
            self.db.add(usage)
        else:
            usage.tx_posted += count
            usage.updated_at = datetime.utcnow()
        
        self.db.commit()
    
    def check_monthly_cap(self, tenant_id: str) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Check if tenant has exceeded monthly transaction cap."""
        entitlement = self.get_entitlement(tenant_id)
        if not entitlement or not entitlement["active"]:
            return False, ERROR_CODES["ENTITLEMENT_REQUIRED"]
        
        usage = self.get_monthly_usage(tenant_id)
        
        if usage["tx_posted"] >= entitlement["tx_cap"]:
            return False, ERROR_CODES["MONTHLY_CAP_EXCEEDED"]
        
        return True, None
    
    def get_daily_usage(self, tenant_id: str) -> Dict[str, int]:
        """Get today's usage for free tier limits."""
        today = date.today().isoformat()
        
        usage = self.db.query(UsageDailyDB).filter(
            and_(
                UsageDailyDB.tenant_id == tenant_id,
                UsageDailyDB.date == today
            )
        ).first()
        
        if not usage:
            # Create new usage record for today
            usage = UsageDailyDB(
                tenant_id=tenant_id,
                date=today,
                analyze_count=0,
                explain_count=0
            )
            self.db.add(usage)
            self.db.commit()
            self.db.refresh(usage)
        
        return {
            "analyze_count": usage.analyze_count,
            "explain_count": usage.explain_count
        }
    
    def increment_daily_analyze(self, tenant_id: str):
        """Increment daily analyze count for free tier."""
        today = date.today().isoformat()
        
        usage = self.db.query(UsageDailyDB).filter(
            and_(
                UsageDailyDB.tenant_id == tenant_id,
                UsageDailyDB.date == today
            )
        ).first()
        
        if not usage:
            usage = UsageDailyDB(
                tenant_id=tenant_id,
                date=today,
                analyze_count=1,
                explain_count=0
            )
            self.db.add(usage)
        else:
            usage.analyze_count += 1
            usage.updated_at = datetime.utcnow()
        
        self.db.commit()
    
    def increment_daily_explain(self, tenant_id: str):
        """Increment daily explain count for free tier."""
        today = date.today().isoformat()
        
        usage = self.db.query(UsageDailyDB).filter(
            and_(
                UsageDailyDB.tenant_id == tenant_id,
                UsageDailyDB.date == today
            )
        ).first()
        
        if not usage:
            usage = UsageDailyDB(
                tenant_id=tenant_id,
                date=today,
                analyze_count=0,
                explain_count=1
            )
            self.db.add(usage)
        else:
            usage.explain_count += 1
            usage.updated_at = datetime.utcnow()
        
        self.db.commit()
    
    def check_daily_analyze_cap(self, tenant_id: str) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Check if tenant has exceeded daily free analyze cap."""
        # If tenant has active subscription, skip free tier limits
        entitlement = self.get_entitlement(tenant_id)
        if entitlement and entitlement["active"]:
            return True, None
        
        usage = self.get_daily_usage(tenant_id)
        
        if usage["analyze_count"] >= FREE_DAILY_ANALYZE_CAP:
            return False, ERROR_CODES["FREE_CAP_EXCEEDED"]
        
        return True, None
    
    def check_daily_explain_cap(self, tenant_id: str) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Check if tenant has exceeded daily free explain cap."""
        # If tenant has active subscription, skip free tier limits
        entitlement = self.get_entitlement(tenant_id)
        if entitlement and entitlement["active"]:
            return True, None
        
        usage = self.get_daily_usage(tenant_id)
        
        if usage["explain_count"] >= FREE_DAILY_EXPLAIN_CAP:
            return False, ERROR_CODES["FREE_CAP_EXCEEDED"]
        
        return True, None
    
    def log_billing_event(
        self,
        event_type: str,
        stripe_event_id: str,
        payload: Dict[str, Any]
    ) -> BillingEventDB:
        """Log billing webhook event for audit trail."""
        
        # Check for duplicate event
        existing = self.db.query(BillingEventDB).filter(
            BillingEventDB.stripe_event_id == stripe_event_id
        ).first()
        
        if existing:
            return existing
        
        event = BillingEventDB(
            type=event_type,
            stripe_event_id=stripe_event_id,
            payload_json=payload,
            processed=True
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        return event
    
    def reset_monthly_usage(self, tenant_id: str):
        """Reset monthly usage counters (called at month start)."""
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        # Create new usage record for this month
        usage = UsageMonthlyDB(
            tenant_id=tenant_id,
            year_month=current_month,
            tx_analyzed=0,
            tx_posted=0,
            last_reset_at=datetime.utcnow()
        )
        
        self.db.add(usage)
        self.db.commit()
    
    def get_billing_status(self, tenant_id: str) -> Dict[str, Any]:
        """Get complete billing status for tenant."""
        entitlement = self.get_entitlement(tenant_id)
        usage = self.get_monthly_usage(tenant_id)
        daily_usage = self.get_daily_usage(tenant_id)
        
        return {
            "active": entitlement["active"] if entitlement else False,
            "plan": entitlement["plan"] if entitlement else None,
            "limits": {
                "tx_cap": entitlement["tx_cap"] if entitlement else 0,
                "bulk_approve": entitlement["bulk_approve"] if entitlement else False,
                "included_companies": entitlement["included_companies"] if entitlement else 1
            },
            "usage": {
                "tx_analyzed": usage["tx_analyzed"],
                "tx_posted": usage["tx_posted"],
                "daily_analyze": daily_usage["analyze_count"],
                "daily_explain": daily_usage["explain_count"]
            },
            "trial_ends_at": entitlement["trial_ends_at"] if entitlement else None,
            "subscription_status": entitlement["subscription_status"] if entitlement else None
        }

