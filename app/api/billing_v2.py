"""
Enhanced Billing API with complete Stripe integration for ad-ready pricing.

Endpoints:
- POST /api/billing/checkout - Create checkout session
- GET /api/billing/status - Get billing status
- POST /api/billing/webhook - Stripe webhook handler
- GET /api/billing/usage - Get current usage
"""
import os
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.session import get_db
from app.db.models import BillingSubscriptionDB, BillingEventDB

router = APIRouter(prefix="/api/billing", tags=["billing"])
logger = logging.getLogger(__name__)

# Stripe
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("Stripe not installed. Run: pip install stripe")

# Environment
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
APP_URL = os.getenv("NEXT_PUBLIC_BASE_URL", "https://app.ai-bookkeeper.app")

if STRIPE_AVAILABLE and STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# Stripe Price IDs - these should be created in Stripe Dashboard
# Format: price_XXXXX
STRIPE_PRICES = {
    # Monthly subscriptions
    "starter_monthly": os.getenv("STRIPE_PRICE_STARTER_MONTHLY", "price_starter_monthly"),
    "team_monthly": os.getenv("STRIPE_PRICE_TEAM_MONTHLY", "price_team_monthly"),
    "firm_monthly": os.getenv("STRIPE_PRICE_FIRM_MONTHLY", "price_firm_monthly"),
    "pilot_monthly": os.getenv("STRIPE_PRICE_PILOT_MONTHLY", "price_pilot_monthly"),
    
    # Annual subscriptions (17% discount)
    "starter_annual": os.getenv("STRIPE_PRICE_STARTER_ANNUAL", "price_starter_annual"),
    "team_annual": os.getenv("STRIPE_PRICE_TEAM_ANNUAL", "price_team_annual"),
    "firm_annual": os.getenv("STRIPE_PRICE_FIRM_ANNUAL", "price_firm_annual"),
    
    # Metered overage prices (per transaction)
    "overage_starter": os.getenv("STRIPE_PRICE_OVERAGE_STARTER", "price_overage_starter"),
    "overage_team": os.getenv("STRIPE_PRICE_OVERAGE_TEAM", "price_overage_team"),
    "overage_firm": os.getenv("STRIPE_PRICE_OVERAGE_FIRM", "price_overage_firm"),
    "overage_enterprise": os.getenv("STRIPE_PRICE_OVERAGE_ENTERPRISE", "price_overage_enterprise"),
    
    # Add-ons
    "addon_extra_entity_starter": os.getenv("STRIPE_PRICE_ADDON_ENTITY_STARTER", "price_addon_entity_starter"),
    "addon_extra_entity_firm": os.getenv("STRIPE_PRICE_ADDON_ENTITY_FIRM", "price_addon_entity_firm"),
    "addon_sso": os.getenv("STRIPE_PRICE_ADDON_SSO", "price_addon_sso"),
    "addon_whitelabel": os.getenv("STRIPE_PRICE_ADDON_WHITELABEL", "price_addon_whitelabel"),
    "addon_retention": os.getenv("STRIPE_PRICE_ADDON_RETENTION", "price_addon_retention"),
    "addon_priority_support": os.getenv("STRIPE_PRICE_ADDON_PRIORITY_SUPPORT", "price_addon_priority_support"),
}

# Plan configurations
PLAN_CONFIG = {
    "starter": {
        "name": "Starter",
        "entities": 1,
        "transactions_monthly": 500,
        "overage_rate": 0.03,
        "monthly_price": 49,
        "annual_price": 41,
    },
    "team": {
        "name": "Team",
        "entities": 3,
        "transactions_monthly": 2000,
        "overage_rate": 0.02,
        "monthly_price": 149,
        "annual_price": 124,
    },
    "firm": {
        "name": "Firm",
        "entities": 10,
        "transactions_monthly": 10000,
        "overage_rate": 0.015,
        "monthly_price": 499,
        "annual_price": 414,
    },
    "pilot": {
        "name": "Pilot",
        "entities": 3,
        "transactions_monthly": 3000,
        "overage_rate": 0.02,
        "monthly_price": 99,
        "annual_price": None,  # Pilot not available annually
    },
    "enterprise": {
        "name": "Enterprise",
        "entities": 25,
        "transactions_monthly": 25000,
        "overage_rate": 0.01,
        "monthly_price": None,  # Custom pricing
        "annual_price": None,
    },
}


