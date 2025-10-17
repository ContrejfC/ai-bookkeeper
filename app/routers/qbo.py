"""
QuickBooks Online API router for OAuth2 and journal entry posting.

Endpoints:
- GET /api/auth/qbo/start - Initialize OAuth2 flow
- GET /api/auth/qbo/callback - OAuth2 callback handler
- GET /api/qbo/status - Get connection status
- POST /api/qbo/journalentry - Post journal entry idempotently
"""

import os
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from app.db.session import get_db
from app.services.qbo import QBOService
from app.ui.rbac import User, get_current_user

router = APIRouter(tags=["qbo"])
logger = logging.getLogger(__name__)


class JELine(BaseModel):
    """Journal entry line."""
    amount: float
    postingType: str  # "Debit" or "Credit"
    accountRef: Dict[str, str]  # {"value": "46"}


class JEPayload(BaseModel):
    """Journal entry payload."""
    txnDate: str  # YYYY-MM-DD
    lines: List[JELine]
    refNumber: Optional[str] = None
    privateNote: Optional[str] = "AI Bookkeeper"


class JEResponse(BaseModel):
    """Journal entry posting response."""
    status: int  # 201 or 200
    qbo_doc_id: str
    idempotent: bool
    message: str


class ConnectionStatus(BaseModel):
    """QBO connection status."""
    connected: bool
    realm_id: Optional[str] = None
    token_age_sec: Optional[int] = None
    expires_in_sec: Optional[int] = None


@router.get("/api/auth/qbo/start")
async def start_qbo_oauth(
    request: Request,
    user: User = Depends(get_current_user)
):
    """
    Initialize QuickBooks Online OAuth2 flow.
    
    Returns 302 redirect to Intuit authorization page.
    """
    # Generate CSRF state token
    state = secrets.token_urlsafe(32)
    
    # Store state in session/cache (for now, just pass it)
    # TODO: Store state in Redis or session for CSRF validation
    
    # Get authorization URL
    from app.integrations.qbo.client import QBOClient
    client = QBOClient()
    
    auth_url = client.get_authorization_url(state=state)
    
    logger.info(f"QBO OAuth started for user {user.user_id}")
    
    # Return redirect
    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/api/auth/qbo/callback")
async def qbo_oauth_callback(
    code: str,
    state: str,
    realmId: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Handle QuickBooks Online OAuth2 callback.
    
    Exchanges authorization code for tokens and stores them.
    
    Args:
        code: Authorization code from QBO
        state: CSRF state token
        realmId: QuickBooks company ID
    
    Returns:
        Success message and redirect
    """
    if not realmId:
        raise HTTPException(status_code=400, detail="Missing realmId parameter")
    
    # TODO: Validate state token against stored value
    
    # Get tenant ID from user
    tenant_id = user.tenants[0] if user.tenants else user.user_id
    
    # Exchange code for tokens
    qbo_service = QBOService(db)
    
    try:
        from app.integrations.qbo.client import QBOClient
        client = QBOClient()
        
        tokens = await client.exchange_code_for_tokens(
            code=code,
            realm_id=realmId
        )
        
        # Store tokens
        qbo_service.store_tokens(
            tenant_id=tenant_id,
            realm_id=tokens["realm_id"],
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_at=tokens["expires_at"]
        )
        
        logger.info(f"QBO OAuth completed for tenant {tenant_id}, realm {realmId}")
        
        # Redirect to success page
        return RedirectResponse(url="/dashboard?qbo=connected", status_code=302)
        
    except Exception as e:
        logger.error(f"QBO OAuth callback failed: {e}")
        raise HTTPException(status_code=400, detail=f"OAuth callback failed: {str(e)}")


@router.get("/api/qbo/status", response_model=ConnectionStatus)
async def get_qbo_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get QuickBooks Online connection status.
    
    Returns:
        {
            "connected": bool,
            "realm_id": str,
            "token_age_sec": int,
            "expires_in_sec": int
        }
    """
    # Get tenant ID from user
    tenant_id = user.tenants[0] if user.tenants else user.user_id
    
    qbo_service = QBOService(db)
    status = qbo_service.get_connection_status(tenant_id)
    
    return ConnectionStatus(**status)


@router.post("/api/qbo/journalentry", response_model=JEResponse)
async def post_journal_entry(
    payload: JEPayload,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Post journal entry to QuickBooks Online with idempotency.
    
    Args:
        payload: Journal entry with txnDate, lines (amount, postingType, accountRef)
    
    Returns:
        201 {qbo_doc_id, idempotent: false} on first post
        200 {qbo_doc_id, idempotent: true} on duplicate
    
    Error Codes:
        400 - UNBALANCED_JE if debits != credits
        401 - QBO_UNAUTHORIZED if not connected or token invalid
        422 - QBO_VALIDATION if QBO rejects the entry
        502 - QBO_UPSTREAM if QBO API unavailable
    """
    # Get tenant ID from user
    tenant_id = user.tenants[0] if user.tenants else user.user_id
    
    qbo_service = QBOService(db)
    
    try:
        # Convert Pydantic model to dict
        payload_dict = payload.dict()
        
        # Post with idempotency
        result = await qbo_service.post_idempotent_je(tenant_id, payload_dict)
        
        return JEResponse(**result)
        
    except ValueError as e:
        # Balance validation error
        error_str = str(e)
        if "UNBALANCED_JE" in error_str:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "UNBALANCED_JE",
                    "message": error_str.replace("UNBALANCED_JE:", "")
                }
            )
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        error_str = str(e)
        
        # Map QBO errors to HTTP status codes
        if "QBO_NOT_CONNECTED" in error_str:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "QBO_UNAUTHORIZED",
                    "message": "QuickBooks not connected. Please connect your QuickBooks account."
                }
            )
        
        if "QBO_UNAUTHORIZED" in error_str:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "QBO_UNAUTHORIZED",
                    "message": "QuickBooks authorization expired. Please re-connect your QuickBooks account."
                }
            )
        
        if "QBO_VALIDATION" in error_str:
            safe_message = error_str.replace("QBO_VALIDATION:", "")
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "QBO_VALIDATION",
                    "message": safe_message
                }
            )
        
        if "QBO_UPSTREAM" in error_str:
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "QBO_UPSTREAM",
                    "message": "QuickBooks API unavailable. Please try again shortly."
                }
            )
        
        if "QBO_RATE_LIMITED" in error_str:
            retry_after = error_str.split(":")[1] if ":" in error_str else "60"
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "QBO_RATE_LIMITED",
                    "message": f"QuickBooks API rate limit reached. Retry after {retry_after} seconds.",
                    "retry_after": int(retry_after)
                }
            )
        
        # Generic error
        logger.error(f"QBO journal entry post failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to post journal entry. Please try again."
            }
        )

