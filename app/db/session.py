"""Database session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
from contextlib import contextmanager
from typing import Generator
from config.settings import settings

# Create engine with appropriate configuration for PostgreSQL or SQLite
engine_kwargs = {
    "echo": settings.app_env == "dev",
}

# PostgreSQL-specific configuration
if "postgresql" in settings.database_url:
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_pre_ping": True,  # Verify connections before using
        "pool_recycle": 3600,   # Recycle connections after 1 hour
    })
# SQLite-specific configuration (backwards compatibility)
elif "sqlite" in settings.database_url:
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
        "poolclass": NullPool,  # Disable pooling for SQLite
    })

engine = create_engine(settings.database_url, **engine_kwargs)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Get database session as context manager."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

