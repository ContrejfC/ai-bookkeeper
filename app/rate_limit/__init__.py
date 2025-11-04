"""
Rate limiting for API endpoints.

Uses token bucket algorithm with in-memory storage.
In production, use Redis for distributed rate limiting.

Limits:
- /api/upload: 30/min per IP, 5/min per tenant
- /api/post/propose: 60/min per tenant
- /api/export/*: 10/min per tenant
"""

import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
import logging

logger = logging.getLogger(__name__)

# Token buckets: {key: (tokens, last_refill_time)}
_buckets: Dict[str, Tuple[float, float]] = defaultdict(lambda: (0.0, time.time()))


class RateLimitConfig:
    """Rate limit configuration per endpoint pattern."""
    
    LIMITS = {
        "/api/upload": {"per_minute": 30, "by": "ip"},
        "/api/ingest/upload": {"per_minute": 5, "by": "tenant"},
        "/api/post/propose": {"per_minute": 60, "by": "tenant"},
        "/api/export/quickbooks": {"per_minute": 10, "by": "tenant"},
        "/api/export/xero": {"per_minute": 10, "by": "tenant"},
        "/api/billing/create_checkout_session": {"per_minute": 20, "by": "ip"},
    }


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request (handles proxies)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_tenant_id(request: Request) -> str:
    """Extract tenant_id from request state (set by auth middleware)."""
    return getattr(request.state, "tenant_id", "unknown")


def _refill_bucket(
    key: str,
    max_tokens: float,
    refill_rate: float,
    current_time: float
) -> float:
    """
    Refill token bucket based on time elapsed.
    
    Args:
        key: Bucket identifier
        max_tokens: Maximum tokens (burst capacity)
        refill_rate: Tokens per second
        current_time: Current timestamp
        
    Returns:
        Current token count after refill
    """
    tokens, last_refill = _buckets[key]
    
    # Calculate tokens to add
    time_passed = current_time - last_refill
    tokens_to_add = time_passed * refill_rate
    
    # Refill (capped at max_tokens)
    new_tokens = min(tokens + tokens_to_add, max_tokens)
    
    _buckets[key] = (new_tokens, current_time)
    return new_tokens


async def rate_limit_check(request: Request):
    """
    Rate limit middleware/dependency.
    
    Checks if request should be rate-limited based on endpoint and identifier.
    
    Raises:
        HTTPException 429 if rate limit exceeded
    """
    
    path = request.url.path
    
    # Find matching limit config
    limit_config = None
    for pattern, config in RateLimitConfig.LIMITS.items():
        if path.startswith(pattern):
            limit_config = config
            break
    
    if not limit_config:
        # No rate limit configured for this endpoint
        return
    
    # Determine rate limit key
    if limit_config["by"] == "ip":
        identifier = _get_client_ip(request)
        key_prefix = "ip"
    elif limit_config["by"] == "tenant":
        identifier = _get_tenant_id(request)
        key_prefix = "tenant"
    else:
        identifier = "global"
        key_prefix = "global"
    
    # Build bucket key
    bucket_key = f"{key_prefix}:{identifier}:{path}"
    
    # Token bucket parameters
    max_tokens = float(limit_config["per_minute"])
    refill_rate = max_tokens / 60.0  # tokens per second
    
    current_time = time.time()
    
    # Refill bucket
    available_tokens = _refill_bucket(bucket_key, max_tokens, refill_rate, current_time)
    
    # Check if request can proceed
    if available_tokens < 1.0:
        # Rate limit exceeded
        logger.warning(
            f"Rate limit exceeded: path={path}, "
            f"identifier={identifier}, key={key_prefix}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error_code": "429_RATE_LIMITED",
                "message": f"Rate limit exceeded. Max {int(max_tokens)} requests per minute.",
                "retry_after_seconds": 60,
                "limit": int(max_tokens),
                "window": "1 minute"
            }
        )
    
    # Consume 1 token
    _buckets[bucket_key] = (available_tokens - 1.0, current_time)
    
    # Add rate limit headers
    request.state.rate_limit_remaining = int(available_tokens - 1.0)
    request.state.rate_limit_limit = int(max_tokens)

