"""Minimal FastAPI application with essential auth routes for Cloud Run."""
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(
    title="AI Bookkeeper API",
    version="0.2.1-beta",
    description="AI-powered bookkeeping automation"
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
logger.info(f"✅ CORS enabled for: {ALLOWED_ORIGINS}")

# Database dependency
def get_db():
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Models
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupResponse(BaseModel):
    success: bool
    user_id: str
    email: str
    role: str
    token: str

class LoginResponse(BaseModel):
    user_id: str
    email: str
    role: str
    token: str

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "AI Bookkeeper API",
        "version": "0.2.1-beta",
        "status": "operational",
        "endpoints": {
            "health": "/healthz",
            "docs": "/docs",
            "signup": "/api/auth/signup",
            "login": "/api/auth/login"
        }
    }

# Health checks
@app.get("/healthz")
async def health_check():
    return {"status": "ok", "version": "0.2.1-beta"}

@app.get("/readyz")
async def readiness_check(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {"ready": True, "database": "connected"}
    except Exception as e:
        return {"ready": False, "database": f"error: {str(e)}"}

# Auth endpoints
@app.post("/api/auth/signup", response_model=SignupResponse)
async def signup(
    request: SignupRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Create a new user account."""
    try:
        from app.db.models import UserDB
        from app.auth.security import get_password_hash
        from app.auth.jwt_handler import create_access_token
        import uuid
        
        logger.info(f"Signup attempt for: {request.email}")
        
        # Check if user exists
        existing_user = db.query(UserDB).filter(UserDB.email == request.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Validate password
        if len(request.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        # Create user
        user_id = f"user-{uuid.uuid4().hex[:8]}"
        password_hash = get_password_hash(request.password)
        
        new_user = UserDB(
            user_id=user_id,
            email=request.email,
            password_hash=password_hash,
            role="owner",
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"✅ User created: {user_id}")
        
        # Create token
        token = create_access_token(
            user_id=new_user.user_id,
            email=new_user.email,
            role=new_user.role,
            tenant_ids=[]
        )
        
        # Set cookie
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=86400  # 24 hours
        )
        
        return SignupResponse(
            success=True,
            user_id=new_user.user_id,
            email=new_user.email,
            role=new_user.role,
            token=token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Authenticate user and issue JWT token."""
    try:
        from app.db.models import UserDB
        from app.auth.security import verify_password
        from app.auth.jwt_handler import create_access_token
        from datetime import datetime
        
        logger.info(f"Login attempt for: {request.email}")
        
        # Find user
        user = db.query(UserDB).filter(UserDB.email == request.email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Account is inactive")
        
        # Verify password
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create token
        token = create_access_token(
            user_id=user.user_id,
            email=user.email,
            role=user.role,
            tenant_ids=[]
        )
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        # Set cookie
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=86400
        )
        
        logger.info(f"✅ Login successful: {user.user_id}")
        
        return LoginResponse(
            user_id=user.user_id,
            email=user.email,
            role=user.role,
            token=token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/api/auth/me")
async def get_current_user(
    authorization: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get current user info from token."""
    try:
        from app.auth.jwt_handler import decode_access_token
        from app.db.models import UserDB
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        token = authorization.split(" ")[1]
        payload = decode_access_token(token)
        
        user = db.query(UserDB).filter(UserDB.user_id == payload["user_id"]).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 AI Bookkeeper API (Minimal) starting...")
    logger.info(f"   Version: 0.2.1-beta")
    logger.info(f"   Environment: {os.getenv('APP_ENV', 'production')}")
    logger.info(f"   CORS Origins: {len(ALLOWED_ORIGINS)} configured")
    logger.info("✅ Ready to accept requests")


# Add diagnostic endpoint
try:
    from diag import router as diag_router
    app.include_router(diag_router)
    logger.info("✅ Diagnostic routes loaded")
except Exception as e:
    logger.warning(f"⚠️  Diagnostic routes not loaded: {e}")
