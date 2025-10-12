#!/usr/bin/env python3
"""
Pilot onboarding CLI (Sprint 9 Release Candidate).

Creates tenants, imports Chart of Accounts, sets feature flags,
seeds users, and generates API tokens for pilot testing.

Usage:
    python scripts/pilot_onboard.py --template starter --tenant "Acme Corp"
    python scripts/pilot_onboard.py --template pro --tenant "Beta Inc"
    python scripts/pilot_onboard.py --template firm --tenant "Accounting Firm LLC"
"""
import argparse
import json
import secrets
import hashlib
from pathlib import Path
from datetime import datetime
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class PilotOnboarder:
    """Pilot tenant onboarding utility."""
    
    def __init__(self, template: str, tenant_name: str):
        self.template = template
        self.tenant_name = tenant_name
        self.tenant_id = self._generate_tenant_id()
        self.api_token = self._generate_api_token()
    
    def _generate_tenant_id(self) -> str:
        """Generate unique tenant ID."""
        # Slugify tenant name
        slug = self.tenant_name.lower().replace(' ', '-').replace(',', '').replace('.', '')
        return f"pilot-{slug}-{secrets.token_hex(4)}"
    
    def _generate_api_token(self) -> str:
        """Generate secure API token."""
        return f"sk_pilot_{secrets.token_urlsafe(32)}"
    
    def load_template(self) -> dict:
        """Load tenant template configuration."""
        templates = {
            "starter": {
                "tier": "starter",
                "autopost_enabled": False,
                "autopost_threshold": 0.90,
                "coldstart_min_labels": 3,
                "llm_tenant_cap_usd": 50,
                "max_transactions_per_month": 500,
                "features": {
                    "ml_classifier": True,
                    "llm_fallback": False,
                    "auto_rule_promotion": True,
                    "drift_detection": False,
                    "calibration": True
                },
                "coa_preset": "standard_small_business"
            },
            "pro": {
                "tier": "pro",
                "autopost_enabled": True,  # Opt-in for pro tier
                "autopost_threshold": 0.92,  # Stricter
                "coldstart_min_labels": 5,   # More conservative
                "llm_tenant_cap_usd": 100,
                "max_transactions_per_month": 2000,
                "features": {
                    "ml_classifier": True,
                    "llm_fallback": True,
                    "auto_rule_promotion": True,
                    "drift_detection": True,
                    "calibration": True
                },
                "coa_preset": "standard_professional_services"
            },
            "firm": {
                "tier": "firm",
                "autopost_enabled": True,
                "autopost_threshold": 0.95,  # Most conservative
                "coldstart_min_labels": 7,   # Highest
                "llm_tenant_cap_usd": 250,
                "max_transactions_per_month": 10000,
                "features": {
                    "ml_classifier": True,
                    "llm_fallback": True,
                    "auto_rule_promotion": True,
                    "drift_detection": True,
                    "calibration": True,
                    "multi_tenant_admin": True,
                    "advanced_reporting": True
                },
                "coa_preset": "gaap_accounting_firm"
            }
        }
        
        if self.template not in templates:
            raise ValueError(f"Unknown template: {self.template}. Choose: starter, pro, firm")
        
        return templates[self.template]
    
    def create_tenant(self, config: dict) -> dict:
        """Create tenant record."""
        tenant_record = {
            "tenant_id": self.tenant_id,
            "tenant_name": self.tenant_name,
            "tier": config["tier"],
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "config": {
                "autopost_enabled": config["autopost_enabled"],
                "autopost_threshold": config["autopost_threshold"],
                "coldstart_min_labels": config["coldstart_min_labels"],
                "llm_tenant_cap_usd": config["llm_tenant_cap_usd"],
                "max_transactions_per_month": config["max_transactions_per_month"]
            },
            "features": config["features"],
            "coa_preset": config["coa_preset"]
        }
        
        return tenant_record
    
    def import_coa(self, preset: str) -> list:
        """Import Chart of Accounts from preset."""
        coa_presets = {
            "standard_small_business": [
                {"code": "1000", "name": "Checking Account", "type": "Asset"},
                {"code": "1200", "name": "Accounts Receivable", "type": "Asset"},
                {"code": "1500", "name": "Inventory", "type": "Asset"},
                {"code": "2000", "name": "Accounts Payable", "type": "Liability"},
                {"code": "2100", "name": "Credit Card", "type": "Liability"},
                {"code": "3000", "name": "Owner's Equity", "type": "Equity"},
                {"code": "4000", "name": "Sales Revenue", "type": "Revenue"},
                {"code": "5000", "name": "Cost of Goods Sold", "type": "Expense"},
                {"code": "6000", "name": "Operating Expenses", "type": "Expense"},
                {"code": "6100", "name": "Rent", "type": "Expense"},
                {"code": "6200", "name": "Utilities", "type": "Expense"},
                {"code": "6300", "name": "Office Supplies", "type": "Expense"},
                {"code": "7000", "name": "Other Income", "type": "Revenue"},
                {"code": "8000", "name": "Other Expenses", "type": "Expense"}
            ],
            "standard_professional_services": [
                {"code": "1000", "name": "Operating Account", "type": "Asset"},
                {"code": "1050", "name": "Payroll Account", "type": "Asset"},
                {"code": "1200", "name": "Accounts Receivable", "type": "Asset"},
                {"code": "1300", "name": "Unbilled Receivables", "type": "Asset"},
                {"code": "2000", "name": "Accounts Payable", "type": "Liability"},
                {"code": "2100", "name": "Accrued Expenses", "type": "Liability"},
                {"code": "3000", "name": "Partner Capital", "type": "Equity"},
                {"code": "4000", "name": "Professional Fees", "type": "Revenue"},
                {"code": "4100", "name": "Consulting Revenue", "type": "Revenue"},
                {"code": "5000", "name": "Subcontractor Costs", "type": "Expense"},
                {"code": "6000", "name": "Salaries & Wages", "type": "Expense"},
                {"code": "6100", "name": "Payroll Taxes", "type": "Expense"},
                {"code": "6200", "name": "Professional Development", "type": "Expense"},
                {"code": "6300", "name": "Technology & Software", "type": "Expense"}
            ],
            "gaap_accounting_firm": [
                {"code": "1010", "name": "Operating Cash", "type": "Asset"},
                {"code": "1020", "name": "Client Trust Account", "type": "Asset"},
                {"code": "1200", "name": "Accounts Receivable", "type": "Asset"},
                {"code": "1210", "name": "Unbilled Time & Expenses", "type": "Asset"},
                {"code": "1500", "name": "Prepaid Expenses", "type": "Asset"},
                {"code": "1700", "name": "Fixed Assets", "type": "Asset"},
                {"code": "2000", "name": "Accounts Payable", "type": "Liability"},
                {"code": "2100", "name": "Accrued Liabilities", "type": "Liability"},
                {"code": "2200", "name": "Deferred Revenue", "type": "Liability"},
                {"code": "3000", "name": "Partner Equity", "type": "Equity"},
                {"code": "3100", "name": "Retained Earnings", "type": "Equity"},
                {"code": "4000", "name": "Audit & Assurance Fees", "type": "Revenue"},
                {"code": "4100", "name": "Tax Services", "type": "Revenue"},
                {"code": "4200", "name": "Advisory Services", "type": "Revenue"},
                {"code": "5000", "name": "Professional Staff Costs", "type": "Expense"},
                {"code": "6000", "name": "Partner Compensation", "type": "Expense"},
                {"code": "6100", "name": "Occupancy Costs", "type": "Expense"},
                {"code": "6200", "name": "Professional Liability Insurance", "type": "Expense"},
                {"code": "6300", "name": "Continuing Education", "type": "Expense"}
            ]
        }
        
        return coa_presets.get(preset, coa_presets["standard_small_business"])
    
    def seed_user(self) -> dict:
        """Create seed user for tenant."""
        return {
            "user_id": f"user-{secrets.token_hex(8)}",
            "email": f"pilot+{self.tenant_id}@example.com",
            "role": "admin",
            "tenant_id": self.tenant_id,
            "created_at": datetime.now().isoformat(),
            "api_token_hash": hashlib.sha256(self.api_token.encode()).hexdigest()
        }
    
    def onboard(self) -> dict:
        """Execute full onboarding flow."""
        print(f"━━━ Pilot Onboarding: {self.tenant_name} ━━━")
        print(f"Template: {self.template}")
        print()
        
        # Load template
        print("1. Loading template configuration...")
        config = self.load_template()
        print(f"   ✅ Loaded {config['tier']} template")
        
        # Create tenant
        print("2. Creating tenant record...")
        tenant = self.create_tenant(config)
        print(f"   ✅ Tenant ID: {self.tenant_id}")
        
        # Import CoA
        print("3. Importing Chart of Accounts...")
        coa = self.import_coa(config["coa_preset"])
        print(f"   ✅ Imported {len(coa)} accounts from {config['coa_preset']}")
        
        # Seed user
        print("4. Creating seed user...")
        user = self.seed_user()
        print(f"   ✅ User: {user['email']}")
        
        # Generate API token
        print("5. Generating API token...")
        print(f"   ✅ Token: {self.api_token}")
        
        print()
        print("━━━ Onboarding Complete ━━━")
        
        return {
            "tenant": tenant,
            "coa": coa,
            "user": user,
            "api_token": self.api_token
        }
    
    def export_config(self, result: dict, output_dir: Path):
        """Export onboarding config to JSON."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export tenant config
        tenant_file = output_dir / f"{self.tenant_id}_config.json"
        with open(tenant_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"\n📄 Config exported to: {tenant_file}")
        
        # Export .env snippet
        env_file = output_dir / f"{self.tenant_id}_env.txt"
        with open(env_file, "w") as f:
            f.write(f"# Environment variables for {self.tenant_name}\n")
            f.write(f"TENANT_ID={self.tenant_id}\n")
            f.write(f"API_TOKEN={self.api_token}\n")
            f.write(f"AUTOPOST_ENABLED={result['tenant']['config']['autopost_enabled']}\n")
            f.write(f"AUTOPOST_THRESHOLD={result['tenant']['config']['autopost_threshold']}\n")
        
        print(f"📄 .env snippet: {env_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Pilot tenant onboarding CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/pilot_onboard.py --template starter --tenant "Acme Corp"
  python scripts/pilot_onboard.py --template pro --tenant "Beta Inc"
  python scripts/pilot_onboard.py --template firm --tenant "CPA Firm LLC"
        """
    )
    
    parser.add_argument(
        "--template",
        required=True,
        choices=["starter", "pro", "firm"],
        help="Tenant template (starter, pro, firm)"
    )
    
    parser.add_argument(
        "--tenant",
        required=True,
        help="Tenant name (e.g., 'Acme Corp')"
    )
    
    parser.add_argument(
        "--output-dir",
        default="pilot_configs",
        help="Output directory for configs (default: pilot_configs)"
    )
    
    args = parser.parse_args()
    
    # Run onboarding
    onboarder = PilotOnboarder(args.template, args.tenant)
    result = onboarder.onboard()
    
    # Export config
    output_dir = Path(args.output_dir)
    onboarder.export_config(result, output_dir)


if __name__ == "__main__":
    main()

