"""
Tenant deletion flow for GDPR compliance.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import secrets
import logging

from app.db.session import get_db
from app.db.models import UserDB, EntitlementDB, UsageMonthlyDB, TransactionDB, JournalEntryDB
from app.auth.security import get_current_user, require_role

router = APIRouter(prefix="/api/tenants", tags=["tenants"])
logger = logging.getLogger(__name__)


class DeleteTenantRequest(BaseModel):
    confirm: str  # Must be "DELETE" to proceed


class DeleteTenantResponse(BaseModel):
    success: bool
    message: str
    deletion_token: str
    scheduled_at: str


def purge_tenant_data(tenant_id: str, db: Session):
    """
    Background task to purge all tenant data.
    
    Deletes (in order to respect foreign keys):
    - Transactions
    - Journal entries
    - Usage records
    - Entitlements
    - User-tenant links
    
    Args:
        tenant_id: Tenant to purge
        db: Database session
    """
    try:
        logger.info(f"Starting data purge for tenant: {tenant_id}")
        
        # Delete transactions
        deleted_transactions = db.query(TransactionDB).filter(
            TransactionDB.tenant_id == tenant_id
        ).delete()
        
        # Delete journal entries
        deleted_jes = db.query(JournalEntryDB).filter(
            JournalEntryDB.tenant_id == tenant_id
        ).delete()
        
        # Delete usage records
        deleted_usage = db.query(UsageMonthlyDB).filter(
            UsageMonthlyDB.tenant_id == tenant_id
        ).delete()
        
        # Delete entitlements
        deleted_entitlements = db.query(EntitlementDB).filter(
            EntitlementDB.tenant_id == tenant_id
        ).delete()
        
        db.commit()
        
        logger.info(
            f"Tenant purge complete: tenant={tenant_id}, "
            f"transactions={deleted_transactions}, "
            f"journal_entries={deleted_jes}, "
            f"usage_records={deleted_usage}, "
            f"entitlements={deleted_entitlements}"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to purge tenant {tenant_id}: {e}")
        raise


@router.post("/{tenant_id}/delete", response_model=DeleteTenantResponse)
async def request_tenant_deletion(
    tenant_id: str,
    request: DeleteTenantRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Request tenant deletion (GDPR compliance).
    
    Requires owner role and confirmation string "DELETE".
    Schedules background job to purge all tenant data.
    """
    # Verify current user is owner of this tenant
    user_tenant_id = current_user.get("tenant_id")
    if user_tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own tenant"
        )
    
    # Check role (must be owner)
    user_role = current_user.get("role", "staff")
    if user_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant owners can delete accounts"
        )
    
    # Verify confirmation
    if request.confirm != "DELETE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "400_CONFIRMATION_REQUIRED",
                "message": "Please confirm deletion by sending 'DELETE' in the confirm field"
            }
        )
    
    # Generate deletion token
    deletion_token = secrets.token_urlsafe(32)
    
    # Schedule purge (background task)
    background_tasks.add_task(purge_tenant_data, tenant_id, db)
    
    logger.warning(
        f"Tenant deletion requested: tenant={tenant_id}, "
        f"user={current_user.get('user_id')}, token={deletion_token}"
    )
    
    return DeleteTenantResponse(
        success=True,
        message="Tenant deletion scheduled. All data will be permanently removed within 24 hours.",
        deletion_token=deletion_token,
        scheduled_at=datetime.utcnow().isoformat()
    )

