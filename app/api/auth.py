"""
Authentication endpoints for Wave-2 Phase 1.

Endpoints:
- POST /api/auth/login - Issue JWT token
- POST /api/auth/logout - Clear session cookie
- GET /api/auth/me - Get current user info
"""
import os
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Header
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.db.models import UserDB, UserTenantDB
from app.auth.jwt_handler import (
    create_access_token,
    decode_access_token,
    generate_csrf_token,
    COOKIE_MAX_AGE,
    JWT_SECRET_KEY
)


router = APIRouter(prefix="/api/auth", tags=["auth"])

AUTH_MODE = os.getenv("AUTH_MODE", "dev")  # 'dev' or 'prod'


class LoginRequest(BaseModel):
    """Login request body."""
    email: EmailStr
    password: Optional[str] = None  # NULL for magic link in dev mode
    magic_token: Optional[str] = None  # For dev mode bypass


class LoginResponse(BaseModel):
    """Login response."""
    success: bool
    user_id: str
    email: str
    role: str
    token: Optional[str] = None  # Only returned for API clients (non-cookie)


class UserInfo(BaseModel):
    """Current user information."""
    user_id: str
    email: str
    role: str
    tenants: list[str]


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    use_cookie: bool = True  # Query param to disable cookie for API clients
):
    """
    Authenticate user and issue JWT token.
    
    Modes:
    - dev: Allows magic link bypass (magic_token="dev")
    - prod: Requires password validation
    
    Response:
    - Sets HttpOnly, Secure, SameSite=Lax cookie for UI
    - Returns token in body for API clients
    """
    # Query user by email
    user = db.query(UserDB).filter(UserDB.email == request.email).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is inactive")
    
    # Authentication validation - support both magic token and password
    if request.magic_token:
        # Magic token mode (dev bypass)
        if AUTH_MODE == "dev" and request.magic_token == "dev":
            pass  # Allow
        else:
            raise HTTPException(status_code=401, detail="Invalid magic token")
    elif request.password:
        # Password mode
        if not user.password_hash:
            raise HTTPException(status_code=401, detail="Password authentication not configured")
        
        # Verify password using bcrypt
        from app.auth.passwords import verify_password
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
    else:
        raise HTTPException(status_code=401, detail="Password or magic_token required")
    
    # Get user's assigned tenants (for staff)
    tenant_ids = []
    if user.role == "staff":
        assignments = db.query(UserTenantDB).filter(
            UserTenantDB.user_id == user.user_id
        ).all()
        tenant_ids = [a.tenant_id for a in assignments]
    
    # Create JWT token
    token = create_access_token(
        user_id=user.user_id,
        email=user.email,
        role=user.role,
        tenant_ids=tenant_ids
    )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Set cookie for UI clients
    if use_cookie:
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=True,  # HTTPS only in production
            samesite="lax",
            max_age=COOKIE_MAX_AGE
        )
        
        # Set CSRF token cookie (using new csrf module)
        from app.auth.csrf import generate_csrf_token, set_csrf_cookie
        csrf_token = generate_csrf_token(session_id=user.user_id)
        set_csrf_cookie(response, csrf_token)
    
    return LoginResponse(
        success=True,
        user_id=user.user_id,
        email=user.email,
        role=user.role,
        token=token if not use_cookie else None
    )


@router.post("/logout")
async def logout(response: Response):
    """
    Clear session cookie.
    
    Returns:
        Success message
    """
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="csrf_token")
    
    return {"success": True, "message": "Logged out"}


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    access_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information.
    
    Supports:
    - Cookie-based auth (access_token cookie)
    - Bearer token auth (Authorization header)
    
    Returns:
        User information
    """
    token = None
    
    # Try cookie first
    if access_token:
        token = access_token
    # Fallback to Authorization header
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = decode_access_token(token)
        
        return UserInfo(
            user_id=payload["sub"],
            email=payload["email"],
            role=payload["role"],
            tenants=payload.get("tenants", [])
        )
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
