#!/usr/bin/env python3
"""
Create a dev user for testing the Next.js frontend.

Creates user: Dev@dev.com / password: Dev
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_context
from app.db.models import UserDB, UserTenantDB
import bcrypt
import uuid
from datetime import datetime

def create_dev_user():
    with get_db_context() as session:
        try:
            # Check if user exists
            existing = session.query(UserDB).filter_by(email="Dev@dev.com").first()
            if existing:
                print(f"✓ Dev user already exists: {existing.user_id}")
                print(f"  Email: {existing.email}")
                print(f"  Role: {existing.role}")
                return
            
            # Create user (bypass password strength check for dev)
            user_id = f"user-dev-{uuid.uuid4().hex[:8]}"
            # Hash password directly with bcrypt
            salt = bcrypt.gensalt(rounds=12)
            password_hash = bcrypt.hashpw("Dev".encode('utf-8'), salt).decode('utf-8')
            
            user = UserDB(
                user_id=user_id,
                email="Dev@dev.com",
                password_hash=password_hash,
                role="owner",
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            session.add(user)
            
            print("✓ Dev user created successfully!")
            print(f"  User ID: {user_id}")
            print(f"  Email: Dev@dev.com")
            print(f"  Password: Dev")
            print(f"  Role: owner")
            print()
            print("You can now login at: http://localhost:3000/login")
            print("  - Uncheck 'Dev mode' checkbox")
            print("  - Email: Dev@dev.com")
            print("  - Password: Dev")
        
        except Exception as e:
            print(f"✗ Error creating dev user: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    create_dev_user()

