#!/usr/bin/env python3
"""
Demo reset script for AI Bookkeeper.

Wipes and reseeds the SQLite demo database for fresh walkthrough sessions.
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import engine
from app.db.models import Base
import subprocess


def reset_demo():
    """Reset demo database to clean state."""
    print("🔄 Resetting demo environment...")
    
    # 1. Drop all tables
    print("  • Dropping all tables...")
    Base.metadata.drop_all(engine)
    print("  ✅ Tables dropped")
    
    # 2. Recreate tables
    print("  • Recreating tables...")
    Base.metadata.create_all(engine)
    print("  ✅ Tables created")
    
    # 3. Seed demo data
    print("  • Seeding demo data...")
    try:
        subprocess.run([sys.executable, "scripts/seed_demo_data.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to seed demo data: {e}")
        return False
    
    # 4. Seed demo receipts
    print("  • Seeding demo receipts...")
    try:
        subprocess.run([sys.executable, "scripts/seed_demo_receipts.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to seed receipts: {e}")
        return False
    
    print("\n✅ Demo environment reset complete!")
    print("\n📋 You can now:")
    print("   1. Start the server: python3 -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000")
    print("   2. Login with:")
    print("      • Owner: owner@pilot-smb-001.demo / demo-password-123")
    print("      • Staff: staff@pilot-smb-001.demo / demo-password-123")
    print("   3. Review 8 transactions with full reason coverage")
    print("   4. View 6 receipts with bounding box overlays")
    
    return True


if __name__ == "__main__":
    success = reset_demo()
    sys.exit(0 if success else 1)

