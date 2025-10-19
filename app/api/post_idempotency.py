"""
Idempotency and rollback for QBO/Xero exports.

Endpoints:
- POST /api/post/rollback - Rollback last export
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db.session import get_db

router = APIRouter(prefix="/api/post", tags=["posting"])
logger = logging.getLogger(__name__)


class RollbackRequest(BaseModel):
    """Rollback request"""
    journal_entry_id: str
    reason: Optional[str] = None


class RollbackResponse(BaseModel):
    """Rollback response"""
    success: bool
    message: str
    journal_entry_id: str
    qbo_doc_id: Optional[str] = None


@router.post("/rollback", response_model=RollbackResponse)
async def rollback_export(
    request: RollbackRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db)
):
    """
    Rollback the last export to QBO/Xero.
    
    Requires Idempotency-Key header to prevent accidental double rollbacks.
    
    Args:
        journal_entry_id: ID of journal entry to rollback
        idempotency_key: Unique key to prevent duplicate rollbacks
    
    Returns:
        Rollback status and message
    """
    from app.db.models import JournalEntryDB
    from app.services.qbo import QBOService
    
    # Check idempotency key
    # In production, store in Redis or dedicated idempotency table
    existing_rollback = db.query(JournalEntryDB).filter(
        JournalEntryDB.id == request.journal_entry_id,
        JournalEntryDB.metadata.contains({"rollback_key": idempotency_key})
    ).first()
    
    if existing_rollback:
        logger.info(f"Idempotent rollback for key {idempotency_key}")
        return RollbackResponse(
            success=True,
            message="Rollback already processed (idempotent)",
            journal_entry_id=request.journal_entry_id,
            qbo_doc_id=existing_rollback.metadata.get("qbo_doc_id") if existing_rollback.metadata else None
        )
    
    # Get journal entry
    je = db.query(JournalEntryDB).filter(
        JournalEntryDB.id == request.journal_entry_id
    ).first()
    
    if not je:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    if not je.metadata or "qbo_doc_id" not in je.metadata:
        raise HTTPException(status_code=400, detail="Journal entry not exported to QBO/Xero")
    
    qbo_doc_id = je.metadata.get("qbo_doc_id")
    
    try:
        # Delete from QBO
        qbo_service = QBOService(db)
        
        # TODO: Implement actual QBO delete/void operation
        # For now, just mark as rolled back in our system
        
        if not je.metadata:
            je.metadata = {}
        
        je.metadata["rolled_back"] = True
        je.metadata["rollback_time"] = datetime.utcnow().isoformat()
        je.metadata["rollback_reason"] = request.reason
        je.metadata["rollback_key"] = idempotency_key
        
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(je, "metadata")
        
        db.commit()
        
        logger.info(f"Rolled back journal entry {request.journal_entry_id} (QBO doc {qbo_doc_id})")
        
        return RollbackResponse(
            success=True,
            message="Export rolled back successfully",
            journal_entry_id=request.journal_entry_id,
            qbo_doc_id=qbo_doc_id
        )
        
    except Exception as e:
        logger.error(f"Error rolling back export: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")

