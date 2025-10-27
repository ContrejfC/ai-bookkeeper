"""
CSRF Protection Middleware (P1.1 Security Patch).

Provides:
- Per-session CSRF token generation
- Token rotation (daily)
- Validation middleware for state-changing requests
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import Response


# CSRF token cache: {session_id: (token, expiry)}
_csrf_tokens = {}


def generate_csrf_token(session_id: str = None) -> str:
    """
    Generate a new CSRF token.
    
    Args:
        session_id: Optional session identifier for token caching
        
    Returns:
        32-character hex token
    """
    token = secrets.token_hex(32)
    
    if session_id:
        # Cache with daily expiry
        expiry = datetime.utcnow() + timedelta(days=1)
        _csrf_tokens[session_id] = (token, expiry)
    
    return token


def get_csrf_token(session_id: str) -> Optional[str]:
    """
    Get cached CSRF token for session.
    
    Rotates daily (returns None if expired).
    
    Args:
        session_id: Session identifier
        
    Returns:
        Token if valid, None if expired
    """
    if session_id not in _csrf_tokens:
        return None
    
    token, expiry = _csrf_tokens[session_id]
    
    # Check expiry (daily rotation)
    if datetime.utcnow() > expiry:
        del _csrf_tokens[session_id]
        return None
    
    return token


def verify_csrf_token(request_token: str, session_token: str) -> bool:
    """
    Verify CSRF token matches.
    
    Args:
        request_token: Token from request header
        session_token: Token from session/cookie
        
    Returns:
        True if tokens match
    """
    if not request_token or not session_token:
        return False
    
    return secrets.compare_digest(request_token, session_token)


async def csrf_protect(request: Request, call_next):
    """
    CSRF protection middleware.
    
    Validates X-CSRF-Token header on state-changing requests.
    
    Exempt routes:
    - GET, HEAD, OPTIONS (read-only)
    - /api/auth/login (no session yet)
    - /api/billing/stripe_webhook (external webhook)
    
    Args:
        request: FastAPI request
        call_next: Next middleware in chain
        
    Returns:
        Response
        
    Raises:
        HTTPException: 403 if CSRF validation fails
    """
    # Skip read-only methods
    if request.method in ["GET", "HEAD", "OPTIONS"]:
        return await call_next(request)
    
    # Skip exempt routes
    exempt_paths = [
        "/api/auth/login",
        "/api/auth/signup",  # Public endpoint - no session/CSRF token yet
        "/api/billing/stripe_webhook"
    ]
    
    if request.url.path in exempt_paths:
        return await call_next(request)
    
    # Get CSRF token from header
    request_token = request.headers.get("X-CSRF-Token")
    
    # Get session token from cookie
    csrf_cookie = request.cookies.get("csrf_token")
    
    # Validate
    if not verify_csrf_token(request_token, csrf_cookie):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token validation failed"
        )
    
    # Pass through
    response = await call_next(request)
    return response


def set_csrf_cookie(response: Response, token: str):
    """
    Set CSRF token cookie.
    
    Cookie is NOT HttpOnly so JavaScript can read it for headers.
    
    Args:
        response: FastAPI response
        token: CSRF token to set
    """
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,  # JS needs to read this
        secure=True,
        samesite="lax",
        max_age=86400  # 24 hours
    )

