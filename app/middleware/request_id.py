"""
Request ID Middleware - Request Tracking
========================================

This middleware adds a unique request ID to every request and response for:
- Distributed tracing
- Error correlation
- Audit logging
- Debugging

Features:
--------
- Generates UUID for each request
- Adds X-Request-Id header to responses
- Logs request ID with every log entry
- Accepts client-provided request IDs

Usage:
------
```python
from app.middleware.request_id import add_request_id_middleware

app = FastAPI()
add_request_id_middleware(app)
```
"""
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds a unique request ID to each request.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Get request ID from header or generate new one
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        
        # Store in request state
        request.state.request_id = request_id
        
        # Add to logger context (thread-local)
        # This requires a custom logger filter
        try:
            # Call next middleware/route
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers["X-Request-Id"] = request_id
            
            return response
            
        except Exception as e:
            # Log exception with request ID
            logger.error(
                f"Request failed: {str(e)}",
                extra={"request_id": request_id, "path": request.url.path}
            )
            raise


def add_request_id_middleware(app: FastAPI):
    """
    Add request ID middleware to FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(RequestIdMiddleware)
    logger.info("Request ID middleware registered")


class RequestIdFilter(logging.Filter):
    """
    Logging filter that adds request_id to log records.
    
    Usage:
    ------
    ```python
    import logging
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    logger.addHandler(handler)
    ```
    """
    
    def filter(self, record):
        # Try to get request ID from various sources
        request_id = None
        
        # 1. From extra dict (preferred)
        if hasattr(record, 'request_id'):
            request_id = record.request_id
        
        # 2. From thread-local storage (if using contextvars)
        try:
            from contextvars import ContextVar
            _request_id_var: ContextVar[str] = ContextVar('request_id', default='')
            request_id = _request_id_var.get()
        except:
            pass
        
        # Set on record
        record.request_id = request_id or 'N/A'
        
        return True

