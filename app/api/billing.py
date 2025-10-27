"""
Billing API - Stripe Subscription Management
============================================

This module handles all billing operations including subscription management,
payment processing, usage tracking, and Stripe webhook integration.

API Endpoints:
-------------
- GET /api/billing/status - Get plan, limits, and current usage
- POST /api/billing/create_checkout_session - Start Stripe checkout
- GET /api/billing/portal_link - Get link to Stripe customer portal
- POST /api/billing/stripe_webhook - Handle Stripe events (webhooks)

Subscription Plans:
------------------
Starter Plan ($49/month):
- 300 transactions/month
- 1 company
- Basic support
- Auto-categorization with AI

Professional Plan ($149/month):
- 1,500 transactions/month
- 1 company
- Priority support
- Advanced features (bulk approve, auto-post)

Firm Plan ($499/month):
- Unlimited transactions
- 10 companies
- Premium support
- White-label options

Billing Flow:
------------
1. User clicks upgrade on pricing page
2. Frontend calls /api/billing/create_checkout_session
3. Backend creates Stripe Checkout Session
4. User redirected to Stripe-hosted payment page
5. User enters card details and confirms
6. Stripe webhook fires (checkout.session.completed)
7. Webhook handler creates BillingSubscriptionDB record
8. User redirected back to success page
9. Access granted to premium features

Usage Tracking:
--------------
- tx_analyzed: Transactions processed by AI
- tx_posted: Transactions posted to QuickBooks
- daily_analyze: Free tier daily limit (20/day)
- daily_explain: AI explanation daily limit (10/day)

Entitlement Checks:
------------------
Before processing requests, middleware checks:
1. Does tenant have active subscription?
2. Are they within monthly transaction cap?
3. Are they within daily rate limits (free tier)?
4. Do they have permission for requested feature?

Stripe Webhook Events:
---------------------
The app listens for these webhook events:
- checkout.session.completed: New subscription created
- customer.subscription.updated: Plan changed or renewed
- customer.subscription.deleted: Subscription canceled
- invoice.payment_succeeded: Successful payment
- invoice.payment_failed: Failed payment (past_due)

Webhook Security:
----------------
All webhooks are verified using Stripe signature:
1. Stripe includes signature in Stripe-Signature header
2. Server computes signature from webhook secret + payload
3. Signatures must match to accept webhook
4. Prevents unauthorized webhook calls

Free Tier:
---------
Users without subscription get free tier access:
- 20 transactions/day (analyze)
- 10 AI explanations/day
- No auto-posting
- No bulk operations
- Single company only
"""
import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.db.models import BillingSubscriptionDB, BillingEventDB, DecisionAuditLogDB
from app.ui.rbac import User, get_current_user, Role, require_role


router = APIRouter(prefix="/api/billing", tags=["billing"])
logger = logging.getLogger(__name__)

# Stripe (lazy import to handle missing package)
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("Stripe not installed. Run: pip install stripe")

# Environment
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
APP_URL = os.getenv("APP_URL", "http://localhost:8000")

if STRIPE_AVAILABLE and STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


class CheckoutRequest(BaseModel):
    """Checkout session request."""
    tenant_id: str
    plan: str  # starter, pro, firm
    coupon: Optional[str] = None


class CheckoutResponse(BaseModel):
    """Checkout session response."""
    success: bool
    checkout_url: Optional[str] = None
    session_id: Optional[str] = None
    message: Optional[str] = None


class PortalResponse(BaseModel):
    """Customer portal response."""
    success: bool
    portal_url: Optional[str] = None
    message: Optional[str] = None


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


