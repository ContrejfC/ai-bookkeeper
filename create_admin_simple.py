#!/usr/bin/env python3
"""
Simple script to create admin user.
Run this in Render shell or locally with DATABASE_URL.
"""
import os
import sys
from pathlib import Path
import uuid
from datetime import datetime

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def create_admin_simple():
    """Create admin user with minimal dependencies."""
    try:
        from app.db.session import get_db_context
        from app.db.models import UserDB
        from app.auth.security import get_password_hash
        
        print("🔗 Connecting to database...")
        
        with get_db_context() as session:
            # Check if user exists
            existing = session.query(UserDB).filter(UserDB.email == "admin@example.com").first()
            if existing:
                print(f"✅ User exists: {existing.email} (role: {existing.role})")
                if existing.password_hash:
                    print("✅ User has password - login should work!")
                    return True
                else:
                    print("⚠️  User exists but no password - adding password...")
                    existing.password_hash = get_password_hash("admin123")
                    session.commit()
                    print("✅ Password added successfully!")
                    return True
            
            # Create new user
            print("👤 Creating new admin user...")
            user_id = f"user-admin-{uuid.uuid4().hex[:8]}"
            password_hash = get_password_hash("admin123")
            
            admin_user = UserDB(
                user_id=user_id,
                email="admin@example.com",
                password_hash=password_hash,
                role="owner",
                is_active=True
            )
            
            session.add(admin_user)
            session.commit()
            
            print("✅ Admin user created successfully!")
            print(f"   Email: admin@example.com")
            print(f"   Password: admin123")
            print(f"   Role: owner")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_admin_simple()
