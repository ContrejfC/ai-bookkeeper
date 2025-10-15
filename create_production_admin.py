#!/usr/bin/env python3
"""
Create admin user for production database.
Run this script with your production DATABASE_URL to create the admin user.
"""
import os
import sys
from pathlib import Path
import uuid
from datetime import datetime

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def create_production_admin():
    """Create admin@example.com user for production."""
    
    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL environment variable not set")
        print()
        print("To get your DATABASE_URL:")
        print("1. Go to https://dashboard.render.com")
        print("2. Find your 'ai-bookkeeper-web' service")
        print("3. Go to Environment tab")
        print("4. Copy the DATABASE_URL value")
        print()
        print("Then run:")
        print("export DATABASE_URL='your_database_url_here'")
        print("python create_production_admin.py")
        return False
    
    try:
        from app.db.session import get_db_context
        from app.db.models import UserDB
        from app.auth.security import get_password_hash
        
        print(f"🔗 Connecting to production database...")
        print(f"   Database: {db_url.split('@')[1].split('/')[0] if '@' in db_url else 'local'}")
        
        with get_db_context() as session:
            # Check if user already exists
            existing = session.query(UserDB).filter(UserDB.email == "admin@example.com").first()
            if existing:
                print(f"✅ Admin user already exists!")
                print(f"   User ID: {existing.user_id}")
                print(f"   Email: {existing.email}")
                print(f"   Role: {existing.role}")
                print(f"   Active: {existing.is_active}")
                return True
            
            # Create new admin user
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
            print(f"   User ID: {user_id}")
            print(f"   Email: admin@example.com")
            print(f"   Password: admin123")
            print(f"   Role: owner")
            print()
            print("🔑 Login credentials for production:")
            print("   Email: admin@example.com")
            print("   Password: admin123")
            print("   OR use Dev Magic Link with: admin@example.com")
            print()
            print("🌐 Test your login at:")
            print("   https://ai-bookkeeper-nine.vercel.app/login")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = create_production_admin()
    sys.exit(0 if success else 1)