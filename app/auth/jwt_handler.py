"""
JWT Token Handler for Wave-2 Phase 1.

Supports:
- Session cookies (HttpOnly, Secure, SameSite=Lax) for UI
- Authorization: Bearer for API
- HS256 algorithm
- CSRF protection for POST forms
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError


# JWT Configuration from environment
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_MAX_AGE_HOURS = int(os.getenv("JWT_MAX_AGE_HOURS", "24"))
COOKIE_MAX_AGE = 24 * 60 * 60  # 24 hours in seconds


def create_access_token(
    user_id: str,
    email: str,
    role: str,
    tenant_ids: list[str]
) -> str:
    """
    Create a JWT access token.
    
    Claims:
    - sub: user_id
    - email: user email
    - role: owner or staff
    - tenants: list of accessible tenant_ids (for staff)
    - iat: issued at
    - exp: expiration
    
    Args:
        user_id: Unique user identifier
        email: User email
        role: User role (owner/staff)
        tenant_ids: List of tenant IDs user can access
        
    Returns:
        JWT token string
    """
    now = datetime.utcnow()
    expire = now + timedelta(hours=JWT_MAX_AGE_HOURS)
    
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "tenants": tenant_ids,
        "iat": now,
        "exp": expire
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token.
    
    Validates:
    - Signature (HS256)
    - Expiration
    - Required claims (sub, role)
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload dict
        
    Raises:
        JWTError: If token is invalid or expired
        ValueError: If required claims missing or algorithm is 'none'
    """
    try:
        # Decode with signature verification
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "require_exp": True
            }
        )
        
        # Validate required claims
        if not payload.get("sub"):
            raise ValueError("Missing 'sub' claim")
        if not payload.get("role"):
            raise ValueError("Missing 'role' claim")
        
        # Reject 'none' algorithm explicitly (defense in depth)
        header = jwt.get_unverified_header(token)
        if header.get("alg", "").lower() == "none":
            raise ValueError("Algorithm 'none' is not allowed")
        
        return payload
    
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}")


def verify_csrf_token(request_csrf: Optional[str], cookie_csrf: Optional[str]) -> bool:
    """
    Verify CSRF token using double-submit cookie pattern.
    
    Args:
        request_csrf: CSRF token from request header (X-CSRF-Token)
        cookie_csrf: CSRF token from cookie
        
    Returns:
        True if tokens match and are present
    """
    if not request_csrf or not cookie_csrf:
        return False
    return request_csrf == cookie_csrf


def generate_csrf_token() -> str:
    """
    Generate a random CSRF token.
    
    Returns:
        Random 32-character hex string
    """
    import secrets
    return secrets.token_hex(16)

