"""FastAPI application optimized for Cloud Run - fast startup."""
import logging
import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Bookkeeper",
    description="AI-powered bookkeeping with automated journal entry posting",
    version="0.2.1-beta",
    servers=[{"url": "https://api.ai-bookkeeper.app", "description": "Production"}]
)

# CORS Configuration
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "https://app.ai-bookkeeper.app,https://ai-bookkeeper-web.onrender.com"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
logger.info(f"✅ CORS enabled for origins: {ALLOWED_ORIGINS}")

# Lazy import database session (only when needed)
def get_db():
    """Lazy load database session."""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fast health check (no DB required, no dependencies)
@app.get("/healthz")
async def health_check():
    """Lightweight health check for Cloud Run - no dependencies."""
    try:
        return {
            "status": "ok",
            "version": "0.2.1-beta",
            "environment": os.getenv("APP_ENV", "production")
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"status": "error", "message": str(e)}

# Ready check with DB
@app.get("/readyz")
async def readiness_check(db: Session = Depends(get_db)):
    """Comprehensive readiness check."""
    start_time = time.time()
    checks = {}
    overall_ready = True
    
    # Database check
    db_start = time.time()
    try:
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        checks["database"] = {
            "status": "healthy",
            "timing_ms": round((time.time() - db_start) * 1000, 2)
        }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "timing_ms": round((time.time() - db_start) * 1000, 2)
        }
        overall_ready = False
    
    total_time = round((time.time() - start_time) * 1000, 2)
    
    return {
        "ready": overall_ready,
        "checks": checks,
        "total_timing_ms": total_time
    }

# Include API routers
try:
    from app.api import auth as auth_router
    app.include_router(auth_router.router)
    logger.info("✅ Auth routes loaded")
except Exception as e:
    logger.error(f"❌ Auth routes failed to load: {e}")

try:
    from app.api import tenants as tenants_router
    app.include_router(tenants_router.router)
    logger.info("✅ Tenants routes loaded")
except Exception as e:
    logger.warning(f"⚠️  Tenants routes not loaded: {e}")

try:
    from app.api import receipts as receipts_router
    app.include_router(receipts_router.router)
    logger.info("✅ Receipts routes loaded")
except Exception as e:
    logger.warning(f"⚠️  Receipts routes not loaded: {e}")

try:
    from app.api import billing_v2 as billing_router
    app.include_router(billing_router.router)
    logger.info("✅ Billing routes loaded")
except Exception as e:
    logger.warning(f"⚠️  Billing routes not loaded: {e}")

@app.on_event("startup")
async def startup_event():
    """Minimal startup - just log that we're ready."""
    logger.info("🚀 AI Bookkeeper API starting up (Cloud Run optimized)")
    logger.info(f"   Environment: {os.getenv('APP_ENV', 'production')}")
    logger.info(f"   Database: {os.getenv('DATABASE_URL', 'Not set')[:50]}...")
    logger.info("✅ Startup complete - ready to accept requests")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Bookkeeper API",
        "version": "0.2.1-beta",
        "docs": "/docs",
        "health": "/healthz"
    }

