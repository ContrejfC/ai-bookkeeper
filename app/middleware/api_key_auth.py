"""
API key authentication middleware for GPT Actions.

Extracts Bearer token from Authorization header and sets tenant_id if valid.
Runs before entitlement middleware to ensure tenant_id is set early.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to authenticate API keys for GPT Actions.
    
    Behavior:
    - Reads Authorization: Bearer <token> header
    - If token is valid API key, sets request.state.tenant_id
    - Does not interfere with existing JWT/session auth
    - Prefers JWT/session over API key if both present
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Check if tenant_id already set by JWT/session auth
        tenant_id = getattr(request.state, "tenant_id", None)
        
        if tenant_id:
            # JWT/session auth already set tenant_id, prefer that
            return await call_next(request)
        
        # Try to extract Bearer token
        auth_header = request.headers.get("Authorization", "")
        
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "").strip()
            
            # Check if token looks like an API key (starts with ak_)
            if token.startswith("ak_"):
                try:
                    # Import here to avoid circular dependency
                    from app.db.session import get_db_context
                    from app.services.api_key import APIKeyService
                    
                    # Verify token and get tenant_id
                    with get_db_context() as db:
                        api_key_service = APIKeyService(db)
                        tenant_id = api_key_service.verify_token(token)
                        
                        if tenant_id:
                            # Set tenant_id for downstream middleware and handlers
                            request.state.tenant_id = tenant_id
                            logger.debug(f"API key authenticated for tenant {tenant_id}")
                
                except Exception as e:
                    # Don't fail request on API key errors, just log
                    logger.warning(f"API key verification failed: {e}")
        
        return await call_next(request)

