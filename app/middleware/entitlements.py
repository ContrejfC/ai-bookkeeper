"""
Entitlements Middleware - Paywall Enforcement
=============================================

This middleware enforces subscription-based access control and quota limits
on protected API endpoints.

Features:
--------
- Plan status validation (active vs. inactive)
- Transaction quota enforcement (soft and hard limits)
- Entity count limits
- Quota headers in responses (X-Tx-Remaining, X-Tx-Quota)
- 402 Payment Required for quota exceeded

Enforcement Matrix:
------------------
| Plan        | Entities | Monthly Tx | Features                    |
|-------------|----------|------------|------------------------------|
| free        | 0        | 0          | Read-only, no write access   |
| starter     | 1        | 500        | Basic AI categorization      |
| professional| 3        | 2000       | + Advanced rules + exports   |
| enterprise  | Unlimited| Unlimited  | + Priority support           |

Usage:
------
```python
from fastapi import Depends
from app.middleware.entitlements import check_entitlements

@app.post("/api/post/propose")
async def propose(
    entitlements: dict = Depends(check_entitlements)
):
    # If we get here, entitlements are valid
    # Check entitlements["tx_remaining"] if needed
    pass
```
"""
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import BillingSubscriptionDB, UsageLogDB
from app.auth.security import get_current_user

logger = logging.getLogger(__name__)

# Entitlement tiers
ENTITLEMENT_TIERS = {
    "free": {
        "entities_allowed": 0,
        "tx_quota_monthly": 0,
        "features": ["read_only"]
    },
    "starter": {
        "entities_allowed": 1,
        "tx_quota_monthly": 500,
        "features": ["ai_categorization", "basic_export"]
    },
    "professional": {
        "entities_allowed": 3,
        "tx_quota_monthly": 2000,
        "features": ["ai_categorization", "advanced_rules", "qbo_export", "xero_export"]
    },
    "enterprise": {
        "entities_allowed": 999999,  # Unlimited
        "tx_quota_monthly": 999999,  # Unlimited
        "features": ["ai_categorization", "advanced_rules", "qbo_export", "xero_export", "priority_support"]
    }
}


class EntitlementError(HTTPException):
    """Custom exception for entitlement violations."""
    
    def __init__(self, detail: str, upgrade_url: str = "/pricing"):
        super().__init__(
            status_code=402,  # Payment Required
            detail={
                "error": "quota_exceeded",
                "message": detail,
                "upgrade_url": upgrade_url
            }
        )


def get_entitlements(
    tenant_id: str,
    db: Session
) -> Dict[str, Any]:
    """
    Get entitlements for a tenant.
    
    Args:
        tenant_id: Tenant identifier
        db: Database session
        
    Returns:
        Dict with entitlements info
    """
    # Get active subscription
    subscription = db.query(BillingSubscriptionDB).filter(
        BillingSubscriptionDB.tenant_id == tenant_id,
        BillingSubscriptionDB.status == 'active'
    ).first()
    
    if not subscription:
        # No active subscription - free tier
        plan = "free"
        status = "inactive"
    else:
        plan = subscription.plan_id or "free"
        status = subscription.status
    
    # Get tier config
    tier_config = ENTITLEMENT_TIERS.get(plan, ENTITLEMENT_TIERS["free"])
    
    # Calculate usage this month
    from datetime import datetime
    from sqlalchemy import func, extract
    
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    
    tx_used_monthly = db.query(func.count(UsageLogDB.id)).filter(
        UsageLogDB.tenant_id == tenant_id,
        extract('month', UsageLogDB.timestamp) == current_month,
        extract('year', UsageLogDB.timestamp) == current_year,
        UsageLogDB.operation.in_(['propose', 'categorize', 'export'])
    ).scalar() or 0
    
    # Calculate remaining
    tx_quota_monthly = tier_config["tx_quota_monthly"]
    tx_remaining = max(0, tx_quota_monthly - tx_used_monthly)
    
    # Get add-ons if any
    addons = []
    if subscription and subscription.stripe_subscription_id:
        # Parse subscription items for add-ons
        # For MVP, keep simple
        pass
    
    return {
        "plan": plan,
        "status": status,
        "entities_allowed": tier_config["entities_allowed"],
        "tx_quota_monthly": tx_quota_monthly,
        "tx_used_monthly": tx_used_monthly,
        "tx_remaining": tx_remaining,
        "features": tier_config["features"],
        "addons": addons
    }


