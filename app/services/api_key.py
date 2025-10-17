"""
API key management service for GPT Actions authentication.
"""

import hashlib
import secrets
import os
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.db.models import APIKeyDB


class APIKeyService:
    """Service for managing API keys."""
    
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def generate_token(prefix: str = "ak") -> str:
        """
        Generate secure API key token.
        
        Format: ak_live_<base62> or ak_test_<base62>
        
        Args:
            prefix: Token prefix (default: "ak")
        
        Returns:
            API key token (plaintext, show once)
        """
        # Determine environment
        env = os.getenv("AUTH_MODE", "dev")
        env_suffix = "test" if env == "dev" else "live"
        
        # Generate secure random token (32 bytes = 256 bits)
        token_bytes = secrets.token_bytes(32)
        token_b62 = secrets.token_urlsafe(32)[:43]  # Base64-url-safe, trimmed
        
        return f"{prefix}_{env_suffix}_{token_b62}"
    
    @staticmethod
    def hash_token(token: str) -> str:
        """
        Compute SHA-256 hash of API key token.
        
        Args:
            token: Plaintext API key
        
        Returns:
            64-character hex hash
        """
        return hashlib.sha256(token.encode('utf-8')).hexdigest()
    
    def create_api_key(
        self,
        tenant_id: str,
        name: Optional[str] = None
    ) -> tuple[str, APIKeyDB]:
        """
        Create new API key for tenant.
        
        Args:
            tenant_id: Tenant identifier
            name: Optional key description
        
        Returns:
            (plaintext_token, api_key_record)
        """
        # Generate token
        token = self.generate_token()
        token_hash = self.hash_token(token)
        
        # Create database record
        api_key = APIKeyDB(
            tenant_id=tenant_id,
            token_hash=token_hash,
            name=name
        )
        
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        
        return token, api_key
    
    def verify_token(self, token: str) -> Optional[str]:
        """
        Verify API key token and return tenant_id if valid.
        
        Args:
            token: Plaintext API key
        
        Returns:
            tenant_id if valid and not revoked, None otherwise
        """
        token_hash = self.hash_token(token)
        
        api_key = self.db.query(APIKeyDB).filter(
            APIKeyDB.token_hash == token_hash,
            APIKeyDB.revoked_at.is_(None)  # Not revoked
        ).first()
        
        if api_key:
            return api_key.tenant_id
        
        return None
    
    def revoke_key(self, token: str) -> bool:
        """
        Revoke an API key.
        
        Args:
            token: Plaintext API key to revoke
        
        Returns:
            True if revoked, False if not found
        """
        token_hash = self.hash_token(token)
        
        api_key = self.db.query(APIKeyDB).filter(
            APIKeyDB.token_hash == token_hash
        ).first()
        
        if api_key:
            api_key.revoked_at = datetime.utcnow()
            self.db.commit()
            return True
        
        return False
    
    def list_keys_for_tenant(self, tenant_id: str) -> list[APIKeyDB]:
        """
        List all API keys for tenant (including revoked).
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            List of API key records
        """
        return self.db.query(APIKeyDB).filter(
            APIKeyDB.tenant_id == tenant_id
        ).order_by(APIKeyDB.created_at.desc()).all()