class CheckoutRequest(BaseModel):
    """Checkout session request"""
    plan: str  # starter, team, firm, pilot, enterprise
    term: str = "monthly"  # monthly or annual
    addons: List[str] = []  # List of addon IDs


class CheckoutResponse(BaseModel):
    """Checkout session response"""
    url: Optional[str] = None
    message: Optional[str] = None


class BillingStatusResponse(BaseModel):
    """Billing status response"""
    plan: Optional[str] = None
    term: Optional[str] = None
    entities_allowed: int = 0
    tx_quota_monthly: int = 0
    tx_used_monthly: int = 0
    overage_unit_price: float = 0.0
    addons: dict = {}
    is_annual: bool = False
    nonprofit_discount: bool = False


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    db: Session = Depends(get_db)
):
    """
    Create Stripe checkout session.
    
    - **plan**: starter, team, firm, pilot, or enterprise
    - **term**: monthly or annual
    - **addons**: list of addon identifiers
    """
    if not STRIPE_AVAILABLE or not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    # Validate plan
    if request.plan not in PLAN_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {request.plan}")
    
    # Enterprise requires contact
    if request.plan == "enterprise":
        return CheckoutResponse(
            message="Enterprise plans require a consultation. Please contact sales@ai-bookkeeper.app"
        )
    
    # Pilot only available monthly
    if request.plan == "pilot" and request.term == "annual":
        raise HTTPException(status_code=400, detail="Pilot plan only available monthly")
    
    # Build line items
    line_items = []
    
    # Main subscription
    price_key = f"{request.plan}_{request.term}"
    if price_key not in STRIPE_PRICES:
        raise HTTPException(status_code=400, detail=f"Price not configured for {price_key}")
    
    line_items.append({
        "price": STRIPE_PRICES[price_key],
        "quantity": 1,
    })
    
    # Add metered overage price
    overage_price_key = f"overage_{request.plan}"
    if overage_price_key in STRIPE_PRICES:
        line_items.append({
            "price": STRIPE_PRICES[overage_price_key],
        })
    
    # Add-ons
    for addon in request.addons:
        addon_price_key = f"addon_{addon}"
        if addon_price_key in STRIPE_PRICES:
            line_items.append({
                "price": STRIPE_PRICES[addon_price_key],
                "quantity": 1,
            })
    
    try:
        # Create checkout session
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=line_items,
            success_url=f"{APP_URL}/success?session_id={{CHECKOUT_SESSION_ID}}&plan={request.plan}&amount={PLAN_CONFIG[request.plan][f'{request.term}_price']}",
            cancel_url=f"{APP_URL}/cancel",
            allow_promotion_codes=True,
            billing_address_collection="required",
            metadata={
                "plan": request.plan,
                "term": request.term,
            }
        )
        
        logger.info(f"Created checkout session for {request.plan}/{request.term}: {session.id}")
        
        return CheckoutResponse(url=session.url)
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.get("/status", response_model=BillingStatusResponse)
async def get_billing_status(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current billing status for tenant.
    
    Returns plan limits, current usage, and active add-ons.
    """
    # Get active subscription from DB
    subscription = db.query(BillingSubscriptionDB).filter(
        BillingSubscriptionDB.tenant_id == tenant_id,
        BillingSubscriptionDB.status == "active"
    ).first()
    
    if not subscription:
        # No active subscription - return free tier defaults
        return BillingStatusResponse(
            plan=None,
            entities_allowed=0,
            tx_quota_monthly=0,
            tx_used_monthly=0,
        )
    
    # Get plan config
    plan_config = PLAN_CONFIG.get(subscription.plan, {})
    
    # Parse add-ons from metadata
    addons_active = {
        "sso": subscription.metadata.get("addon_sso", False) if subscription.metadata else False,
        "white_label": subscription.metadata.get("addon_whitelabel", False) if subscription.metadata else False,
        "retention_24m": subscription.metadata.get("addon_retention", False) if subscription.metadata else False,
        "priority_support": subscription.metadata.get("addon_priority_support", False) if subscription.metadata else False,
    }
    
    return BillingStatusResponse(
        plan=subscription.plan,
        term=subscription.metadata.get("term", "monthly") if subscription.metadata else "monthly",
        entities_allowed=plan_config.get("entities", 0),
        tx_quota_monthly=plan_config.get("transactions_monthly", 0),
        tx_used_monthly=subscription.metadata.get("tx_used_monthly", 0) if subscription.metadata else 0,
        overage_unit_price=plan_config.get("overage_rate", 0.0),
        addons=addons_active,
        is_annual=subscription.metadata.get("term") == "annual" if subscription.metadata else False,
        nonprofit_discount=subscription.metadata.get("nonprofit", False) if subscription.metadata else False,
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhooks.
    
    Events:
    - checkout.session.completed
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.paid
    """
    if not STRIPE_AVAILABLE or not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook not configured")
    
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle events
    event_type = event["type"]
    data = event["data"]["object"]
    
    logger.info(f"Received Stripe webhook: {event_type}")
    
    if event_type == "checkout.session.completed":
        # Extract subscription info
        subscription_id = data.get("subscription")
        customer_id = data.get("customer")
        metadata = data.get("metadata", {})
        
        # Create billing event
        billing_event = BillingEventDB(
            id=f"evt_{datetime.utcnow().timestamp()}",
            tenant_id=metadata.get("tenant_id", customer_id),
            event_type="checkout_completed",
            stripe_event_id=event["id"],
            amount=data.get("amount_total", 0) / 100,  # Convert cents to dollars
            currency=data.get("currency", "usd"),
            metadata=metadata,
            created_at=datetime.utcnow()
        )
        db.add(billing_event)
        db.commit()
        
    elif event_type == "customer.subscription.created":
        # Create subscription record
        subscription_id = data["id"]
        customer_id = data["customer"]
        status = data["status"]
        plan_id = data["items"]["data"][0]["price"]["id"]
        
        subscription = BillingSubscriptionDB(
            id=subscription_id,
            tenant_id=customer_id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            plan=_map_price_to_plan(plan_id),
            status=status,
            current_period_start=datetime.fromtimestamp(data["current_period_start"]),
            current_period_end=datetime.fromtimestamp(data["current_period_end"]),
            cancel_at_period_end=data.get("cancel_at_period_end", False),
            metadata={},
            created_at=datetime.utcnow()
        )
        db.add(subscription)
        db.commit()
        
        logger.info(f"Created subscription {subscription_id} for {customer_id}")
        
    elif event_type == "invoice.paid":
        # Record payment
        invoice_id = data["id"]
        customer_id = data["customer"]
        amount = data["amount_paid"] / 100
        
        billing_event = BillingEventDB(
            id=f"evt_{datetime.utcnow().timestamp()}",
            tenant_id=customer_id,
            event_type="invoice_paid",
            stripe_event_id=event["id"],
            amount=amount,
            currency=data.get("currency", "usd"),
            metadata={"invoice_id": invoice_id},
            created_at=datetime.utcnow()
        )
        db.add(billing_event)
        db.commit()
        
    return {"status": "success"}


def _map_price_to_plan(price_id: str) -> str:
    """Map Stripe price ID to plan name"""
    for plan, plan_price_id in STRIPE_PRICES.items():
        if plan_price_id == price_id:
            # Extract base plan name (remove _monthly, _annual suffix)
            return plan.split("_")[0] if "_" in plan else plan
    return "unknown"

