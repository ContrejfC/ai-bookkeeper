"""
Email-based auth flows: verification and password reset.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import UserDB
from app.infra.mailer import send_verification_email, send_password_reset_email
from app.auth.passwords import hash_password, verify_password
import os

router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory store for verification codes (use Redis in production)
_verification_codes = {}  # {email: (code, expires_at)}
_reset_codes = {}  # {email: (code, expires_at)}


class RequestVerifyRequest(BaseModel):
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str


class RequestResetRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str


@router.post("/request-verify")
async def request_email_verification(
    request: RequestVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Request email verification code.
    
    Sends 6-digit code to user's email.
    Code expires in 24 hours.
    """
    # Check if user exists
    user = db.query(UserDB).filter(UserDB.email == request.email).first()
    if not user:
        # Don't reveal if email exists (security)
        return {"success": True, "message": "If the email exists, a verification code was sent"}
    
    # Generate 6-digit code
    code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    # Store code
    _verification_codes[request.email] = (code, expires_at)
    
    # Send email
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    verification_url = f"{frontend_url}/verify?email={request.email}&code={code}"
    
    try:
        await send_verification_email(request.email, code, verification_url)
        return {"success": True, "message": "Verification code sent", "expires_in_hours": 24}
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to send email. Please try again later."
        )


@router.post("/verify-email")
async def verify_email(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Verify email with code.
    
    Marks user as verified and activates account.
    """
    # Check code
    if request.email not in _verification_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verification code found for this email"
        )
    
    code, expires_at = _verification_codes[request.email]
    
    # Check expiry
    if datetime.utcnow() > expires_at:
        del _verification_codes[request.email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired. Please request a new one."
        )
    
    # Check code match
    if code != request.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Mark user as verified
    user = db.query(UserDB).filter(UserDB.email == request.email).first()
    if user:
        user.is_active = True
        db.commit()
    
    # Clear code
    del _verification_codes[request.email]
    
    return {"success": True, "message": "Email verified successfully"}


@router.post("/request-reset")
async def request_password_reset(
    request: RequestResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset code.
    
    Sends 6-digit code to user's email.
    Code expires in 1 hour.
    """
    # Check if user exists
    user = db.query(UserDB).filter(UserDB.email == request.email).first()
    if not user:
        # Don't reveal if email exists (security)
        return {"success": True, "message": "If the email exists, a reset code was sent"}
    
    # Generate 6-digit code
    code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Store code
    _reset_codes[request.email] = (code, expires_at)
    
    # Send email
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    reset_url = f"{frontend_url}/reset-password?email={request.email}&code={code}"
    
    try:
        await send_password_reset_email(request.email, code, reset_url)
        return {"success": True, "message": "Reset code sent", "expires_in_hours": 1}
    except Exception as e:
        logger.error(f"Failed to send reset email: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to send email. Please try again later."
        )


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password with code.
    """
    # Check code
    if request.email not in _reset_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No reset code found for this email"
        )
    
    code, expires_at = _reset_codes[request.email]
    
    # Check expiry
    if datetime.utcnow() > expires_at:
        del _reset_codes[request.email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code expired. Please request a new one."
        )
    
    # Check code match
    if code != request.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset code"
        )
    
    # Update password
    user = db.query(UserDB).filter(UserDB.email == request.email).first()
    if user:
        user.password_hash = hash_password(request.new_password)
        db.commit()
    
    # Clear code
    del _reset_codes[request.email]
    
    return {"success": True, "message": "Password reset successfully"}


import logging
logger = logging.getLogger(__name__)

