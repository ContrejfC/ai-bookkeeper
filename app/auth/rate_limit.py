"""
Rate Limiting for Authentication (S10.2 Auth Hardening)

Simple in-memory rate limiting with fallback to database for persistence.
"""
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple
from collections import defaultdict
import threading


# Rate limit configuration
MAX_AUTH_ATTEMPTS = 5
RATE_LIMIT_WINDOW_SECONDS = 300  # 5 minutes
LOCKOUT_DURATION_SECONDS = 900  # 15 minutes


class RateLimiter:
    """
    In-memory rate limiter for authentication attempts.
    
    Tracks attempts by IP + email combination.
    Implements sliding window with automatic cleanup.
    """
    
    def __init__(self):
        self._attempts: Dict[str, list] = defaultdict(list)
        self._lockouts: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def _get_key(self, ip_address: str, identifier: str) -> str:
        """Generate rate limit key."""
        return f"{ip_address}:{identifier}"
    
    def _cleanup_old_attempts(self, key: str):
        """Remove attempts older than the window."""
        cutoff = time.time() - RATE_LIMIT_WINDOW_SECONDS
        self._attempts[key] = [ts for ts in self._attempts[key] if ts > cutoff]
    
    def is_locked_out(self, ip_address: str, identifier: str) -> Tuple[bool, int]:
        """
        Check if account/IP is locked out.
        
        Returns:
            Tuple of (is_locked, remaining_seconds)
        """
        key = self._get_key(ip_address, identifier)
        
        with self._lock:
            if key in self._lockouts:
                remaining = self._lockouts[key] - time.time()
                if remaining > 0:
                    return True, int(remaining)
                else:
                    # Lockout expired
                    del self._lockouts[key]
                    self._attempts[key] = []  # Clear attempts
            
            return False, 0
    
    def record_attempt(self, ip_address: str, identifier: str, success: bool = False) -> Tuple[bool, int, int]:
        """
        Record an authentication attempt.
        
        Args:
            ip_address: IP address of requester
            identifier: Email or username
            success: Whether attempt was successful
            
        Returns:
            Tuple of (should_block, attempts_remaining, lockout_seconds)
        """
        key = self._get_key(ip_address, identifier)
        
        with self._lock:
            # Check if already locked out
            if key in self._lockouts:
                remaining = self._lockouts[key] - time.time()
                if remaining > 0:
                    return True, 0, int(remaining)
                else:
                    del self._lockouts[key]
            
            # Successful attempt clears the record
            if success:
                if key in self._attempts:
                    del self._attempts[key]
                return False, MAX_AUTH_ATTEMPTS, 0
            
            # Record failed attempt
            self._cleanup_old_attempts(key)
            self._attempts[key].append(time.time())
            
            attempts_count = len(self._attempts[key])
            attempts_remaining = MAX_AUTH_ATTEMPTS - attempts_count
            
            # Check if we should trigger lockout
            if attempts_count >= MAX_AUTH_ATTEMPTS:
                self._lockouts[key] = time.time() + LOCKOUT_DURATION_SECONDS
                return True, 0, LOCKOUT_DURATION_SECONDS
            
            return False, attempts_remaining, 0
    
    def get_attempts_count(self, ip_address: str, identifier: str) -> int:
        """Get current number of attempts in window."""
        key = self._get_key(ip_address, identifier)
        
        with self._lock:
            self._cleanup_old_attempts(key)
            return len(self._attempts[key])
    
    def reset(self, ip_address: str, identifier: str):
        """Reset rate limit for a specific account/IP (admin use)."""
        key = self._get_key(ip_address, identifier)
        
        with self._lock:
            if key in self._attempts:
                del self._attempts[key]
            if key in self._lockouts:
                del self._lockouts[key]


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    return _rate_limiter

