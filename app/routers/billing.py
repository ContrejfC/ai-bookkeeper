"""
Billing API Router for Stripe integration.

Endpoints:
- GET /api/billing/status - Get billing status
- POST /api/billing/portal - Create Stripe billing portal session
- POST /api/billing/checkout - Create Stripe checkout session
- POST /api/billing/webhook - Handle Stripe webhooks
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
import stripe

from app.db.session import get_db
from app.services.billing import BillingService
from app.config.limits import PAYWALL_MD
from app.auth.jwt_handler import get_current_user
from sqlalchemy.orm import Session


router = APIRouter(prefix="/api/billing", tags=["billing"])

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


class BillingLimits(BaseModel):
    """Billing limits model."""
    tx_cap: int
    bulk_approve: bool = False
    included_companies: int = 1


class BillingUsage(BaseModel):
    """Billing usage model."""
    tx_analyzed: int
    tx_posted: int
    daily_analyze: int = 0
    daily_explain: int = 0


class BillingStatusResponse(BaseModel):
    """Billing status response."""
    active: bool
    plan: Optional[str] = None
    limits: BillingLimits
    usage: BillingUsage
    trial_ends_at: Optional[str] = None
    subscription_status: Optional[str] = None


class CheckoutRequest(BaseModel):
    """Checkout session request."""
    price_id: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


def get_tenant_id(request: Request, user: dict = Depends(get_current_user)) -> str:
    """Extract tenant ID from request state or user."""
    # Try request state first (set by middleware)
    tenant_id = getattr(request.state, "tenant_id", None)
    
    # Fallback to user tenants
    if not tenant_id and user:
        tenants = user.get("tenants", [])
        if tenants:
            tenant_id = tenants[0]
    
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: No tenant ID"
        )
    
    return tenant_id


@router.get("/status", response_model=BillingStatusResponse)
def get_billing_status(
    request: Request,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Get current plan, limits, and usage for tenant.
    
    This is the first Action call in any "post" flow for GPT paywall checks.
    """
    billing_service = BillingService(db)
    status_dict = billing_service.get_billing_status(tenant_id)
    
    return BillingStatusResponse(
        active=status_dict["active"],
        plan=status_dict["plan"],
        limits=BillingLimits(**status_dict["limits"]),
        usage=BillingUsage(**status_dict["usage"]),
        trial_ends_at=status_dict.get("trial_ends_at"),
        subscription_status=status_dict.get("subscription_status")
    )