@router.get("/status", response_model=BillingStatusResponse)
async def get_billing_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current plan, limits, and usage for tenant.
    
    This is the first Action call in any "post" flow for GPT paywall checks.
    """
    # Get tenant ID from user
    # For now, use first tenant or default to user_id
    tenant_id = user.tenants[0] if user.tenants else user.user_id
    
    try:
        from app.services.billing import BillingService
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
    except Exception as e:
        logger.error(f"Error getting billing status for tenant {tenant_id}: {e}")
        # Return default free tier status
        return BillingStatusResponse(
            active=False,
            plan=None,
            limits=BillingLimits(tx_cap=0, bulk_approve=False, included_companies=1),
            usage=BillingUsage(tx_analyzed=0, tx_posted=0, daily_analyze=0, daily_explain=0)
        )


@router.post("/create_checkout_session", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create Stripe Checkout session for subscription.
    
    Requires:
    - STRIPE_SECRET_KEY in environment
    - Owner role
    
    Returns checkout URL or stub message if Stripe not configured.
    """
    # RBAC: Owner only
    require_role(Role.OWNER, user)
    
    # Check Stripe configured
    if not STRIPE_AVAILABLE or not STRIPE_SECRET_KEY:
        logger.warning("Billing not configured (Stripe keys missing)")
        return CheckoutResponse(
            success=False,
            message="Billing not configured (test mode). Set STRIPE_SECRET_KEY to enable."
        )
    
    # Validate plan
    valid_plans = ["starter", "pro", "firm"]
    if request.plan not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Must be one of: {valid_plans}")
    
    # Get price IDs from environment
    price_ids = {
        "starter": os.getenv("STRIPE_PRICE_STARTER"),
        "pro": os.getenv("STRIPE_PRICE_PRO"),
        "firm": os.getenv("STRIPE_PRICE_FIRM")
    }
    
    price_id = price_ids.get(request.plan)
    if not price_id:
        raise HTTPException(
            status_code=500,
            detail=f"Price ID not configured for plan '{request.plan}'. Set STRIPE_PRICE_{request.plan.upper()}."
        )
    
    # Create checkout session
    try:
        session_params = {
            "customer_email": user.email,
            "line_items": [{
                "price": price_id,
                "quantity": 1
            }],
            "mode": "subscription",
            "success_url": f"{APP_URL}/billing?success=true&session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{APP_URL}/billing?canceled=true",
            "metadata": {
                "tenant_id": request.tenant_id,
                "plan": request.plan,
                "user_id": user.user_id
            }
        }
        
        # Add coupon if provided
        if request.coupon:
            session_params["discounts"] = [{"coupon": request.coupon}]
        
        session = stripe.checkout.Session.create(**session_params)
        
        # Audit entry
        audit = DecisionAuditLogDB(
            timestamp=datetime.utcnow(),
            tenant_id=request.tenant_id,
            action="billing_checkout_started",
            user_id=user.user_id
        )
        db.add(audit)
        db.commit()
        
        logger.info(f"Checkout session created: {session.id} for tenant {request.tenant_id}, plan {request.plan}")
        
        return CheckoutResponse(
            success=True,
            checkout_url=session.url,
            session_id=session.id
        )
    
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/portal_link", response_model=PortalResponse)
async def get_portal_link(
    tenant_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Stripe Customer Portal link for managing subscription.
    
    Requires:
    - Existing subscription with stripe_customer_id
    - Owner role
    
    Returns portal URL or stub message if not configured.
    """
    # RBAC: Owner only
    require_role(Role.OWNER, user)
    
    # Check Stripe configured
    if not STRIPE_AVAILABLE or not STRIPE_SECRET_KEY:
        return PortalResponse(
            success=False,
            message="Billing not configured"
        )
    
    # Get subscription
    subscription = db.query(BillingSubscriptionDB).filter_by(
        tenant_id=tenant_id
    ).first()
    
    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(
            status_code=404,
            detail="No subscription found for this tenant. Create a subscription first."
        )
    
    # Create portal session
    try:
        session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=f"{APP_URL}/billing"
        )
        
        logger.info(f"Customer portal session created for tenant {tenant_id}")
        
        return PortalResponse(
            success=True,
            portal_url=session.url
        )
    
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating portal session: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/entitlements")
async def get_entitlements_endpoint(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get entitlements for the current user's tenant.
    
    Returns:
    -------
    - plan: Current plan name (free, starter, professional, enterprise)
    - status: Subscription status (active, inactive, cancelled, past_due)
    - entities_allowed: Number of companies/entities allowed
    - tx_quota_monthly: Monthly transaction quota
    - tx_used_monthly: Transactions used this month
    - tx_remaining: Transactions remaining this month
    - features: List of enabled features
    - addons: List of active add-ons
    
    Usage:
    ------
    Frontend can call this to:
    - Show quota usage in UI
    - Disable features not in plan
    - Show upgrade CTAs when approaching limit
    """
    from app.middleware.entitlements import get_entitlements
    
    # Get tenant_id from user
    tenant_ids = user.tenant_ids if hasattr(user, 'tenant_ids') else []
    if not tenant_ids:
        raise HTTPException(status_code=403, detail="No tenant access")
    
    tenant_id = tenant_ids[0] if isinstance(tenant_ids, list) else tenant_ids
    
    # Get entitlements
    entitlements = get_entitlements(tenant_id, db)
    
    return entitlements


@router.post("/portal")
async def create_portal_session(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create Stripe billing portal session.
    
    This endpoint creates a portal session and returns the URL where
    the user can manage their subscription, update payment methods,
    view invoices, etc.
    
    Returns:
    -------
    { "url": "https://billing.stripe.com/session/..." }
    
    The frontend should redirect the user to this URL.
    """
    from app.auth.rbac import require_role, Role
    
    # RBAC: Owner only
    require_role(Role.OWNER, user)
    
    # Check Stripe configured
    if not STRIPE_AVAILABLE or not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Billing portal not configured"
        )
    
    # Get tenant_id
    tenant_ids = user.tenant_ids if hasattr(user, 'tenant_ids') else []
    if not tenant_ids:
        raise HTTPException(status_code=403, detail="No tenant access")
    
    tenant_id = tenant_ids[0] if isinstance(tenant_ids, list) else tenant_ids
    
    # Get subscription
    subscription = db.query(BillingSubscriptionDB).filter_by(
        tenant_id=tenant_id
    ).first()
    
    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(
            status_code=404,
            detail="No subscription found. Please create a subscription first."
        )
    
    # Create portal session
    try:
        import os
        return_url = os.getenv("STRIPE_BILLING_PORTAL_RETURN_URL", f"{APP_URL}/firm")
        
        session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=return_url
        )
        
        logger.info(
            f"Billing portal session created",
            extra={"tenant_id": tenant_id, "user_id": user.user_id}
        )
        
        return {"url": session.url}
    
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating portal session: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stripe_webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    
    Verifies signature and processes:
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_failed
    
    Idempotent: duplicate events are ignored.
    """
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    
    # Check webhook secret configured
    if not STRIPE_WEBHOOK_SECRET:
        logger.warning("Stripe webhook secret not configured. Webhook processing disabled.")
        return {"success": False, "message": "Webhook secret not configured"}
    
    if not STRIPE_AVAILABLE:
        return {"success": False, "message": "Stripe not available"}
    
    # Verify signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Check if event already processed (idempotency)
    existing_event = db.query(BillingEventDB).filter_by(
        stripe_event_id=event["id"]
    ).first()
    
    if existing_event:
        logger.info(f"Event {event['id']} already processed (idempotent)")
        return {"success": True, "message": "Event already processed"}
    
    # Log event
    event_log = BillingEventDB(
        type=event["type"],
        stripe_event_id=event["id"],
        payload_json=event["data"],
        processed=False
    )
    db.add(event_log)
    db.commit()
    
    # Process event
    try:
        if event["type"] == "checkout.session.completed":
            handle_checkout_completed(event["data"]["object"], db)
        elif event["type"] == "customer.subscription.created":
            handle_subscription_created(event["data"]["object"], db)
        elif event["type"] == "customer.subscription.updated":
            handle_subscription_updated(event["data"]["object"], db)
        elif event["type"] == "customer.subscription.deleted":
            handle_subscription_deleted(event["data"]["object"], db)
        elif event["type"] == "invoice.payment_failed":
            handle_payment_failed(event["data"]["object"], db)
        elif event["type"] == "invoice.paid":
            handle_invoice_paid(event["data"]["object"], db)
        elif event["type"] == "customer.subscription.trial_will_end":
            handle_trial_will_end(event["data"]["object"], db)
        else:
            logger.info(f"Unhandled event type: {event['type']}")
        
        # Mark as processed
        event_log.processed = True
        db.commit()
        
        logger.info(f"Webhook event {event['id']} processed successfully")
        
    except Exception as e:
        logger.error(f"Error processing webhook event {event['id']}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing event: {str(e)}")
    
    return {"success": True}


def handle_subscription_created(subscription_data, db):
    """Handle subscription creation."""
    tenant_id = subscription_data["metadata"].get("tenant_id")
    if not tenant_id:
        logger.warning(f"Subscription {subscription_data['id']} missing tenant_id in metadata")
        return
    
    subscription = BillingSubscriptionDB(
        tenant_id=tenant_id,
        plan=subscription_data["metadata"].get("plan", "starter"),
        status=subscription_data["status"],
        stripe_customer_id=subscription_data["customer"],
        stripe_subscription_id=subscription_data["id"],
        current_period_start=datetime.fromtimestamp(subscription_data["current_period_start"]),
        current_period_end=datetime.fromtimestamp(subscription_data["current_period_end"]),
        cancel_at_period_end=subscription_data.get("cancel_at_period_end", False)
    )
    db.add(subscription)
    
    # Create entitlement from price metadata
    try:
        from app.services.billing import BillingService
        billing_service = BillingService(db)
        
        # Get price metadata
        price_id = subscription_data["items"]["data"][0]["price"]["id"]
        if STRIPE_AVAILABLE:
            price = stripe.Price.retrieve(price_id)
            price_metadata = price.get("metadata", {})
            
            # Extract trial end
            trial_end = None
            if subscription_data.get("trial_end"):
                trial_end = datetime.fromtimestamp(subscription_data["trial_end"])
            
            # Map entitlement from price metadata
            billing_service.map_entitlement_from_price(
                tenant_id=tenant_id,
                price_id=price_id,
                price_metadata=price_metadata,
                subscription_status=subscription_data["status"],
                trial_end=trial_end
            )
    except Exception as e:
        logger.error(f"Error creating entitlement for tenant {tenant_id}: {e}")
    
    # Update tenant settings with Stripe customer ID
    from app.db.models import TenantSettingsDB
    tenant_settings = db.query(TenantSettingsDB).filter(
        TenantSettingsDB.tenant_id == tenant_id
    ).first()
    
    if tenant_settings:
        tenant_settings.stripe_customer_id = subscription_data["customer"]
        tenant_settings.stripe_subscription_id = subscription_data["id"]
    
    # Audit entry
    audit = DecisionAuditLogDB(
        timestamp=datetime.utcnow(),
        tenant_id=tenant_id,
        action="billing_subscription_created"
    )
    db.add(audit)
    db.commit()
    
    logger.info(f"Subscription created for tenant {tenant_id}: {subscription_data['id']}")


def handle_subscription_updated(subscription_data, db):
    """Handle subscription update."""
    tenant_id = subscription_data["metadata"].get("tenant_id")
    if not tenant_id:
        logger.warning(f"Subscription {subscription_data['id']} missing tenant_id in metadata")
        return
    
    subscription = db.query(BillingSubscriptionDB).filter_by(
        tenant_id=tenant_id
    ).first()
    
    if not subscription:
        # Create if doesn't exist (edge case)
        handle_subscription_created(subscription_data, db)
        return
    
    # Update existing
    old_status = subscription.status
    subscription.status = subscription_data["status"]
    subscription.current_period_start = datetime.fromtimestamp(subscription_data["current_period_start"])
    subscription.current_period_end = datetime.fromtimestamp(subscription_data["current_period_end"])
    subscription.cancel_at_period_end = subscription_data.get("cancel_at_period_end", False)
    subscription.updated_at = datetime.utcnow()
    
    # Update entitlement
    try:
        from app.services.billing import BillingService
        billing_service = BillingService(db)
        
        # Get price metadata
        price_id = subscription_data["items"]["data"][0]["price"]["id"]
        if STRIPE_AVAILABLE:
            price = stripe.Price.retrieve(price_id)
            price_metadata = price.get("metadata", {})
            
            # Extract trial end
            trial_end = None
            if subscription_data.get("trial_end"):
                trial_end = datetime.fromtimestamp(subscription_data["trial_end"])
            
            # Update entitlement from price metadata
            billing_service.map_entitlement_from_price(
                tenant_id=tenant_id,
                price_id=price_id,
                price_metadata=price_metadata,
                subscription_status=subscription_data["status"],
                trial_end=trial_end
            )
    except Exception as e:
        logger.error(f"Error updating entitlement for tenant {tenant_id}: {e}")
    
    # Audit entry
    audit = DecisionAuditLogDB(
        timestamp=datetime.utcnow(),
        tenant_id=tenant_id,
        action="billing_subscription_updated"
    )
    db.add(audit)
    db.commit()
    
    logger.info(f"Subscription updated for tenant {tenant_id}: {old_status} -> {subscription.status}")


def handle_subscription_deleted(subscription_data, db):
    """Handle subscription cancellation."""
    tenant_id = subscription_data["metadata"].get("tenant_id")
    if not tenant_id:
        return
    
    subscription = db.query(BillingSubscriptionDB).filter_by(
        tenant_id=tenant_id
    ).first()
    
    if subscription:
        subscription.status = "canceled"
        subscription.updated_at = datetime.utcnow()
        
        # Deactivate entitlement
        try:
            from app.db.models import EntitlementDB
            entitlement = db.query(EntitlementDB).filter(
                EntitlementDB.tenant_id == tenant_id
            ).first()
            
            if entitlement:
                entitlement.active = False
                entitlement.subscription_status = "canceled"
                entitlement.updated_at = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error deactivating entitlement for tenant {tenant_id}: {e}")
        
        # Audit entry
        audit = DecisionAuditLogDB(
            timestamp=datetime.utcnow(),
            tenant_id=tenant_id,
            action="billing_subscription_canceled"
        )
        db.add(audit)
        db.commit()
        
        logger.info(f"Subscription canceled for tenant {tenant_id}")


def handle_payment_failed(invoice_data, db):
    """Handle payment failure."""
    customer_id = invoice_data.get("customer")
    if not customer_id:
        return
    
    # Find subscription by customer_id
    subscription = db.query(BillingSubscriptionDB).filter_by(
        stripe_customer_id=customer_id
    ).first()
    
    if subscription:
        subscription.status = "past_due"
        subscription.updated_at = datetime.utcnow()
        
        # Deactivate entitlement
        try:
            from app.db.models import EntitlementDB
            entitlement = db.query(EntitlementDB).filter(
                EntitlementDB.tenant_id == subscription.tenant_id
            ).first()
            
            if entitlement:
                entitlement.active = False
                entitlement.subscription_status = "past_due"
                entitlement.updated_at = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error deactivating entitlement for tenant {subscription.tenant_id}: {e}")
        
        # Audit entry
        audit = DecisionAuditLogDB(
            timestamp=datetime.utcnow(),
            tenant_id=subscription.tenant_id,
            action="billing_payment_failed"
        )
        db.add(audit)
        db.commit()
        
        logger.warning(f"Payment failed for tenant {subscription.tenant_id}")


def handle_invoice_paid(invoice_data, db):
    """Handle successful invoice payment."""
    customer_id = invoice_data.get("customer")
    if not customer_id:
        return
    
    # Find subscription by customer_id
    subscription = db.query(BillingSubscriptionDB).filter_by(
        stripe_customer_id=customer_id
    ).first()
    
    if subscription:
        # Update status to active if it was past_due
        if subscription.status == "past_due":
            subscription.status = "active"
            subscription.updated_at = datetime.utcnow()
            
            # Reactivate entitlement
            try:
                from app.db.models import EntitlementDB
                entitlement = db.query(EntitlementDB).filter(
                    EntitlementDB.tenant_id == subscription.tenant_id
                ).first()
                
                if entitlement:
                    entitlement.active = True
                    entitlement.subscription_status = "active"
                    entitlement.updated_at = datetime.utcnow()
            except Exception as e:
                logger.error(f"Error reactivating entitlement for tenant {subscription.tenant_id}: {e}")
            
            # Audit entry
            audit = DecisionAuditLogDB(
                timestamp=datetime.utcnow(),
                tenant_id=subscription.tenant_id,
                action="billing_payment_successful"
            )
            db.add(audit)
            db.commit()
            
            logger.info(f"Payment successful for tenant {subscription.tenant_id}, subscription reactivated")


def handle_checkout_completed(session_data, db):
    """Handle checkout session completion."""
    tenant_id = session_data["metadata"].get("tenant_id")
    if not tenant_id:
        logger.warning(f"Checkout session {session_data['id']} missing tenant_id in metadata")
        return
    
    customer_id = session_data.get("customer")
    subscription_id = session_data.get("subscription")
    
    if customer_id:
        # Update tenant settings with Stripe customer ID
        from app.db.models import TenantSettingsDB
        tenant_settings = db.query(TenantSettingsDB).filter(
            TenantSettingsDB.tenant_id == tenant_id
        ).first()
        
        if not tenant_settings:
            # Create tenant settings if doesn't exist
            tenant_settings = TenantSettingsDB(
                tenant_id=tenant_id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id
            )
            db.add(tenant_settings)
        else:
            tenant_settings.stripe_customer_id = customer_id
            if subscription_id:
                tenant_settings.stripe_subscription_id = subscription_id
        
        db.commit()
        logger.info(f"Checkout completed for tenant {tenant_id}, customer {customer_id}")


def handle_trial_will_end(subscription_data, db):
    """Handle trial ending soon notification (3 days before)."""
    tenant_id = subscription_data["metadata"].get("tenant_id")
    if not tenant_id:
        return
    
    # Log the event for potential notification system
    audit = DecisionAuditLogDB(
        timestamp=datetime.utcnow(),
        tenant_id=tenant_id,
        action="billing_trial_will_end"
    )
    db.add(audit)
    db.commit()
    
    logger.info(f"Trial will end soon for tenant {tenant_id}")
    
    # TODO: Send notification to user (email, in-app notification)
    # This can be integrated with the existing notification system