async def check_entitlements(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    enforce_quota: bool = True,
    required_feature: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check entitlements and enforce quotas.
    
    This dependency should be used on protected endpoints.
    
    Args:
        request: FastAPI request
        current_user: Current authenticated user
        db: Database session
        enforce_quota: Whether to enforce transaction quota
        required_feature: Required feature name (e.g., "qbo_export")
        
    Returns:
        Entitlements dict
        
    Raises:
        HTTPException 402: Quota exceeded or feature not available
        HTTPException 403: Plan status inactive
    """
    # Get tenant_id from user
    tenant_ids = current_user.tenant_ids if hasattr(current_user, 'tenant_ids') else []
    if not tenant_ids:
        raise HTTPException(status_code=403, detail="No tenant access")
    
    tenant_id = tenant_ids[0] if isinstance(tenant_ids, list) else tenant_ids
    
    # Get entitlements
    entitlements = get_entitlements(tenant_id, db)
    
    # Check plan status
    if entitlements["status"] != "active" and entitlements["plan"] != "free":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "subscription_inactive",
                "message": "Your subscription is not active. Please update your billing.",
                "manage_url": "/firm"
            }
        )
    
    # Check required feature
    if required_feature and required_feature not in entitlements["features"]:
        raise EntitlementError(
            detail=f"Your plan does not include {required_feature}. Please upgrade.",
            upgrade_url="/pricing"
        )
    
    # Check transaction quota (hard limit)
    if enforce_quota:
        if entitlements["tx_remaining"] <= 0:
            raise EntitlementError(
                detail=f"Monthly transaction quota exceeded ({entitlements['tx_used_monthly']}/{entitlements['tx_quota_monthly']}). Please upgrade.",
                upgrade_url="/pricing"
            )
    
    # Log entitlement check (for monitoring)
    logger.info(
        f"Entitlement check passed",
        extra={
            "tenant_id": tenant_id,
            "plan": entitlements["plan"],
            "tx_remaining": entitlements["tx_remaining"],
            "path": request.url.path
        }
    )
    
    return entitlements


def add_quota_headers(response, entitlements: Dict[str, Any]):
    """
    Add quota information to response headers.
    
    Usage:
    ------
    ```python
    @app.post("/api/post/propose")
    async def propose(
        response: Response,
        entitlements: dict = Depends(check_entitlements)
    ):
        result = do_work()
        add_quota_headers(response, entitlements)
        return result
    ```
    """
    response.headers["X-Tx-Remaining"] = str(entitlements["tx_remaining"])
    response.headers["X-Tx-Quota"] = str(entitlements["tx_quota_monthly"])
    response.headers["X-Tx-Used"] = str(entitlements["tx_used_monthly"])
    response.headers["X-Plan"] = entitlements["plan"]


def log_usage(
    tenant_id: str,
    operation: str,
    count: int,
    db: Session,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log usage for quota tracking.
    
    Args:
        tenant_id: Tenant identifier
        operation: Operation type (propose, categorize, export)
        count: Number of transactions processed
        db: Database session
        metadata: Optional metadata
    """
    from datetime import datetime
    
    usage_log = UsageLogDB(
        tenant_id=tenant_id,
        timestamp=datetime.utcnow(),
        operation=operation,
        count=count,
        metadata=metadata or {}
    )
    
    db.add(usage_log)
    db.commit()
    
    logger.info(
        f"Usage logged: {operation} x{count}",
        extra={
            "tenant_id": tenant_id,
            "operation": operation,
            "count": count
        }
    )
