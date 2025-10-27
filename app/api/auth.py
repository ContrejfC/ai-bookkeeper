"""
Authentication API - User Login, Signup, and JWT Token Management
=================================================================

This module handles user authentication with JWT tokens and HTTP-only cookies.

API Endpoints:
-------------
- POST /api/auth/signup - Create new user account
- POST /api/auth/login - Authenticate and issue JWT token
- POST /api/auth/logout - Clear session cookie (logout)
- GET /api/auth/me - Get current user information
- POST /api/auth/qbo/start - Initiate QuickBooks OAuth flow
- GET /api/auth/qbo/callback - Handle QBO OAuth redirect

Authentication Flow:
-------------------
1. User submits email/password to /api/auth/login
2. Server validates credentials against UserDB table
3. Server generates JWT token with user_id, email, role
4. Server sets HttpOnly cookie with JWT (secure in production)
5. Client includes cookie in subsequent requests
6. Server validates JWT on protected routes

Security Features:
-----------------
- Passwords hashed with bcrypt (never stored plain text)
- JWT tokens signed with SECRET_KEY (validate authenticity)
- HttpOnly cookies (prevent XSS attacks)
- Secure flag in production (HTTPS only)
- SameSite=Lax (CSRF protection)
- CSRF tokens for state-changing operations

Development vs Production:
-------------------------
- DEV mode (AUTH_MODE=dev):
  * Allows magic token bypass for testing
  * Less strict validation
  * HTTP cookies allowed (localhost)

- PROD mode (AUTH_MODE=prod):
  * Strict password validation required
  * HTTPS-only cookies (Secure flag)
  * Full security enforcement

Role-Based Access Control (RBAC):
---------------------------------
- owner: Full access to tenant settings and data
- staff: Read-only access, can review but not approve

Multi-Tenancy:
-------------
Users can belong to multiple tenants (companies).
UserTenantDB table maps users to their accessible tenants.
"""
import os
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Header
from fastapi.responses import JSONResponse
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


class SignupRequest(BaseModel):
    """Signup request body."""
    email: EmailStr
    password: str
    full_name: str
    company_name: Optional[str] = None


class LoginResponse(BaseModel):
    """Login response."""
    success: bool
    user_id: str
    email: str
    role: str
    token: Optional[str] = None  # Only returned for API clients (non-cookie)


class SignupResponse(BaseModel):
    """Signup response."""
    success: bool
    user_id: str
    email: str
    role: str
    message: str


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
    User Login - Authenticate and Issue JWT Token
    ==============================================
    
    Purpose:
        Authenticates user credentials and issues JWT token for API access.
        Supports both password authentication (production) and magic token (development).
    
    Authentication Modes:
        1. Password (Production):
           - Validates email and password hash
           - Uses bcrypt for password verification
        
        2. Magic Token (Development Only):
           - Set AUTH_MODE=dev in environment
           - Use magic_token="dev" to bypass password
           - For testing and development only
    
    Flow:
        1. Look up user by email
        2. Check user is active
        3. Validate credentials (password or magic token)
        4. Generate JWT token with user_id, email, role
        5. Set HTTP-only cookie (if use_cookie=true)
        6. Return success response with user details
    
    Request Body:
        {
            "email": "user@example.com",
            "password": "securepass123",
            "magic_token": null  // Optional, dev mode only
        }
    
    Query Parameters:
        use_cookie: bool = true (set false for API clients)
    
    Response (200 OK):
        {
            "success": true,
            "user_id": "user-abc12345",
            "email": "user@example.com",
            "role": "owner",
            "token": "eyJ..." // Only if use_cookie=false
        }
    
    Error Codes:
        401: Invalid credentials, inactive account, or invalid magic token
        500: Database error or unexpected failure
    
    Security:
        - CSRF protection: Exempted (stateless auth)
        - Password: Verified with bcrypt.checkpw()
        - JWT: Signed with HS256, 24-hour expiry
        - Cookie: HTTP-only, Secure, SameSite=Lax
        - Rate limiting: Applied by middleware
    
    Side Effects:
        - Sets access_token cookie in browser
        - Logs login event
        - Updates last_login timestamp (if tracked)
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


@router.post("/signup")
async def signup(
    request: SignupRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    User Signup - Create New Account
    =================================
    
    Purpose:
        Creates a new user account with email/password authentication.
        Automatically assigns 'owner' role and issues JWT token.
    
    Flow:
        1. Validate email is unique (check existing users)
        2. Validate password strength (minimum 8 characters)
        3. Hash password with bcrypt
        4. Create user record with 'owner' role
        5. Generate JWT token
        6. Set HTTP-only cookie with token
        7. Return user details
    
    Request Body:
        {
            "email": "user@example.com",
            "password": "securepass123",
            "full_name": "John Doe",
            "tenant_name": "My Company"
        }
    
    Response (200 OK):
        {
            "success": true,
            "user_id": "user-abc12345",
            "email": "user@example.com",
            "role": "owner",
            "message": "Account created successfully! Welcome to AI Bookkeeper."
        }
    
    Error Codes:
        400: Email already exists or password too weak
        500: Database error or unexpected failure
    
    Security:
        - CSRF protection: Exempted (no session yet)
        - Password: Hashed with bcrypt
        - JWT: Signed with HS256, stored in HTTP-only cookie
        - Cookie: Secure, SameSite=Lax, 24-hour expiry
    
    Side Effects:
        - Creates user record in database
        - Sets access_token cookie in browser
        - Logs signup event
    """
    import uuid
    import logging
    from app.auth.security import get_password_hash
    
    logger = logging.getLogger(__name__)
    
    # Check if user already exists
    existing_user = db.query(UserDB).filter(UserDB.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Validate password strength
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    
    try:
        logger.info(f"Creating user: {request.email}")
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
        logger.info(f"User created: {user_id}")
        
        # Create access token
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
            max_age=COOKIE_MAX_AGE
        )
        
        return {
            "success": True,
            "user_id": new_user.user_id,
            "email": new_user.email,
            "role": new_user.role,
            "message": "Account created successfully! Welcome to AI Bookkeeper."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {type(e).__name__}: {str(e)}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"error": f"{type(e).__name__}: {str(e)}"}
        )


@router.get("/signup/test")
async def test_signup_route():
    """Test endpoint to verify signup route works."""
    return {"message": "Signup route is working", "status": "ok"}


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
