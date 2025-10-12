#!/usr/bin/env python3
"""
Database smoke test for ops/DevOps (Sprint 9 Stage A).

Quick connectivity test without starting the full API server.
Uses DATABASE_URL from environment or .env file.

Usage:
    python scripts/db_smoke.py
    
Expected output:
    ✅ DB connection: OK
    ✅ SELECT 1: OK
    ✅ Database type: postgresql
    ✅ Connection time: 0.12s
"""
import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from config.settings import settings


def test_database_connection():
    """Test database connectivity and basic query."""
    print("\n" + "="*80)
    print("DATABASE SMOKE TEST")
    print("="*80 + "\n")
    
    # Show configuration
    db_url = settings.DATABASE_URL
    db_type = "postgresql" if "postgresql" in db_url else "sqlite" if "sqlite" in db_url else "unknown"
    
    # Mask password in URL for display
    display_url = db_url
    if "@" in db_url and ":" in db_url.split("@")[0]:
        parts = db_url.split("@")
        user_pass = parts[0].split("://")[1]
        if ":" in user_pass:
            user = user_pass.split(":")[0]
            display_url = db_url.replace(user_pass, f"{user}:****")
    
    print(f"Database URL: {display_url}")
    print(f"Database type: {db_type}")
    print("")
    
    # Test connection
    start_time = time.time()
    
    try:
        # Create engine
        print("Attempting connection...")
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            echo=False
        )
        
        # Test connection with SELECT 1
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            
            if row and row[0] == 1:
                connection_time = time.time() - start_time
                
                print("\n" + "-"*80)
                print("RESULTS")
                print("-"*80 + "\n")
                print(f"✅ DB connection: OK")
                print(f"✅ SELECT 1: OK (returned {row[0]})")
                print(f"✅ Database type: {db_type}")
                print(f"✅ Connection time: {connection_time:.2f}s")
                print("")
                
                # Additional checks for PostgreSQL
                if db_type == "postgresql":
                    try:
                        version_result = conn.execute(text("SELECT version()"))
                        version = version_result.fetchone()[0]
                        print(f"✅ PostgreSQL version: {version.split(',')[0]}")
                    except Exception:
                        pass
                
                print("\n" + "="*80)
                print("DATABASE SMOKE TEST: PASSED ✅")
                print("="*80 + "\n")
                
                return 0
            else:
                print("\n❌ SELECT 1 returned unexpected value")
                return 1
                
    except Exception as e:
        connection_time = time.time() - start_time
        
        print("\n" + "-"*80)
        print("RESULTS")
        print("-"*80 + "\n")
        print(f"❌ DB connection: FAILED")
        print(f"❌ Error: {str(e)}")
        print(f"⏱  Connection attempt time: {connection_time:.2f}s")
        print("")
        
        # Provide helpful error messages
        error_str = str(e).lower()
        print("TROUBLESHOOTING:")
        
        if "no module named 'psycopg2'" in error_str:
            print("  → Install PostgreSQL driver: pip install psycopg2-binary")
        elif "connection refused" in error_str or "could not connect" in error_str:
            print("  → PostgreSQL is not running")
            print("  → Start with: docker compose up -d postgres")
            print("  → Or: brew services start postgresql@15")
        elif "authentication failed" in error_str or "password" in error_str:
            print("  → Check DATABASE_URL credentials")
            print("  → Default: postgresql://bookkeeper:bookkeeper_dev_pass@localhost:5432/aibookkeeper")
        elif "database" in error_str and "does not exist" in error_str:
            print("  → Create database: createdb aibookkeeper")
        else:
            print(f"  → Check database configuration and logs")
        
        print("")
        print("\n" + "="*80)
        print("DATABASE SMOKE TEST: FAILED ❌")
        print("="*80 + "\n")
        
        return 1


if __name__ == "__main__":
    sys.exit(test_database_connection())