@router.post("/portal")
def create_billing_portal(
    request: Request,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Create Stripe Billing Portal session URL for self-serve plan changes.
    
    Returns:
        {"url": "https://billing.stripe.com/session/..."}
    """
    billing_service = BillingService(db)
    
    # Get tenant's Stripe customer ID
    from app.db.models import TenantSettingsDB
    tenant_settings = db.query(TenantSettingsDB).filter(
        TenantSettingsDB.tenant_id == tenant_id
    ).first()
    
    if not tenant_settings or not tenant_settings.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No Stripe customer found. Please start a subscription first."
        )
    
    try:
        # Create billing portal session
        return_url = os.getenv("BILLING_RETURN_URL", f"{request.base_url}dashboard")
        
        session = stripe.billing_portal.Session.create(
            customer=tenant_settings.stripe_customer_id,
            return_url=return_url
        )
        
        return {"url": session.url}
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/checkout")
def create_checkout_session(
    checkout_request: CheckoutRequest,
    request: Request,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Create Stripe Checkout session for subscription signup.
    
    Args:
        price_id: Stripe price ID (e.g., price_...)
        success_url: Optional success redirect URL
        cancel_url: Optional cancel redirect URL
    
    Returns:
        {"url": "https://checkout.stripe.com/..."}
    """
    from app.db.models import TenantSettingsDB
    
    # Get or create Stripe customer
    tenant_settings = db.query(TenantSettingsDB).filter(
        TenantSettingsDB.tenant_id == tenant_id
    ).first()
    
    customer_id = None
    if tenant_settings and tenant_settings.stripe_customer_id:
        customer_id = tenant_settings.stripe_customer_id
    
    try:
        # Default URLs
        base_url = str(request.base_url).rstrip("/")
        success_url = checkout_request.success_url or f"{base_url}/dashboard?checkout=success"
        cancel_url = checkout_request.cancel_url or f"{base_url}/dashboard?checkout=cancel"
        
        # Create checkout session
        session_params = {
            "mode": "subscription",
            "line_items": [{
                "price": checkout_request.price_id,
                "quantity": 1
            }],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": {
                "tenant_id": tenant_id
            },
            "subscription_data": {
                "trial_period_days": 14,
                "metadata": {
                    "tenant_id": tenant_id
                }
            }
        }
        
        # Add customer if exists
        if customer_id:
            session_params["customer"] = customer_id
        else:
            # Let Stripe create customer and we'll capture it in webhook
            session_params["customer_creation"] = "always"
        
        session = stripe.checkout.Session.create(**session_params)
        
        return {"url": session.url}
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Stripe webhook receiver.
    
    Handles events:
    - checkout.session.completed
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_failed
    - customer.subscription.trial_will_end
    
    Updates entitlements based on subscription status and price metadata.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Webhook secret not configured"
        )
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    billing_service = BillingService(db)
    
    # Log the event
    billing_service.log_billing_event(
        event_type=event["type"],
        stripe_event_id=event["id"],
        payload=event
    )
    
    # Handle the event
    event_type = event["type"]
    
    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        tenant_id = session["metadata"].get("tenant_id")
        customer_id = session["customer"]
        subscription_id = session.get("subscription")
        
        if tenant_id and customer_id:
            # Update tenant with Stripe customer ID
            from app.db.models import TenantSettingsDB
            tenant_settings = db.query(TenantSettingsDB).filter(
                TenantSettingsDB.tenant_id == tenant_id
            ).first()
            
            if tenant_settings:
                tenant_settings.stripe_customer_id = customer_id
                if subscription_id:
                    tenant_settings.stripe_subscription_id = subscription_id
                db.commit()
    
    elif event_type in ["customer.subscription.created", "customer.subscription.updated"]:
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]
        subscription_id = subscription["id"]
        status_str = subscription["status"]
        
        # Get price metadata
        price_id = subscription["items"]["data"][0]["price"]["id"]
        price = stripe.Price.retrieve(price_id)
        price_metadata = price.get("metadata", {})
        
        # Find tenant by customer ID
        from app.db.models import TenantSettingsDB
        tenant_settings = db.query(TenantSettingsDB).filter(
            TenantSettingsDB.stripe_customer_id == customer_id
        ).first()
        
        if tenant_settings:
            tenant_id = tenant_settings.tenant_id
            
            # Update subscription ID
            tenant_settings.stripe_subscription_id = subscription_id
            db.commit()
            
            # Extract trial end
            trial_end = None
            if subscription.get("trial_end"):
                from datetime import datetime
                trial_end = datetime.fromtimestamp(subscription["trial_end"])
            
            # Map entitlement from price metadata
            billing_service.map_entitlement_from_price(
                tenant_id=tenant_id,
                price_id=price_id,
                price_metadata=price_metadata,
                subscription_status=status_str,
                trial_end=trial_end
            )
    
    elif event_type == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]
        
        # Find tenant and deactivate entitlement
        from app.db.models import TenantSettingsDB
        tenant_settings = db.query(TenantSettingsDB).filter(
            TenantSettingsDB.stripe_customer_id == customer_id
        ).first()
        
        if tenant_settings:
            tenant_id = tenant_settings.tenant_id
            
            # Deactivate entitlement
            from app.db.models import EntitlementDB
            entitlement = db.query(EntitlementDB).filter(
                EntitlementDB.tenant_id == tenant_id
            ).first()
            
            if entitlement:
                entitlement.active = False
                entitlement.subscription_status = "canceled"
                db.commit()
    
    elif event_type == "invoice.payment_failed":
        invoice = event["data"]["object"]
        customer_id = invoice["customer"]
        
        # Find tenant and mark subscription as past_due
        from app.db.models import TenantSettingsDB
        tenant_settings = db.query(TenantSettingsDB).filter(
            TenantSettingsDB.stripe_customer_id == customer_id
        ).first()
        
        if tenant_settings:
            tenant_id = tenant_settings.tenant_id
            
            # Update entitlement status
            from app.db.models import EntitlementDB
            entitlement = db.query(EntitlementDB).filter(
                EntitlementDB.tenant_id == tenant_id
            ).first()
            
            if entitlement:
                entitlement.active = False
                entitlement.subscription_status = "past_due"
                db.commit()
    
    elif event_type == "customer.subscription.trial_will_end":
        # Optional: Send notification to user
        # This event fires 3 days before trial ends
        pass
    
    return JSONResponse({"received": True})

