#!/usr/bin/env python3
"""
QuickBooks Online environment verification script.

Usage:
    python scripts/check_qbo_env.py

Checks:
- Required QBO environment variables present
- QBO_BASE URL format correct
- Environment detection (sandbox vs production)
"""

import os
import sys

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def check_env_var(name: str, required: bool = True) -> tuple[bool, str]:
    """Check if environment variable exists and is non-empty."""
    value = os.getenv(name)
    
    if not value:
        if required:
            return False, f"{RED}❌{RESET} {name} not set"
        else:
            return True, f"{YELLOW}⚠️{RESET}  {name} not set (optional)"
    
    # Mask sensitive values
    if "SECRET" in name or "CLIENT_ID" in name:
        masked = value[:8] + "..." if len(value) > 8 else "***"
        return True, f"{GREEN}✅{RESET} {name} present ({masked})"
    else:
        return True, f"{GREEN}✅{RESET} {name} present ({value})"


def detect_environment(qbo_base: str) -> str:
    """Detect if QBO is configured for sandbox or production."""
    if not qbo_base:
        return "UNKNOWN"
    
    if "sandbox" in qbo_base.lower():
        return "SANDBOX"
    elif "quickbooks.api.intuit.com" in qbo_base:
        return "PRODUCTION"
    else:
        return "UNKNOWN"


def main():
    """Run QuickBooks environment verification."""
    
    print("\n" + "="*70)
    print("  QuickBooks Environment Verification")
    print("="*70 + "\n")
    
    checks = []
    all_passed = True
    
    # Required variables
    required_vars = [
        "QBO_CLIENT_ID",
        "QBO_CLIENT_SECRET",
        "QBO_REDIRECT_URI",
        "QBO_SCOPES"
    ]
    
    # Optional but recommended
    optional_vars = [
        "QBO_BASE",
        "QBO_AUTH_BASE",
        "QBO_ENVIRONMENT"
    ]
    
    # Check required variables
    print(f"{BLUE}Required Variables:{RESET}\n")
    for var in required_vars:
        passed, message = check_env_var(var, required=True)
        print(f"  {message}")
        if not passed:
            all_passed = False
        checks.append((var, passed))
    
    print()
    
    # Check optional variables
    print(f"{BLUE}Optional Variables:{RESET}\n")
    for var in optional_vars:
        passed, message = check_env_var(var, required=False)
        print(f"  {message}")
        checks.append((var, passed))
    
    print()
    
    # Detect environment
    qbo_base = os.getenv("QBO_BASE", "")
    qbo_env = os.getenv("QBO_ENVIRONMENT", "")
    
    detected_env = detect_environment(qbo_base)
    
    print(f"{BLUE}Environment Detection:{RESET}\n")
    if qbo_env:
        print(f"  QBO_ENVIRONMENT: {qbo_env.upper()}")
    if qbo_base:
        print(f"  QBO_BASE: {qbo_base}")
    print(f"  Detected: {YELLOW if detected_env == 'UNKNOWN' else GREEN}{detected_env}{RESET}")
    
    if detected_env == "UNKNOWN" and qbo_base:
        print(f"  {YELLOW}⚠️{RESET}  Could not determine environment from QBO_BASE")
        print(f"     Expected: https://sandbox-quickbooks.api.intuit.com (SANDBOX)")
        print(f"            or https://quickbooks.api.intuit.com (PRODUCTION)")
    
    print()
    
    # Verify redirect URI format
    redirect_uri = os.getenv("QBO_REDIRECT_URI", "")
    if redirect_uri:
        print(f"{BLUE}Redirect URI Check:{RESET}\n")
        if redirect_uri.startswith("https://"):
            print(f"  {GREEN}✅{RESET} HTTPS enforced")
        elif redirect_uri.startswith("http://localhost"):
            print(f"  {YELLOW}⚠️{RESET}  localhost redirect (development only)")
        else:
            print(f"  {RED}❌{RESET} Redirect URI should use HTTPS in production")
            all_passed = False
        
        if redirect_uri.endswith("/api/auth/qbo/callback"):
            print(f"  {GREEN}✅{RESET} Callback path correct")
        else:
            print(f"  {YELLOW}⚠️{RESET}  Callback path may not match expected: /api/auth/qbo/callback")
        
        print()
    
    # Verify scopes
    scopes = os.getenv("QBO_SCOPES", "")
    if scopes:
        print(f"{BLUE}Scopes Check:{RESET}\n")
        if "com.intuit.quickbooks.accounting" in scopes:
            print(f"  {GREEN}✅{RESET} Accounting scope present")
        else:
            print(f"  {RED}❌{RESET} Required scope missing: com.intuit.quickbooks.accounting")
            all_passed = False
        print()
    
    # Summary
    print("="*70)
    if all_passed and detected_env != "UNKNOWN":
        print(f"  {GREEN}✅ All checks passed{RESET}")
        print("="*70 + "\n")
        return 0
    elif all_passed and detected_env == "UNKNOWN":
        print(f"  {YELLOW}⚠️  All required variables present, but environment unclear{RESET}")
        print("="*70 + "\n")
        return 0
    else:
        print(f"  {RED}❌ Some checks failed{RESET}")
        print("="*70 + "\n")
        print(f"Fix missing variables and re-run: python scripts/check_qbo_env.py\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

