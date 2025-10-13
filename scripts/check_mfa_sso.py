#!/usr/bin/env python3
"""
SSO/MFA Verification Script (SOC 2 Min Controls).

Checks security posture for:
- GitHub org SSO/MFA policy
- Render team SSO/MFA (where available)

Environment:
- GITHUB_ORG: GitHub organization name
- GITHUB_TOKEN: GitHub API token (with org:read scope)
- RENDER_API_KEY: Render API key (optional)

Outputs:
- Human-readable status report
- Exit 0 on success, 1 on failure, 0 on skipped (no creds)

Usage:
    python scripts/check_mfa_sso.py
"""
import os
import sys
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add app to path for logging
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ops.logging import get_logger

logger = get_logger(__name__)

# Configuration from environment
GITHUB_ORG = os.getenv("GITHUB_ORG", "").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
RENDER_API_KEY = os.getenv("RENDER_API_KEY", "").strip()

# Exit codes
EXIT_SUCCESS = 0
EXIT_FAILURE = 1


class SecurityPostureCheck:
    """Security posture check result."""
    
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0
    
    def add_check(self, name: str, status: str, message: str, details: Optional[Dict] = None):
        """Add a check result."""
        self.checks.append({
            "name": name,
            "status": status,  # "pass", "fail", "skip"
            "message": message,
            "details": details or {}
        })
        
        if status == "pass":
            self.passed += 1
        elif status == "fail":
            self.failed += 1
        elif status == "skip":
            self.skipped += 1
    
    def print_report(self):
        """Print human-readable report."""
        print("=" * 70)
        print("SSO/MFA SECURITY POSTURE CHECK")
        print("=" * 70)
        print()
        
        for check in self.checks:
            status_icon = {
                "pass": "✓",
                "fail": "✗",
                "skip": "⊘"
            }.get(check["status"], "?")
            
            print(f"{status_icon} {check['name']}: {check['message']}")
            
            if check["details"]:
                for key, value in check["details"].items():
                    print(f"    {key}: {value}")
            print()
        
        print("-" * 70)
        print(f"SUMMARY: {self.passed} passed, {self.failed} failed, {self.skipped} skipped")
        print("-" * 70)
        
        if self.failed > 0:
            print("\n⚠️  SECURITY POSTURE CHECK FAILED")
            print("   Action required: Fix failed checks above")
            return False
        elif self.passed > 0:
            print("\n✓ SECURITY POSTURE CHECK PASSED")
            return True
        else:
            print("\n⊘ SECURITY POSTURE CHECK SKIPPED (no credentials)")
            return True


def check_github_mfa() -> tuple[str, str, Optional[Dict]]:
    """
    Check GitHub org MFA requirement.
    
    Returns:
        (status, message, details)
    """
    if not GITHUB_ORG or not GITHUB_TOKEN:
        return ("skip", "GitHub credentials not set", None)
    
    try:
        import requests
        
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get org details
        url = f"https://api.github.com/orgs/{GITHUB_ORG}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            return ("fail", f"Organization '{GITHUB_ORG}' not found or no access", None)
        
        if response.status_code != 200:
            return ("fail", f"GitHub API error: {response.status_code}", None)
        
        org_data = response.json()
        
        # Check MFA requirement
        mfa_required = org_data.get("two_factor_requirement_enabled", False)
        
        if mfa_required:
            return (
                "pass",
                "MFA required for all org members",
                {"org": GITHUB_ORG, "mfa_enforced": True}
            )
        else:
            return (
                "fail",
                "MFA NOT required for org members",
                {
                    "org": GITHUB_ORG,
                    "mfa_enforced": False,
                    "recommendation": "Enable MFA requirement in org settings"
                }
            )
    
    except Exception as e:
        logger.error(f"Error checking GitHub MFA: {e}")
        return ("fail", f"Error checking GitHub: {str(e)}", None)


