"""
GPT Actions discovery endpoint.

Provides links, status, and configuration for ChatGPT GPT integration.
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import os
import logging

from app.db.session import get_db
from app.config.limits import PAYWALL_MD, FREE_DAILY_ANALYZE_CAP

# Read version from file
try:
    from pathlib import Path
    version_file = Path(__file__).parent.parent / "VERSION"
    __version__ = version_file.read_text().strip() if version_file.exists() else "0.9.1"
except:
    __version__ = "0.9.1"

router = APIRouter(tags=["actions"])
logger = logging.getLogger(__name__)


class ActionsDiscovery(BaseModel):
    """Actions discovery response."""
    version: str
    links: Dict[str, str]
    paywall_md: str
    cap: Dict[str, int]
    connected: Dict[str, bool]
    entitlement: Dict[str, Any]


@router.get("/actions", response_model=ActionsDiscovery)
async def get_actions_discovery(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    GPT Actions discovery endpoint.
    
    Returns:
        {
            "version": "0.2.1-beta",
            "links": {
                "openapi": "/openapi.json",
                "billing_portal": "/api/billing/portal",
                "connect_quickbooks": "/api/auth/qbo/start",
                "status": "/api/billing/status",
                "qbo_status": "/api/qbo/status"
            },
            "paywall_md": "To post to QuickBooks, activate a plan...",
            "cap": {
                "free_daily_analyze": 50
            },
            "connected": {
                "qbo": true/false
            },
            "entitlement": {
                "active": true/false,
                "plan": "starter|pro|firm|none"
            }
        }
    
    No authentication required for static links.
    Status sections (connected, entitlement) depend on tenant_id if present.
    """
    # Static links
    links = {
        "openapi": "/openapi.json",
        "billing_portal": "/api/billing/portal",
        "billing_status": "/api/billing/status",
        "connect_quickbooks": "/api/auth/qbo/start",
        "qbo_status": "/api/qbo/status",
        "post_commit": "/api/post/commit",
        "post_propose": "/api/post/propose"
    }
    
    # Try to get tenant_id from request state
    tenant_id = getattr(request.state, "tenant_id", None)
    
    # Default status (no tenant)
    connected = {"qbo": False}
    entitlement = {"active": False, "plan": "none"}
    
    # If tenant_id present, get real status
    if tenant_id:
        try:
            # Get QBO connection status
            from app.services.qbo import QBOService
            qbo_service = QBOService(db)
            qbo_status = qbo_service.get_connection_status(tenant_id)
            connected["qbo"] = qbo_status.get("connected", False)
            
        except Exception as e:
            logger.warning(f"Failed to get QBO status: {e}")
        
        try:
            # Get entitlement status
            from app.services.billing import BillingService
            billing_service = BillingService(db)
            billing_status = billing_service.get_billing_status(tenant_id)
            entitlement = {
                "active": billing_status.get("active", False),
                "plan": billing_status.get("plan", "none")
            }
            
        except Exception as e:
            logger.warning(f"Failed to get billing status: {e}")
    
    return ActionsDiscovery(
        version=__version__,
        links=links,
        paywall_md=PAYWALL_MD,
        cap={"free_daily_analyze": FREE_DAILY_ANALYZE_CAP},
        connected=connected,
        entitlement=entitlement
    )

