#!/usr/bin/env python3
"""
Verify Stripe webhook endpoint configuration.

Usage:
    # With TEST key (default)
    python scripts/verify_stripe_webhook.py
    
    # With LIVE key
    STRIPE_SECRET_KEY=sk_live_... python scripts/verify_stripe_webhook.py

Checks:
- Webhook endpoint exists
- Endpoint is enabled
- Expected events are subscribed
"""

import os
import sys

try:
    import stripe
except ImportError:
    print("❌ Stripe library not installed")
    print("Run: pip install stripe")
    sys.exit(1)


def main():
    """Verify Stripe webhook configuration."""
    
    # Get API key from environment
    api_key = os.getenv("STRIPE_SECRET_KEY")
    if not api_key:
        print("❌ STRIPE_SECRET_KEY not set")
        sys.exit(1)
    
    # Determine mode
    is_live = api_key.startswith("sk_live_")
    mode = "LIVE" if is_live else "TEST"
    
    print("\n" + "="*70)
    print(f"  Stripe Webhook Verification ({mode} Mode)")
    print("="*70 + "\n")
    
    stripe.api_key = api_key
    
    try:
        # List webhook endpoints
        endpoints = stripe.WebhookEndpoint.list(limit=100)
        
        if not endpoints.data:
            print(f"⚠️  No webhook endpoints found in {mode} mode")
            print("\nTo create webhook:")
            print("1. Go to Stripe Dashboard → Developers → Webhooks")
            print("2. Click 'Add endpoint'")
            print("3. URL: https://YOUR_DOMAIN/api/billing/webhook")
            print("4. Events to send:")
            print("   - checkout.session.completed")
            print("   - customer.subscription.created")
            print("   - customer.subscription.updated")
            print("   - customer.subscription.deleted")
            print("   - invoice.payment_failed")
            print("   - customer.subscription.trial_will_end")
            sys.exit(1)
        
        print(f"Found {len(endpoints.data)} webhook endpoint(s):\n")
        
        expected_events = {
            "checkout.session.completed",
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "invoice.payment_failed",
            "customer.subscription.trial_will_end"
        }
        
        for idx, endpoint in enumerate(endpoints.data, 1):
            status = "✅ ENABLED" if endpoint.status == "enabled" else "❌ DISABLED"
            print(f"{idx}. {status}")
            print(f"   URL: {endpoint.url}")
            print(f"   Events: {len(endpoint.enabled_events)} subscribed")
            
            # Check for expected events
            subscribed = set(endpoint.enabled_events)
            missing = expected_events - subscribed
            
            if missing:
                print(f"   ⚠️  Missing events: {', '.join(sorted(missing))}")
            else:
                print(f"   ✅ All expected events subscribed")
            
            print()
        
        # Summary
        active_count = sum(1 for e in endpoints.data if e.status == "enabled")
        
        if active_count == 0:
            print("❌ No enabled webhooks found")
            sys.exit(1)
        elif active_count > 1:
            print(f"⚠️  Multiple active webhooks ({active_count}) - ensure only one is production")
        else:
            print(f"✅ {active_count} active webhook configured")
        
        print("\n" + "="*70)
        print("  Verification Complete")
        print("="*70 + "\n")
        
    except stripe.error.AuthenticationError:
        print("❌ Invalid Stripe API key")
        sys.exit(1)
    except stripe.error.StripeError as e:
        print(f"❌ Stripe API error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

