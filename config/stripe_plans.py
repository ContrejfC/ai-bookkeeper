"""
Stripe plan configuration loader.

Loads plan details from stripe_price_map.json and substitutes env vars.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import re

_plan_cache: Optional[Dict[str, Any]] = None


def load_stripe_plans() -> Dict[str, Any]:
    """
    Load Stripe plan configuration from JSON file.
    
    Replaces ${ENV_VAR} placeholders with actual environment variable values.
    
    Returns:
        Dict with plan configurations
        
    Example:
        {
            "starter": {
                "display_name": "Starter",
                "price_id_monthly": "price_123...",
                "entitlements": {"entity_limit": 1, ...},
                ...
            },
            ...
        }
    """
    global _plan_cache
    
    if _plan_cache is not None:
        return _plan_cache
    
    config_path = Path(__file__).parent / "stripe_price_map.json"
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Substitute environment variables
    config_str = json.dumps(config)
    
    # Find all ${VAR_NAME} patterns
    def replace_env_var(match):
        var_name = match.group(1)
        value = os.getenv(var_name)
        if value is None:
            # Return placeholder if env var not set (for dev/testing)
            return f"${{{{STRIPE_PRICE_NOT_SET_{var_name}}}}}"
        return value
    
    config_str = re.sub(r'\$\{([^}]+)\}', replace_env_var, config_str)
    
    _plan_cache = json.loads(config_str)
    return _plan_cache


def get_plan_config(plan_code: str) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific plan.
    
    Args:
        plan_code: Plan code (starter, team, firm, pilot)
        
    Returns:
        Plan configuration dict or None if not found
    """
    plans = load_stripe_plans()
    return plans.get("plans", {}).get(plan_code)


def get_price_id(plan_code: str, billing_cycle: str = "monthly") -> Optional[str]:
    """
    Get Stripe price ID for a plan and billing cycle.
    
    Args:
        plan_code: Plan code (starter, team, firm, pilot)
        billing_cycle: "monthly" or "annual"
        
    Returns:
        Stripe price ID (price_xxx) or None
    """
    plan = get_plan_config(plan_code)
    if not plan:
        return None
    
    field = f"price_id_{billing_cycle}"
    return plan.get(field)


def get_entitlements(plan_code: str) -> Optional[Dict[str, Any]]:
    """
    Get entitlement limits for a plan.
    
    Args:
        plan_code: Plan code (starter, team, firm, pilot)
        
    Returns:
        Dict with entity_limit, monthly_tx_cap, trial_days, features
    """
    plan = get_plan_config(plan_code)
    if not plan:
        return None
    
    return plan.get("entitlements")


def get_overage_price_id(plan_code: str) -> Optional[str]:
    """
    Get overage (metered) price ID for a plan.
    
    Args:
        plan_code: Plan code
        
    Returns:
        Stripe price ID for overage billing or None
    """
    plan = get_plan_config(plan_code)
    if not plan:
        return None
    
    return plan.get("overage_price_id")


def get_addon_price_id(plan_code: str, addon_name: str) -> Optional[str]:
    """
    Get price ID for an add-on.
    
    Args:
        plan_code: Plan code
        addon_name: Add-on name (e.g., "additional_entity", "sso")
        
    Returns:
        Stripe price ID or None
    """
    plan = get_plan_config(plan_code)
    if not plan:
        return None
    
    addons = plan.get("addons", {})
    return addons.get(addon_name)


def get_enforcement_rules() -> Dict[str, Any]:
    """
    Get entitlement enforcement rules.
    
    Returns:
        Dict with soft_limit_threshold, hard_limit_threshold, grace_period_days
    """
    plans = load_stripe_plans()
    return plans.get("enforcement_rules", {
        "soft_limit_threshold": 0.8,
        "hard_limit_threshold": 1.0,
        "grace_period_days": 3
    })


# Convenience function for API routes
def validate_plan_code(plan_code: str) -> bool:
    """
    Check if plan code is valid.
    
    Args:
        plan_code: Plan code to validate
        
    Returns:
        True if plan exists
    """
    return get_plan_config(plan_code) is not None