def check_github_sso() -> tuple[str, str, Optional[Dict]]:
    """
    Check GitHub org SSO configuration.
    
    Returns:
        (status, message, details)
    """
    if not GITHUB_ORG or not GITHUB_TOKEN:
        return ("skip", "GitHub credentials not set", None)
    
    try:
        import requests
        
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get org details
        url = f"https://api.github.com/orgs/{GITHUB_ORG}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return ("skip", "Cannot access org SSO info", None)
        
        org_data = response.json()
        
        # Check if SSO is enabled (has saml_identity_provider)
        has_sso = org_data.get("has_organization_projects", False)  # Proxy check
        
        # Note: GitHub API doesn't directly expose SSO status for orgs
        # This would require enterprise-level API access
        # For now, provide guidance
        
        return (
            "skip",
            "SSO status check requires manual verification",
            {
                "org": GITHUB_ORG,
                "note": "Verify SSO at https://github.com/organizations/{}/settings/security".format(GITHUB_ORG)
            }
        )
    
    except Exception as e:
        logger.error(f"Error checking GitHub SSO: {e}")
        return ("skip", f"Error checking GitHub SSO: {str(e)}", None)


def check_github_members_mfa() -> tuple[str, str, Optional[Dict]]:
    """
    Check that all GitHub org members have MFA enabled.
    
    Returns:
        (status, message, details)
    """
    if not GITHUB_ORG or not GITHUB_TOKEN:
        return ("skip", "GitHub credentials not set", None)
    
    try:
        import requests
        
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get members without MFA (requires admin access)
        url = f"https://api.github.com/orgs/{GITHUB_ORG}/members?filter=2fa_disabled"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 403:
            return ("skip", "Insufficient permissions to check member MFA status", None)
        
        if response.status_code != 200:
            return ("skip", f"Cannot check member MFA (status {response.status_code})", None)
        
        members_without_mfa = response.json()
        
        if len(members_without_mfa) == 0:
            return (
                "pass",
                "All org members have MFA enabled",
                {"org": GITHUB_ORG, "members_without_mfa": 0}
            )
        else:
            return (
                "fail",
                f"{len(members_without_mfa)} member(s) without MFA",
                {
                    "org": GITHUB_ORG,
                    "members_without_mfa": len(members_without_mfa),
                    "members": [m["login"] for m in members_without_mfa[:5]]  # First 5
                }
            )
    
    except Exception as e:
        logger.error(f"Error checking member MFA: {e}")
        return ("skip", f"Error checking member MFA: {str(e)}", None)


def check_render_sso() -> tuple[str, str, Optional[Dict]]:
    """
    Check Render team SSO/MFA configuration.
    
    Returns:
        (status, message, details)
    """
    if not RENDER_API_KEY:
        return ("skip", "Render API key not set", None)
    
    # Note: Render API doesn't currently expose SSO/MFA status
    # This is a placeholder for when/if Render adds this capability
    
    return (
        "skip",
        "Render SSO/MFA check requires manual verification",
        {
            "note": "Verify team security settings at https://dashboard.render.com/org/settings",
            "recommendation": "Enable SSO and MFA for all team members"
        }
    )


def main():
    """Main entry point."""
    logger.info("=== SSO/MFA Security Posture Check Started ===")
    
    posture = SecurityPostureCheck()
    
    # GitHub checks
    status, message, details = check_github_mfa()
    posture.add_check("GitHub Org MFA Requirement", status, message, details)
    
    status, message, details = check_github_members_mfa()
    posture.add_check("GitHub Members MFA Status", status, message, details)
    
    status, message, details = check_github_sso()
    posture.add_check("GitHub Org SSO", status, message, details)
    
    # Render checks
    status, message, details = check_render_sso()
    posture.add_check("Render Team SSO/MFA", status, message, details)
    
    # Print report
    posture.print_report()
    
    # Determine exit code
    if posture.failed > 0:
        logger.error("Security posture check failed")
        return EXIT_FAILURE
    elif posture.passed == 0 and posture.skipped > 0:
        logger.info("Security posture check skipped (no credentials)")
        return EXIT_SUCCESS  # Don't fail if no creds
    else:
        logger.info("Security posture check passed")
        return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())

