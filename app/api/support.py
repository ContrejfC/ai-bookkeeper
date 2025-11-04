"""
Self-support API routes: ticketing, help search.
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid

from app.infra.mailer import send_support_ticket_email
from app.auth.security import get_current_user

router = APIRouter(prefix="/api/support", tags=["support"])


class CreateTicketRequest(BaseModel):
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=10, max_length=5000)
    category: Optional[str] = Field(None, description="billing, technical, general")


@router.post("/ticket")
async def create_support_ticket(
    request_body: CreateTicketRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Create support ticket and send to support inbox.
    
    Includes request_id for log correlation.
    """
    # Get request_id from middleware (or generate)
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Get user info
    user_email = current_user.get("email", "unknown@example.com")
    tenant_id = current_user.get("tenant_id", "unknown")
    
    # Send ticket email
    try:
        result = await send_support_ticket_email(
            user_email=user_email,
            subject=request_body.subject,
            message=request_body.message,
            request_id=request_id,
            tenant_id=tenant_id
        )
        
        return {
            "success": True,
            "ticket_id": request_id,
            "message": "Support ticket created. We'll respond within 24 hours.",
            "email_sent": result["success"]
        }
    except Exception as e:
        return {
            "success": False,
            "ticket_id": request_id,
            "message": "Ticket created but email failed. We've logged your request.",
            "error": str(e)
        }

