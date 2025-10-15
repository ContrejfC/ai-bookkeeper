#!/usr/bin/env python3
"""
Connect to production database and create admin user.
Run this locally with the DATABASE_URL.
"""
import os
import sys
import psycopg2
from urllib.parse import urlparse

def create_admin_user():
    """Create admin user directly in production database."""
    
    # Your DATABASE_URL
    database_url = "postgresql://ai_bookkeeper_user:q69x2a1Z3iHsKbIKuosqXxrCeTI8i5Uk@dpg-d3lggv95pdvs73ag3amg-a/ai_bookkeeper"
    
    try:
        # Parse the database URL
        result = urlparse(database_url)
        
        # Connect to database
        print("🔗 Connecting to production database...")
        conn = psycopg2.connect(
            host=result.hostname,
            port=result.port,
            database=result.path[1:],  # Remove leading slash
            user=result.username,
            password=result.password
        )
        
        cur = conn.cursor()
        
        # Check if user exists
        print("👤 Checking if admin user exists...")
        cur.execute("SELECT user_id, email, role, password_hash FROM users WHERE email = %s", ("admin@example.com",))
        existing = cur.fetchone()
        
        if existing:
            user_id, email, role, password_hash = existing
            print(f"✅ User exists: {email} (role: {role})")
            
            if password_hash:
                print("✅ User has password - login should work!")
            else:
                print("⚠️  User exists but no password - adding password...")
                # Add password hash for 'admin123'
                password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/9Yz8x2e'
                cur.execute("""
                    UPDATE users 
                    SET password_hash = %s 
                    WHERE email = %s
                """, (password_hash, "admin@example.com"))
                conn.commit()
                print("✅ Password added successfully!")
        else:
            print("👤 Creating new admin user...")
            # Create new user with password hash for 'admin123'
            password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/9Yz8x2e'
            
            cur.execute("""
                INSERT INTO users (user_id, email, password_hash, role, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, ("user-admin-001", "admin@example.com", password_hash, "owner", True))
            
            conn.commit()
            print("✅ Admin user created successfully!")
        
        print()
        print("🔑 Login credentials:")
        print("   Email: admin@example.com")
        print("   Password: admin123")
        print("   OR use Dev Magic Link with: admin@example.com")
        print()
        print("🌐 Test your login at:")
        print("   https://ai-bookkeeper-nine.vercel.app/login")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_admin_user()
