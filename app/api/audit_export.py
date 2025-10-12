"""
Audit Log CSV Export - Streaming & Scale (Wave-2 Phase 1 Final).

Memory-bounded streaming for 100k+ rows.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import csv
from io import StringIO

from app.db.session import get_db
from app.db.models import DecisionAuditLogDB
from app.ui.rbac import User, get_current_user


router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/export.csv")
async def export_audit_csv(
    start_ts: Optional[str] = None,
    end_ts: Optional[str] = None,
    tenant_id: Optional[str] = None,
    vendor: Optional[str] = None,
    action: Optional[str] = None,
    reason: Optional[str] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Stream audit log as CSV (memory-bounded for 100k+ rows).
    
    Features:
    - Chunked streaming (1000 rows per batch)
    - Memory-bounded (no full dataset load)
    - UTC ISO8601 timestamps
    - All filters supported
    
    CSV Columns:
    - timestamp
    - tenant_id
    - user_id
    - action
    - txn_id
    - vendor_normalized
    - calibrated_p
    - threshold_used
    - not_auto_post_reason
    - cold_start_label_count
    - ruleset_version_id (placeholder)
    - model_version_id (placeholder)
    
    Args:
        start_ts: Start timestamp (ISO8601)
        end_ts: End timestamp (ISO8601)
        tenant_id: Filter by tenant
        vendor: Filter by vendor (partial match)
        action: Filter by action
        reason: Filter by not_auto_post_reason
        user_id: Filter by user
        
    Returns:
        Streaming CSV response
    """
    def generate_csv():
        """Generator function for streaming CSV rows."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header row
        writer.writerow([
            "timestamp",
            "tenant_id",
            "user_id",
            "action",
            "txn_id",
            "vendor_normalized",
            "calibrated_p",
            "threshold_used",
            "not_auto_post_reason",
            "cold_start_label_count",
            "ruleset_version_id",
            "model_version_id"
        ])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)
        
        # Build query with filters
        query = db.query(DecisionAuditLogDB).order_by(
            DecisionAuditLogDB.timestamp.desc()
        )
        
        # Apply filters
        if start_ts:
            query = query.filter(DecisionAuditLogDB.timestamp >= start_ts)
        if end_ts:
            query = query.filter(DecisionAuditLogDB.timestamp <= end_ts)
        if tenant_id:
            query = query.filter(DecisionAuditLogDB.tenant_id == tenant_id)
        if action:
            query = query.filter(DecisionAuditLogDB.action == action)
        if reason:
            query = query.filter(DecisionAuditLogDB.not_auto_post_reason == reason)
        if vendor:
            query = query.filter(DecisionAuditLogDB.vendor_normalized.like(f"%{vendor}%"))
        if user_id:
            query = query.filter(DecisionAuditLogDB.user_id == user_id)
        
        # Stream rows in batches (memory-bounded)
        BATCH_SIZE = 1000
        offset = 0
        
        while True:
            batch = query.offset(offset).limit(BATCH_SIZE).all()
            if not batch:
                break
            
            for entry in batch:
                # Normalize timestamp to UTC ISO8601
                timestamp_utc = entry.timestamp.isoformat() + "Z" if entry.timestamp else ""
                
                writer.writerow([
                    timestamp_utc,
                    entry.tenant_id or "",
                    entry.user_id or "",
                    entry.action or "",
                    entry.txn_id or "",
                    entry.vendor_normalized or "",
                    entry.calibrated_p if entry.calibrated_p is not None else "",
                    entry.threshold_used if entry.threshold_used is not None else "",
                    entry.not_auto_post_reason or "",
                    entry.cold_start_label_count if entry.cold_start_label_count is not None else "",
                    "",  # ruleset_version_id (placeholder)
                    ""   # model_version_id (placeholder)
                ])
                
                # Yield after each row (chunked streaming)
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)
            
            offset += BATCH_SIZE
    
    # Generate filename with timestamp
    filename = f"audit_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache"
        }
    )

