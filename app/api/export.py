"""
Export API Endpoints (Sprint 11.2)

QBO and Xero export endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.jwt import get_current_user
from app.exporters.xero_exporter import XeroExporter, get_xero_credentials

router = APIRouter(prefix="/api/export", tags=["export"])


@router.post("/xero")
async def export_to_xero(
    tenant_id: str,
    journal_entry_ids: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Export journal entries to Xero.
    
    Idempotent: Safe to retry, skips already-exported entries.
    
    Args:
        tenant_id: Tenant ID
        journal_entry_ids: Optional list of specific JE IDs to export
        date_from: Optional start date filter (YYYY-MM-DD)
        date_to: Optional end date filter (YYYY-MM-DD)
        
    Returns:
        Export summary with posted/skipped/failed counts
    """
    # RBAC: Check user has access to tenant
    # (In production, verify user.tenant_id or user_tenants table)
    
    # Get Xero credentials
    creds = get_xero_credentials(tenant_id, db)
    if not creds:
        raise HTTPException(400, "Xero not connected for this tenant")
    
    # Get journal entries
    jes = _get_journal_entries(tenant_id, journal_entry_ids, date_from, date_to, db)
    
    if not jes:
        return {
            "tenant_id": tenant_id,
            "summary": {
                "total": 0,
                "posted": 0,
                "skipped": 0,
                "failed": 0
            },
            "message": "No journal entries found"
        }
    
    # Export
    exporter = XeroExporter(tenant_id, creds)
    
    results = {
        "posted": [],
        "skipped": [],
        "failed": []
    }
    
    for je in jes:
        try:
            result = exporter.export_journal_entry(je)
            results[result["status"]].append({
                "journal_entry_id": je['id'],
                "external_id": result["external_id"],
                "xero_journal_id": result.get("xero_journal_id"),
                "reason": result.get("reason")
            })
        except Exception as e:
            results["failed"].append({
                "journal_entry_id": je['id'],
                "error": str(e)
            })
    
    return {
        "tenant_id": tenant_id,
        "summary": {
            "total": len(jes),
            "posted": len(results["posted"]),
            "skipped": len(results["skipped"]),
            "failed": len(results["failed"])
        },
        "results": results
    }


def _get_journal_entries(
    tenant_id: str,
    je_ids: Optional[List[str]],
    date_from: Optional[str],
    date_to: Optional[str],
    db: Session
) -> List[Dict]:
    """
    Get journal entries for export.
    
    In production, query JournalEntryDB table.
    For now, returns mock data.
    """
    from app.db.models import JournalEntryDB
    
    query = db.query(JournalEntryDB).filter_by(tenant_id=tenant_id)
    
    if je_ids:
        query = query.filter(JournalEntryDB.id.in_(je_ids))
    
    if date_from:
        query = query.filter(JournalEntryDB.date >= date_from)
    
    if date_to:
        query = query.filter(JournalEntryDB.date <= date_to)
    
    # Convert to dict format
    entries = []
    for je_db in query.all():
        entries.append({
            "id": je_db.id,
            "txn_id": je_db.txn_id,
            "date": str(je_db.date),
            "memo": je_db.memo,
            "lines": je_db.lines,  # JSON field
            "total_amount": je_db.total_amount
        })
    
    return entries


@router.get("/xero/status")
async def xero_export_status(
    tenant_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get Xero export status for tenant.
    
    Returns summary of recent exports.
    """
    from app.db.models import XeroExportLogDB
    from sqlalchemy import func
    
    # Get last 30 days
    logs = db.query(XeroExportLogDB).filter_by(tenant_id=tenant_id).order_by(
        XeroExportLogDB.exported_at.desc()
    ).limit(100).all()
    
    # Summarize
    summary = {
        "total": len(logs),
        "posted": sum(1 for log in logs if log.status == "posted"),
        "skipped": sum(1 for log in logs if log.status == "skipped"),
        "failed": sum(1 for log in logs if log.status == "failed"),
        "last_export": logs[0].exported_at.isoformat() if logs else None
    }
    
    return {
        "tenant_id": tenant_id,
        "summary": summary,
        "recent_exports": [
            {
                "journal_entry_id": log.journal_entry_id,
                "external_id": log.external_id,
                "xero_journal_id": log.xero_journal_id,
                "status": log.status,
                "exported_at": log.exported_at.isoformat()
            }
            for log in logs[:10]
        ]
    }

