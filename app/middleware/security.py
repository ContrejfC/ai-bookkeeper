"""
Security Headers Middleware (S10.2 Auth Hardening)

Adds security headers to all responses.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import os


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    
    Headers:
    - Content-Security-Policy
    - X-Content-Type-Options
    - X-Frame-Options  
    - X-XSS-Protection
    - Referrer-Policy
    - Strict-Transport-Security (if HTTPS)
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Content Security Policy
        # Allow self, inline styles for Tailwind, and CDN resources
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS Protection (legacy, but doesn't hurt)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS (only if HTTPS)
        if request.url.scheme == "https" or os.getenv("FORCE_HSTS") == "true":
            # 1 year max-age, include subdomains
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        return response

