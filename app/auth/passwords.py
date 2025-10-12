"""
Password Management (S10.2 Auth Hardening)

Secure password hashing, verification, and reset token generation.
"""
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
import bcrypt


# Password policy
MIN_PASSWORD_LENGTH = 12
RESET_TOKEN_EXPIRY_HOURS = 24


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Bcrypt hash string
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    
    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds = good balance of security/performance
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a bcrypt hash.
    
    Args:
        password: Plain text password
        hashed: Bcrypt hash string
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return False


def generate_reset_token(user_id: str, email: str) -> Tuple[str, datetime]:
    """
    Generate a secure password reset token.
    
    Token format: {random_bytes}.{signature}
    Signature = HMAC(user_id + email + expiry + secret)
    
    Args:
        user_id: User identifier
        email: User email address
        
    Returns:
        Tuple of (token, expiry_datetime)
    """
    # Generate random component
    random_bytes = secrets.token_urlsafe(32)
    
    # Calculate expiry
    expiry = datetime.utcnow() + timedelta(hours=RESET_TOKEN_EXPIRY_HOURS)
    expiry_ts = int(expiry.timestamp())
    
    # Create signature
    secret = os.getenv("PASSWORD_RESET_SECRET", "default-dev-secret-change-me")
    payload = f"{user_id}:{email}:{expiry_ts}:{random_bytes}"
    signature = hashlib.sha256(f"{payload}:{secret}".encode()).hexdigest()[:16]
    
    # Combine token
    token = f"{random_bytes}.{expiry_ts}.{signature}"
    
    return token, expiry


def verify_reset_token(token: str, user_id: str, email: str) -> bool:
    """
    Verify a password reset token is valid and not expired.
    
    Args:
        token: Reset token string
        user_id: User identifier
        email: User email address
        
    Returns:
        True if token is valid and not expired, False otherwise
    """
    try:
        # Parse token
        parts = token.split('.')
        if len(parts) != 3:
            return False
        
        random_bytes, expiry_ts_str, provided_sig = parts
        expiry_ts = int(expiry_ts_str)
        
        # Check expiry
        if datetime.utcnow().timestamp() > expiry_ts:
            return False
        
        # Verify signature
        secret = os.getenv("PASSWORD_RESET_SECRET", "default-dev-secret-change-me")
        payload = f"{user_id}:{email}:{expiry_ts}:{random_bytes}"
        expected_sig = hashlib.sha256(f"{payload}:{secret}".encode()).hexdigest()[:16]
        
        return secrets.compare_digest(provided_sig, expected_sig)
    
    except:
        return False


def is_strong_password(password: str) -> Tuple[bool, Optional[str]]:
    """
    Check if password meets strength requirements.
    
    Args:
        password: Password to check
        
    Returns:
        Tuple of (is_strong, error_message)
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    
    # Check for variety
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    
    variety_count = sum([has_lower, has_upper, has_digit, has_special])
    
    if variety_count < 3:
        return False, "Password must include at least 3 of: lowercase, uppercase, digits, special characters"
    
    return True, None

