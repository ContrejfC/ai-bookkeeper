"""
Database Session Management - SQLAlchemy Connection Handling
===========================================================

This module manages database connections and session lifecycle for the application.
It provides both dependency injection (for FastAPI) and context manager patterns.

Key Components:
--------------
1. engine: SQLAlchemy engine (connection pool)
2. SessionLocal: Session factory for creating new DB sessions
3. get_db(): FastAPI dependency for automatic session management
4. get_db_context(): Context manager for manual session control

Connection Pooling:
------------------
- PostgreSQL: Uses QueuePool with configurable size (default: 5 connections)
- SQLite: Uses NullPool (no pooling needed for file-based DB)

Session Lifecycle:
-----------------
FastAPI routes use Depends(get_db) to automatically:
1. Create session at request start
2. Provide session to route function
3. Close session after request completes
4. Handle rollback on errors

Usage Examples:
--------------
In FastAPI routes:
    @app.get("/api/data")
    def get_data(db: Session = Depends(get_db)):
        return db.query(Model).all()

In background tasks:
    with get_db_context() as db:
        db.query(Model).update(...)
        # Auto-commits on success, rolls back on error
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
from contextlib import contextmanager
from typing import Generator
from config.settings import settings

# ============================================================================
# Engine Configuration - Database Connection Pool Setup
# ============================================================================

# Base engine configuration
# echo=True logs all SQL statements (useful for debugging in dev)
engine_kwargs = {
    "echo": settings.app_env == "dev",  # Log SQL in development only
}

# ============================================================================
# PostgreSQL Configuration - Production Database
# ============================================================================
if "postgresql" in settings.database_url:
    engine_kwargs.update({
        # Connection pool size (number of persistent connections)
        "pool_size": settings.DB_POOL_SIZE,  # Default: 5
        
        # Max overflow (additional connections beyond pool_size)
        "max_overflow": settings.DB_MAX_OVERFLOW,  # Default: 10
        
        # Verify connection is alive before using from pool
        # Prevents "server closed connection" errors
        "pool_pre_ping": True,
        
        # Recycle connections after 1 hour (prevents stale connections)
        # Neon/cloud databases may close idle connections
        "pool_recycle": 3600,
    })

# ============================================================================
# SQLite Configuration - Local Development (Legacy Support)
# ============================================================================
elif "sqlite" in settings.database_url:
    engine_kwargs.update({
        # SQLite is single-threaded by default
        # This allows multi-threaded FastAPI to access SQLite
        "connect_args": {"check_same_thread": False},
        
        # Disable connection pooling for SQLite (file-based DB)
        "poolclass": NullPool,
    })

# ============================================================================
# Create Engine - Main Database Connection Pool
# ============================================================================
engine = create_engine(settings.database_url, **engine_kwargs)

# ============================================================================
# Session Factory - Creates New Database Sessions
# ============================================================================
# autocommit=False: Explicit commit() required (prevents accidental commits)
# autoflush=False: Explicit flush() required (better control over DB writes)
# bind=engine: Links sessions to our connection pool
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ============================================================================
# FastAPI Dependency - Auto Session Management for Routes
# ============================================================================
def get_db() -> Generator[Session, None, None]:
    """
    Get database session for FastAPI dependency injection.
    
    This function is used with FastAPI's Depends() to automatically manage
    database sessions in route handlers.
    
    Lifecycle:
    ----------
    1. Creates new session when request starts
    2. Yields session to route handler
    3. Automatically closes session when request completes
    
    Usage in Routes:
    ---------------
    @app.get("/api/users")
    def get_users(db: Session = Depends(get_db)):
        return db.query(UserDB).all()
    
    Error Handling:
    --------------
    - Session is closed even if route raises exception
    - Uncommitted changes are NOT automatically rolled back
    - Route should handle explicit rollback if needed
    
    Note: This does NOT auto-commit. Route handlers must call db.commit()
          to persist changes to the database.
    """
    db = SessionLocal()
    try:
        yield db  # Provide session to route handler
    finally:
        db.close()  # Always close, even on errors


# ============================================================================
# Context Manager - Manual Session Control for Background Tasks
# ============================================================================
@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Get database session as context manager for manual session control.
    
    This is used in background tasks, scripts, or anywhere you need
    explicit control over the session lifecycle.
    
    Features:
    ---------
    - Auto-commits on successful completion
    - Auto-rolls back on exceptions
    - Always closes session
    
    Usage Example:
    -------------
    # In a background job or script
    with get_db_context() as db:
        user = db.query(UserDB).filter_by(email="test@example.com").first()
        user.last_login = datetime.now()
        # Auto-commits when exiting with block
    
    Error Handling:
    --------------
    with get_db_context() as db:
        db.add(new_record)
        raise ValueError("Something went wrong")
        # Automatically rolls back and closes session
    
    Difference from get_db():
    ------------------------
    - get_db(): Used in FastAPI routes, does NOT auto-commit
    - get_db_context(): Used in background tasks, DOES auto-commit
    """
    db = SessionLocal()
    try:
        yield db  # Provide session to caller
        db.commit()  # Auto-commit on success
    except Exception:
        db.rollback()  # Auto-rollback on error
        raise  # Re-raise exception for caller to handle
    finally:
        db.close()  # Always close connection

