"""
Entitlement enforcement helpers.

Checks plan limits and returns 402 Payment Required when exceeded.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging

from app.db.models import EntitlementDB, UsageMonthlyDB
from config.stripe_plans import get_entitlements

logger = logging.getLogger(__name__)


class PlanLimitExceeded(HTTPException):
    """402 Payment Required - Plan limit exceeded."""
    
    def __init__(self, limit_type: str, current: int, max_allowed: int, plan: str):
        detail = {
            "error_code": "402_PLAN_LIMIT_REACHED",
            "message": f"Plan limit exceeded: {limit_type}",
            "limit_type": limit_type,
            "current_usage": current,
            "max_allowed": max_allowed,
            "current_plan": plan,
            "upgrade_url": f"{os.getenv('FRONTEND_URL', 'https://app.ai-bookkeeper.app')}/pricing",
            "hint": f"Upgrade to a higher plan to increase your {limit_type} limit"
        }
        super().__init__(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=detail)


def check_entity_limit(
    db: Session,
    tenant_id: str,
    current_entities: Optional[int] = None
) -> None:
    """
    Check if tenant has reached entity limit.
    
    Args:
        db: Database session
        tenant_id: Tenant identifier
        current_entities: Current entity count (optional, will query if not provided)
        
    Raises:
        PlanLimitExceeded (402) if limit reached
    """
    # Get entitlement
    entitlement = db.query(EntitlementDB).filter(
        EntitlementDB.tenant_id == tenant_id
    ).first()
    
    if not entitlement:
        # No entitlement = assume free tier with limit 1
        max_entities = 1
        plan = "free"
    else:
        max_entities = entitlement.included_companies
        plan = entitlement.plan
    
    # Get current entity count if not provided
    if current_entities is None:
        # Query from companies/entities table
        # For now, use a placeholder - would need actual query
        current_entities = 0  # TODO: Query actual entity count
    
    if current_entities >= max_entities:
        raise PlanLimitExceeded(
            limit_type="entities",
            current=current_entities,
            max_allowed=max_entities,
            plan=plan
        )


def check_monthly_transaction_limit(
    db: Session,
    tenant_id: str,
    increment_by: int = 0
) -> None:
    """
    Check if tenant has reached monthly transaction limit.
    
    Args:
        db: Database session
        tenant_id: Tenant identifier
        increment_by: Number of transactions about to be processed
        
    Raises:
        PlanLimitExceeded (402) if limit would be exceeded
    """
    # Get entitlement
    entitlement = db.query(EntitlementDB).filter(
        EntitlementDB.tenant_id == tenant_id
    ).first()
    
    if not entitlement:
        # No entitlement = assume free tier with limit 100
        max_transactions = 100
        plan = "free"
    else:
        max_transactions = entitlement.tx_cap
        plan = entitlement.plan
    
    # Get current month usage
    from datetime import datetime
    current_month = datetime.utcnow().strftime("%Y-%m")
    
    usage = db.query(UsageMonthlyDB).filter(
        UsageMonthlyDB.tenant_id == tenant_id,
        UsageMonthlyDB.month == current_month
    ).first()
    
    current_usage = 0
    if usage:
        # Assuming usage has a propose_count or transaction_count field
        current_usage = getattr(usage, "propose_count", 0)
    
    # Check if new transactions would exceed limit
    new_total = current_usage + increment_by
    
    if new_total > max_transactions:
        raise PlanLimitExceeded(
            limit_type="monthly_transactions",
            current=current_usage,
            max_allowed=max_transactions,
            plan=plan
        )


def check_bulk_approve_allowed(
    db: Session,
    tenant_id: str
) -> None:
    """
    Check if tenant's plan allows bulk approve.
    
    Args:
        db: Database session
        tenant_id: Tenant identifier
        
    Raises:
        PlanLimitExceeded (402) if feature not included in plan
    """
    entitlement = db.query(EntitlementDB).filter(
        EntitlementDB.tenant_id == tenant_id
    ).first()
    
    if not entitlement or not entitlement.bulk_approve:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error_code": "402_FEATURE_NOT_INCLUDED",
                "message": "Bulk approve is not included in your plan",
                "feature": "bulk_approve",
                "current_plan": entitlement.plan if entitlement else "free",
                "upgrade_url": f"{os.getenv('FRONTEND_URL', 'https://app.ai-bookkeeper.app')}/pricing",
                "hint": "Upgrade to Team or Firm plan for bulk approve"
            }
        )


def increment_usage(
    db: Session,
    tenant_id: str,
    event_type: str = "propose",
    count: int = 1
) -> None:
    """
    Increment usage counter for metering.
    
    Args:
        db: Database session
        tenant_id: Tenant identifier
        event_type: Type of event (propose, export, etc.)
        count: Number to increment by
    """
    from datetime import datetime
    
    current_month = datetime.utcnow().strftime("%Y-%m")
    
    # Get or create usage record
    usage = db.query(UsageMonthlyDB).filter(
        UsageMonthlyDB.tenant_id == tenant_id,
        UsageMonthlyDB.month == current_month
    ).first()
    
    if not usage:
        usage = UsageMonthlyDB(
            tenant_id=tenant_id,
            month=current_month,
            propose_count=0,
            export_count=0
        )
        db.add(usage)
    
    # Increment appropriate counter
    if event_type == "propose":
        usage.propose_count = (usage.propose_count or 0) + count
    elif event_type == "export":
        usage.export_count = (usage.export_count or 0) + count
    
    db.commit()
    
    logger.info(
        f"Usage incremented: tenant={tenant_id}, event={event_type}, count={count}"
    )


import os

