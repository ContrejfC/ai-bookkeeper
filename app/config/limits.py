"""
Billing limits and entitlement configuration for AI Bookkeeper.
"""

# Free tier daily limits
FREE_DAILY_ANALYZE_CAP = 50  # Free analyze calls per tenant per day
FREE_DAILY_EXPLAIN_CAP = 50  # Free explain calls per tenant per day

# Plan transaction caps (monthly)
PLAN_TX_CAPS = {
    "starter": 300,
    "pro": 2000,
    "firm": 10000
}

# Plan features
PLAN_FEATURES = {
    "starter": {
        "tx_cap": 300,
        "bulk_approve": False,
        "included_companies": 1,
        "price_monthly": 49.00
    },
    "pro": {
        "tx_cap": 2000,
        "bulk_approve": True,
        "included_companies": 1,
        "price_monthly": 149.00
    },
    "firm": {
        "tx_cap": 10000,
        "bulk_approve": True,
        "included_companies": 10,
        "price_monthly": 499.00,
        "additional_company_price": 39.00
    }
}

# Error codes and messages
ERROR_CODES = {
    "ENTITLEMENT_REQUIRED": {
        "code": "ENTITLEMENT_REQUIRED",
        "message": "Activate a plan to post to QuickBooks.",
        "http_status": 402
    },
    "MONTHLY_CAP_EXCEEDED": {
        "code": "MONTHLY_CAP_EXCEEDED", 
        "message": "Monthly posting limit reached. Upgrade or wait for reset.",
        "http_status": 402
    },
    "FREE_CAP_EXCEEDED": {
        "code": "FREE_CAP_EXCEEDED",
        "message": "Free daily analysis cap (50) reached.",
        "http_status": 429
    },
    "BULK_APPROVE_REQUIRED": {
        "code": "BULK_APPROVE_REQUIRED",
        "message": "Bulk approvals require Pro or Firm plan.",
        "http_status": 402
    }
}

# Paywall markdown for GPT integration
PAYWALL_MD = """To post to QuickBooks, activate a plan:
- **Starter** $49/mo (300 tx/mo)
- **Pro** $149/mo (2,000 tx/mo, bulk approvals)
- **Firm** $499/mo (10 companies included)

Click **Start 14-day trial** to open secure checkout, then say 'retry post'.
Or **continue free** to review proposals only."""

# Stripe webhook events to handle
STRIPE_WEBHOOK_EVENTS = [
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.payment_failed",
    "customer.subscription.trial_will_end"
]

