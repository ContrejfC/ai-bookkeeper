#!/usr/bin/env python3
"""
Stripe Bootstrap Script for AI Bookkeeper

Creates products and prices in Stripe TEST mode and outputs configuration.

Usage:
    export STRIPE_SECRET_KEY=sk_test_...
    python scripts/stripe_bootstrap.py

Outputs:
    - JSON map of product and price IDs
    - Updates .env.example with Stripe configuration
"""

import os
import sys
import json
from pathlib import Path

try:
    import stripe
except ImportError:
    print("ERROR: stripe package not installed. Run: pip install stripe")
    sys.exit(1)


def bootstrap_stripe():
    """Bootstrap Stripe products and prices for AI Bookkeeper."""
    
    # Get Stripe API key
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        print("ERROR: STRIPE_SECRET_KEY environment variable not set")
        print("Usage: export STRIPE_SECRET_KEY=sk_test_... && python scripts/stripe_bootstrap.py")
        sys.exit(1)
    
    if not stripe_key.startswith("sk_test_"):
        print("WARNING: This script is designed for TEST mode keys (sk_test_...)")
        response = input("Continue with live key? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            sys.exit(0)
    
    stripe.api_key = stripe_key
    
    print("\n" + "="*70)
    print("  AI Bookkeeper - Stripe Bootstrap")
    print("="*70 + "\n")
    
    # Define plan configurations
    plans = {
        "starter": {
            "name": "AI Bookkeeper Starter",
            "description": "Perfect for small businesses - 300 transactions per month",
            "price": 4900,  # $49.00 in cents
            "metadata": {
                "plan": "starter",
                "tx_cap": "300",
                "bulk_approve": "false",
                "included_companies": "1"
            }
        },
        "pro": {
            "name": "AI Bookkeeper Pro",
            "description": "For growing businesses - 2,000 transactions per month with bulk approvals",
            "price": 14900,  # $149.00 in cents
            "metadata": {
                "plan": "pro",
                "tx_cap": "2000",
                "bulk_approve": "true",
                "included_companies": "1"
            }
        },
        "firm": {
            "name": "AI Bookkeeper Firm",
            "description": "For accounting firms - includes 10 companies, additional companies $39/mo each",
            "price": 49900,  # $499.00 in cents
            "metadata": {
                "plan": "firm",
                "tx_cap": "10000",
                "bulk_approve": "true",
                "included_companies": "10"
            }
        }
    }
    
    results = {}
    
    # Create products and prices
    for plan_key, plan_config in plans.items():
        print(f"Creating {plan_config['name']}...")
        
        try:
            # Create product
            product = stripe.Product.create(
                name=plan_config["name"],
                description=plan_config["description"],
                metadata=plan_config["metadata"]
            )
            
            print(f"  ✓ Product created: {product.id}")
            
            # Create price
            price = stripe.Price.create(
                product=product.id,
                unit_amount=plan_config["price"],
                currency="usd",
                recurring={
                    "interval": "month",
                    "trial_period_days": 14
                },
                metadata=plan_config["metadata"]
            )
            
            print(f"  ✓ Price created: {price.id}")
            print(f"  ✓ Amount: ${plan_config['price']/100:.2f}/month")
            print(f"  ✓ Trial: 14 days")
            print(f"  ✓ Metadata: {plan_config['metadata']}")
            print()
            
            results[plan_key] = {
                "product_id": product.id,
                "price_id": price.id,
                "amount": plan_config["price"],
                "metadata": plan_config["metadata"]
            }
            
        except stripe.error.StripeError as e:
            print(f"  ✗ Error creating {plan_key}: {e}")
            continue
    
    # Create additional company price for Firm plan
    print("Creating Firm Additional Company Add-on...")
    try:
        addon_product = stripe.Product.create(
            name="AI Bookkeeper Firm - Additional Company",
            description="Add additional company to Firm plan",
            metadata={
                "addon": "firm_additional_company",
                "base_plan": "firm"
            }
        )
        
        addon_price = stripe.Price.create(
            product=addon_product.id,
            unit_amount=3900,  # $39.00 in cents
            currency="usd",
            recurring={"interval": "month"},
            metadata={
                "addon": "firm_additional_company",
                "base_plan": "firm"
            }
        )
        
        print(f"  ✓ Add-on Product created: {addon_product.id}")
        print(f"  ✓ Add-on Price created: {addon_price.id}")
        print(f"  ✓ Amount: $39.00/month per additional company")
        print()
        
        results["firm_addon"] = {
            "product_id": addon_product.id,
            "price_id": addon_price.id,
            "amount": 3900
        }
        
    except stripe.error.StripeError as e:
        print(f"  ✗ Error creating add-on: {e}")
    
    # Print summary
    print("="*70)
    print("  Bootstrap Complete!")
    print("="*70 + "\n")
    
    print("Product and Price IDs (JSON):")
    print(json.dumps(results, indent=2))
    print()
    
    # Generate .env configuration
    env_config = []
    env_config.append("# Stripe Configuration (TEST MODE)")
    env_config.append(f"STRIPE_SECRET_KEY={stripe_key}")
    env_config.append("STRIPE_WEBHOOK_SECRET=whsec_...  # Set this after creating webhook in Stripe Dashboard")
    env_config.append("")
    env_config.append("# Stripe Product IDs")
    if "starter" in results:
        env_config.append(f"STRIPE_PRODUCT_STARTER={results['starter']['product_id']}")
        env_config.append(f"STRIPE_PRICE_STARTER={results['starter']['price_id']}")
    if "pro" in results:
        env_config.append(f"STRIPE_PRODUCT_PRO={results['pro']['product_id']}")
        env_config.append(f"STRIPE_PRICE_PRO={results['pro']['price_id']}")
    if "firm" in results:
        env_config.append(f"STRIPE_PRODUCT_FIRM={results['firm']['product_id']}")
        env_config.append(f"STRIPE_PRICE_FIRM={results['firm']['price_id']}")
    if "firm_addon" in results:
        env_config.append(f"STRIPE_PRICE_FIRM_ADDON={results['firm_addon']['price_id']}")
    
    print("\nEnvironment Configuration:")
    print("-" * 70)
    for line in env_config:
        print(line)
    print("-" * 70)
    
    # Update .env.example
    try:
        env_example_path = Path(__file__).parent.parent / ".env.example"
        
        # Read existing .env.example
        if env_example_path.exists():
            with open(env_example_path, "r") as f:
                existing_content = f.read()
        else:
            existing_content = ""
        
        # Remove old Stripe configuration if exists
        lines = existing_content.split("\n")
        filtered_lines = []
        skip_section = False
        
        for line in lines:
            if "# Stripe Configuration" in line or "# Stripe Product IDs" in line:
                skip_section = True
                continue
            elif skip_section and (line.startswith("STRIPE_") or not line.strip()):
                continue
            else:
                skip_section = False
                filtered_lines.append(line)
        
        # Add new Stripe configuration
        new_content = "\n".join(filtered_lines).strip() + "\n\n" + "\n".join(env_config) + "\n"
        
        # Write updated .env.example
        with open(env_example_path, "w") as f:
            f.write(new_content)
        
        print(f"\n✓ Updated {env_example_path}")
        
    except Exception as e:
        print(f"\n✗ Error updating .env.example: {e}")
    
    # Save results to JSON file
    try:
        output_path = Path(__file__).parent.parent / "config" / "stripe_products.json"
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"✓ Saved product configuration to {output_path}")
        
    except Exception as e:
        print(f"✗ Error saving JSON: {e}")
    
    print("\n" + "="*70)
    print("  Next Steps:")
    print("="*70)
    print("1. Copy the environment variables above to your .env file")
    print("2. Create a webhook endpoint in Stripe Dashboard:")
    print("   - URL: https://your-domain.com/api/billing/webhook")
    print("   - Events: checkout.session.completed, customer.subscription.*,")
    print("            invoice.payment_failed, customer.subscription.trial_will_end")
    print("3. Copy the webhook signing secret to STRIPE_WEBHOOK_SECRET")
    print("4. Test the billing flow with test card: 4242 4242 4242 4242")
    print("="*70 + "\n")


if __name__ == "__main__":
    bootstrap_stripe()

