#!/usr/bin/env python3
"""
Production environment verification script.

Usage:
    python scripts/verify_prod_env.py

Validates all required LIVE environment variables are present and correctly formatted.
"""

import os
import sys

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def check_stripe_key(value: str, key_type: str) -> tuple[bool, str]:
    """Validate Stripe key format."""
    if key_type == "SECRET":
        if not value.startswith("sk_"):
            return False, "should start with sk_"
        if value.startswith("sk_test_"):
            return False, "using TEST key (should be sk_live_)"
        if not value.startswith("sk_live_"):
            return False, "unknown format"
        return True, "LIVE"
    
    elif key_type == "PUBLISHABLE":
        if not value.startswith("pk_"):
            return False, "should start with pk_"
        if value.startswith("pk_test_"):
            return False, "using TEST key (should be pk_live_)"
        if not value.startswith("pk_live_"):
            return False, "unknown format"
        return True, "LIVE"
    
    elif key_type == "WEBHOOK":
        if not value.startswith("whsec_"):
            return False, "should start with whsec_"
        return True, "OK"
    
    return True, "OK"


def check_url(value: str) -> tuple[bool, str]:
    """Validate URL format."""
    if not value.startswith("http"):
        return False, "should start with http:// or https://"
    if not value.startswith("https://") and "localhost" not in value:
        return False, "should use HTTPS in production"
    return True, "OK"


def check_env_var(name: str, validator=None, required: bool = True) -> tuple[bool, str, str]:
    """
    Check environment variable.
    
    Returns:
        (passed, status_symbol, message)
    """
    value = os.getenv(name)
    
    if not value:
        if required:
            return False, f"{RED}❌{RESET}", f"{name:<30} Missing (required)"
        else:
            return True, f"{YELLOW}⚠️{RESET} ", f"{name:<30} Not set (optional)"
    
    # Run validator if provided
    if validator:
        valid, detail = validator(value)
        if not valid:
            return False, f"{RED}❌{RESET}", f"{name:<30} Present but {detail}"
        else:
            # Mask sensitive values
            if "SECRET" in name or "KEY" in name and "PUBLISHABLE" not in name:
                masked = value[:8] + "..." if len(value) > 8 else "***"
                return True, f"{GREEN}✅{RESET}", f"{name:<30} {masked} ({detail})"
            else:
                return True, f"{GREEN}✅{RESET}", f"{name:<30} {detail}"
    else:
        # Basic check (just presence)
        masked = value[:30] + "..." if len(value) > 30 else value
        return True, f"{GREEN}✅{RESET}", f"{name:<30} {masked}"


def main():
    """Run production environment verification."""
    
    print("\n" + "="*80)
    print("  Production Environment Verification")
    print("="*80 + "\n")
    
    all_passed = True
    categories = {}
    
    # Define checks by category
    categories["Stripe (LIVE Mode)"] = [
        ("STRIPE_SECRET_KEY", lambda v: check_stripe_key(v, "SECRET"), True),
        ("STRIPE_PUBLISHABLE_KEY", lambda v: check_stripe_key(v, "PUBLISHABLE"), True),
        ("STRIPE_WEBHOOK_SECRET", lambda v: check_stripe_key(v, "WEBHOOK"), True),
        ("STRIPE_PRODUCT_STARTER", None, True),
        ("STRIPE_PRICE_STARTER", None, True),
        ("STRIPE_PRODUCT_PRO", None, True),
        ("STRIPE_PRICE_PRO", None, True),
        ("STRIPE_PRODUCT_FIRM", None, True),
        ("STRIPE_PRICE_FIRM", None, True),
    ]
    
    categories["QuickBooks Online (Production)"] = [
        ("QBO_CLIENT_ID", None, True),
        ("QBO_CLIENT_SECRET", None, True),
        ("QBO_REDIRECT_URI", check_url, True),
        ("QBO_SCOPES", None, True),
        ("QBO_BASE", check_url, False),
        ("QBO_ENVIRONMENT", None, False),
    ]
    
    categories["Application"] = [
        ("DATABASE_URL", lambda v: (v.startswith("postgresql://") or v.startswith("postgres://"), 
                                    "PostgreSQL" if v.startswith("postgres") else "Invalid format"), True),
        ("BASE_URL", check_url, False),
        ("PUBLIC_BASE_URL", check_url, False),
    ]
    
    categories["Monitoring (Optional)"] = [
        ("SENTRY_DSN", None, False),
        ("LOG_LEVEL", None, False),
    ]
    
    # Run checks
    for category, checks in categories.items():
        print(f"{BLUE}{category}:{RESET}\n")
        
        for check in checks:
            var_name = check[0]
            validator = check[1] if len(check) > 1 else None
            required = check[2] if len(check) > 2 else True
            
            passed, symbol, message = check_env_var(var_name, validator, required)
            print(f"  {symbol}  {message}")
            
            if not passed and required:
                all_passed = False
        
        print()
    
    # Summary
    print("="*80)
    if all_passed:
        print(f"  {GREEN}✅ All required checks passed - ready for production{RESET}")
        print("="*80 + "\n")
        return 0
    else:
        print(f"  {RED}❌ Some required checks failed - NOT ready for production{RESET}")
        print("="*80 + "\n")
        print("Fix missing/invalid variables and re-run: python scripts/verify_prod_env.py\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

