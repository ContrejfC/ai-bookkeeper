"""
RBAC (Role-Based Access Control) for Wave-2 UI (De-mocked with JWT).

Roles:
- owner: Full access to all tenants and settings
- staff: Read-only access to assigned tenants

Authentication:
- JWT tokens (cookie or Bearer)
- CSRF protection for POST forms
"""
from enum import Enum
from typing import List, Optional
from fastapi import HTTPException, status, Cookie, Header, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db


class Role(str, Enum):
    """User roles."""
    OWNER = "owner"
    STAFF = "staff"


class User:
    """Mock user for RBAC demonstration."""
    
    def __init__(
        self,
        user_id: str,
        email: str,
        role: Role,
        assigned_tenant_ids: Optional[List[str]] = None
    ):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.assigned_tenant_ids = assigned_tenant_ids or []
    
    def can_view_tenant(self, tenant_id: str) -> bool:
        """Check if user can view a tenant."""
        if self.role == Role.OWNER:
            return True
        return tenant_id in self.assigned_tenant_ids
    
    def can_modify_tenant(self, tenant_id: str) -> bool:
        """Check if user can modify tenant settings."""
        if self.role != Role.OWNER:
            return False
        return self.can_view_tenant(tenant_id)
    
    def get_visible_tenants(self, all_tenant_ids: List[str]) -> List[str]:
        """Get list of tenants visible to this user."""
        if self.role == Role.OWNER:
            return all_tenant_ids
        return [tid for tid in all_tenant_ids if tid in self.assigned_tenant_ids]


def get_current_user(
    access_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT (de-mocked).
    
    Supports:
    - Cookie-based auth (access_token cookie) for UI
    - Bearer token auth (Authorization header) for API
    
    Returns:
        User object with role and tenant assignments
        
    Raises:
        HTTPException: 401 if not authenticated or token invalid
    """
    from app.auth.jwt_handler import decode_access_token
    from app.db.models import UserTenantDB
    from jose import JWTError
    
    token = None
    
    # Try cookie first (UI)
    if access_token:
        token = access_token
    # Fallback to Authorization header (API)
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    
    # Development fallback if no token
    if not token:
        import os
        if os.getenv("AUTH_MODE", "dev") == "dev":
            # Dev mode: return mock owner
            return User(
                user_id="user-admin-001",
                email="admin@example.com",
                role=Role.OWNER,
                assigned_tenant_ids=[]
            )
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Decode JWT
        payload = decode_access_token(token)
        
        # Extract claims
        user_id = payload["sub"]
        email = payload["email"]
        role = Role(payload["role"])
        
        # Get tenant assignments for staff from DB (fresh query)
        assigned_tenant_ids = []
        if role == Role.STAFF:
            assignments = db.query(UserTenantDB).filter(
                UserTenantDB.user_id == user_id
            ).all()
            assigned_tenant_ids = [a.tenant_id for a in assignments]
        
        return User(
            user_id=user_id,
            email=email,
            role=role,
            assigned_tenant_ids=assigned_tenant_ids
        )
    
    except (JWTError, ValueError, KeyError) as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def require_role(required_role: Role, user: User) -> None:
    """
    Enforce role requirement.
    
    Args:
        required_role: Minimum required role
        user: Current user
        
    Raises:
        HTTPException: 403 if user doesn't have required role
    """
    role_hierarchy = {Role.STAFF: 0, Role.OWNER: 1}
    
    if role_hierarchy.get(user.role, -1) < role_hierarchy.get(required_role, 999):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires {required_role.value} role"
        )


def require_tenant_access(tenant_id: str, user: User, modify: bool = False) -> None:
    """
    Enforce tenant access control.
    
    Args:
        tenant_id: Tenant to check access for
        user: Current user
        modify: If True, requires modify permission; else requires view permission
        
    Raises:
        HTTPException: 403 if user doesn't have access
    """
    if modify:
        if not user.can_modify_tenant(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to modify tenant settings"
            )
    else:
        if not user.can_view_tenant(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant not found or access denied"
            )

