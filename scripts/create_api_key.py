#!/usr/bin/env python3
"""
Create API key for GPT Actions authentication.

Usage:
    python scripts/create_api_key.py --tenant TENANT_ID --name "GPT Actions Key"

Outputs:
    Plaintext API key (shown ONCE - save it securely)
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_context
from app.services.api_key import APIKeyService


def main():
    """Create API key."""
    parser = argparse.ArgumentParser(description="Create API key for GPT Actions")
    parser.add_argument("--tenant", required=True, help="Tenant ID")
    parser.add_argument("--name", default="GPT Actions", help="Key description")
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  AI Bookkeeper - Create API Key")
    print("="*70 + "\n")
    
    with get_db_context() as db:
        service = APIKeyService(db)
        
        # Create API key
        token, api_key = service.create_api_key(
            tenant_id=args.tenant,
            name=args.name
        )
        
        print(f"✓ API Key created successfully!")
        print()
        print(f"Tenant ID: {args.tenant}")
        print(f"Name: {api_key.name}")
        print(f"Created: {api_key.created_at}")
        print()
        print("="*70)
        print("  🔑 API KEY (SAVE THIS - SHOWN ONCE ONLY)")
        print("="*70)
        print()
        print(f"  {token}")
        print()
        print("="*70)
        print()
        print("Next Steps:")
        print("1. Copy the API key above")
        print("2. In ChatGPT GPT Builder:")
        print("   - Go to Configure → Actions → Authentication")
        print("   - Select: API Key")
        print("   - Auth Type: Bearer")
        print("   - API Key: Paste the token above")
        print("3. Test connection with GET /actions")
        print()
        print("⚠️  Keep this key secure. It grants full access to your tenant.")
        print("   To revoke: python scripts/revoke_api_key.py --token <token>")
        print()


if __name__ == "__main__":
    main()

