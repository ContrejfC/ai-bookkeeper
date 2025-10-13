"""
Admin Compliance API (SOC 2 Min Controls).

Provides owner-only endpoints for audit exports and compliance status.

Endpoints:
- GET /api/admin/audit/export.jsonl - Streaming JSONL export of decision audit log
- GET /api/admin/audit/export.csv - Streaming CSV export of decision audit log
- GET /api/admin/compliance/status - Compliance posture status
"""
import csv
import io
from datetime import datetime, timedelta
from typing import Iterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import DecisionAuditLogDB, TenantSettingsDB
from app.ui.rbac import get_current_user, require_role, Role, User
from app.ops.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_decision_audit_logs(session: Session, days: int = 90) -> Iterator[DecisionAuditLogDB]:
    """
    Stream decision audit logs from the database.
    
    Args:
        session: Database session
        days: Number of days to export (default=90)
    
    Yields:
        DecisionAuditLogDB records
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Stream results instead of loading all at once
    query = session.query(DecisionAuditLogDB).filter(
        DecisionAuditLogDB.timestamp >= cutoff
    ).order_by(DecisionAuditLogDB.timestamp.desc())
    
    for record in query.yield_per(1000):
        yield record


@router.get("/api/admin/audit/export.jsonl")
async def export_audit_jsonl(
    days: int = 90,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Export decision audit log as streaming JSONL (owner-only).
    
    Args:
        days: Number of days to export (default=90, max=365)
    
    Returns:
        Streaming JSONL response
    
    RBAC: Owner only (403 for staff)
    """
    # RBAC check
    require_role(Role.OWNER, user)
    
    # Validate days
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
    
    logger.info(f"Audit export started by user {user.user_id} (days={days})")
    
    def generate_jsonl() -> Iterator[str]:
        """Generate JSONL output."""
        import json
        
        count = 0
        for record in get_decision_audit_logs(session, days):
            # Convert to dict (exclude sensitive fields if any)
            row = {
                "id": record.id,
                "timestamp": record.timestamp.isoformat() if record.timestamp else None,
                "tenant_id": record.tenant_id,
                "txn_id": record.txn_id,
                "vendor_normalized": record.vendor_normalized,
                "action": record.action,
                "not_auto_post_reason": record.not_auto_post_reason,
                "calibrated_p": record.calibrated_p,
                "threshold_used": record.threshold_used,
                "user_id": record.user_id,
                "cold_start_label_count": record.cold_start_label_count,
                "cold_start_eligible": record.cold_start_eligible,
            }
            
            yield json.dumps(row) + "\n"
            count += 1
        
        logger.info(f"Audit export completed: {count} records")
    
    return StreamingResponse(
        generate_jsonl(),
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": f"attachment; filename=audit_export_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        }
    )


@router.get("/api/admin/audit/export.csv")
async def export_audit_csv(
    days: int = 90,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Export decision audit log as streaming CSV (owner-only).
    
    Args:
        days: Number of days to export (default=90, max=365)
    
    Returns:
        Streaming CSV response
    
    RBAC: Owner only (403 for staff)
    """
    # RBAC check
    require_role(Role.OWNER, user)
    
    # Validate days
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
    
    logger.info(f"Audit CSV export started by user {user.user_id} (days={days})")
    
    def generate_csv() -> Iterator[str]:
        """Generate CSV output."""
        # CSV headers
        fieldnames = [
            "id", "timestamp", "tenant_id", "txn_id", "vendor_normalized",
            "action", "not_auto_post_reason", "calibrated_p", "threshold_used",
            "user_id", "cold_start_label_count", "cold_start_eligible"
        ]
        
        # Create in-memory buffer for CSV writer
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        # Write header
        writer.writeheader()
        yield output.getvalue()
        output.truncate(0)
        output.seek(0)
        
        # Write rows
        count = 0
        for record in get_decision_audit_logs(session, days):
            row = {
                "id": record.id,
                "timestamp": record.timestamp.isoformat() if record.timestamp else "",
                "tenant_id": record.tenant_id or "",
                "txn_id": record.txn_id or "",
                "vendor_normalized": record.vendor_normalized or "",
                "action": record.action or "",
                "not_auto_post_reason": record.not_auto_post_reason or "",
                "calibrated_p": record.calibrated_p if record.calibrated_p is not None else "",
                "threshold_used": record.threshold_used if record.threshold_used is not None else "",
                "user_id": record.user_id or "",
                "cold_start_label_count": record.cold_start_label_count if record.cold_start_label_count is not None else "",
                "cold_start_eligible": record.cold_start_eligible if record.cold_start_eligible is not None else "",
            }
            
            writer.writerow(row)
            yield output.getvalue()
            output.truncate(0)
            output.seek(0)
            count += 1
        
        logger.info(f"Audit CSV export completed: {count} records")
    
    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=audit_export_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/api/admin/compliance/status")
async def get_compliance_status(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Get compliance posture status (owner-only).
    
    Returns:
        - Latest access snapshot timestamp
        - Last backup/restore evidence file
        - Last retention report
        - PR gate status
    
    RBAC: Owner only (403 for staff)
    """
    # RBAC check
    require_role(Role.OWNER, user)
    
    logger.info(f"Compliance status requested by user {user.user_id}")
    
    from pathlib import Path
    
    # Check for latest evidence files
    def get_latest_file(pattern: str, directory: str) -> dict:
        """Get latest file matching pattern."""
        try:
            files = sorted(Path(directory).glob(pattern), reverse=True)
            if files:
                latest = files[0]
                return {
                    "filename": latest.name,
                    "path": str(latest),
                    "timestamp": datetime.fromtimestamp(latest.stat().st_mtime).isoformat(),
                    "size_bytes": latest.stat().st_size
                }
            return None
        except Exception as e:
            logger.warning(f"Error checking {pattern}: {e}")
            return None
    
    status = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "evidence": {
            "access_snapshot": get_latest_file("access_snapshot_*.json", "reports/compliance"),
            "backup_restore": get_latest_file("backup_restore_*.txt", "artifacts/compliance"),
            "data_retention": get_latest_file("data_retention_*.txt", "reports/compliance"),
        },
        "pr_gate": {
            "enabled": Path(".github/workflows/pr_label_gate.yml").exists(),
            "template": Path(".github/pull_request_template.md").exists(),
        },
        "logging": {
            "drain_configured": bool(Path("app/ops/logging.py").exists()),
        }
    }
    
    logger.info("Compliance status retrieved successfully")
    return status

