"""
Entitlement gate middleware for billing enforcement.

Gates:
- POST /api/post/commit (+ bulk endpoints) => requires active subscription and within tx_cap
- POST /api/post/propose => free daily analyze cap (50/day tenant-wide)
- POST /api/post/explain => free daily explain cap (50/day tenant-wide)
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Callable, Optional
import os

from app.config.limits import (
    ERROR_CODES,
    PAYWALL_MD,
    FREE_DAILY_ANALYZE_CAP,
    FREE_DAILY_EXPLAIN_CAP
)


class EntitlementGateMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce billing entitlements and usage caps.
    
    Assumes auth middleware has set request.state.tenant_id before this runs.
    """
    
    def __init__(self, app, bulk_paths: Optional[list] = None):
        super().__init__(app)
        self.bulk_paths = set(bulk_paths or [
            "/api/post/bulk_approve",
            "/api/transactions/bulk_approve"
        ])
    
    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        method = request.method.upper()
        
        # Get tenant ID from request state (set by auth middleware)
        tenant_id = getattr(request.state, "tenant_id", None)
        
        # Skip gate checks for non-protected routes
        if not self._is_protected_route(path, method):
            return await call_next(request)
        
        # Require tenant ID for protected routes
        if not tenant_id:
            return JSONResponse(
                {"detail": "Unauthorized: Authentication required"},
                status_code=401
            )
        
        # Import here to avoid circular dependency
        from app.db.session import get_db_context
        from app.services.billing import BillingService
        
        with get_db_context() as db:
            billing_service = BillingService(db)
            
            # Free tier daily cap on propose/analyze
            if method == "POST" and path in ["/api/post/propose", "/api/analyze"]:
                allowed, error = billing_service.check_daily_analyze_cap(tenant_id)
                
                if not allowed:
                    response_data = error.copy()
                    response_data["paywall"] = PAYWALL_MD
                    return JSONResponse(
                        response_data,
                        status_code=error["http_status"]
                    )
                
                # Increment count after check passes
                billing_service.increment_daily_analyze(tenant_id)
            
            # Free tier daily cap on explain
            if method == "POST" and path in ["/api/post/explain", "/api/explain"]:
                allowed, error = billing_service.check_daily_explain_cap(tenant_id)
                
                if not allowed:
                    response_data = error.copy()
                    response_data["paywall"] = PAYWALL_MD
                    return JSONResponse(
                        response_data,
                        status_code=error["http_status"]
                    )
                
                # Increment count after check passes
                billing_service.increment_daily_explain(tenant_id)
            
            # Subscription required + monthly cap on commit and bulk
            if method == "POST" and (path == "/api/post/commit" or path in self.bulk_paths):
                allowed, error = billing_service.check_monthly_cap(tenant_id)
                
                if not allowed:
                    response_data = error.copy()
                    response_data["paywall"] = PAYWALL_MD
                    return JSONResponse(
                        response_data,
                        status_code=error["http_status"]
                    )
                
                # Check bulk approve entitlement for bulk paths
                if path in self.bulk_paths:
                    entitlement = billing_service.get_entitlement(tenant_id)
                    if entitlement and not entitlement.get("bulk_approve", False):
                        response_data = ERROR_CODES["BULK_APPROVE_REQUIRED"].copy()
                        response_data["paywall"] = PAYWALL_MD
                        return JSONResponse(
                            response_data,
                            status_code=402
                        )
        
        # All checks passed, continue with request
        response = await call_next(request)
        
        # Increment posted count after successful commit
        if method == "POST" and path == "/api/post/commit":
            if response.status_code in [200, 201, 204]:
                with get_db_context() as db:
                    billing_service = BillingService(db)
                    
                    # Extract count from response if available
                    # For now, increment by 1
                    # TODO: Extract actual count from request/response
                    billing_service.increment_posted(tenant_id, count=1)
        
        return response
    
    def _is_protected_route(self, path: str, method: str) -> bool:
        """Check if route requires billing enforcement."""
        protected_paths = [
            "/api/post/propose",
            "/api/post/commit",
            "/api/post/explain",
            "/api/analyze",
            "/api/explain"
        ]
        
        # Add bulk paths
        protected_paths.extend(self.bulk_paths)
        
        return method == "POST" and path in protected_paths

