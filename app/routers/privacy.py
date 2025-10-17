"""
Privacy and training data management endpoints.
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import json
import logging

from app.db.session import get_db
from app.services.labels import LabelsService

router = APIRouter(prefix="/api/privacy", tags=["privacy"])
logger = logging.getLogger(__name__)


class ConsentRequest(BaseModel):
    """Consent toggle request."""
    opt_in: bool


class ConsentResponse(BaseModel):
    """Consent status response."""
    opt_in: bool
    actor: Optional[str] = None
    created_at: str


class PurgeResponse(BaseModel):
    """Purge result response."""
    deleted_count: int
    salt_rotated: bool


def get_tenant_id(request: Request) -> str:
    """Extract tenant_id from request state (set by auth middleware)."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return tenant_id


@router.post("/consent", response_model=ConsentResponse)
def set_consent(
    body: ConsentRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Set training data consent for tenant.
    
    POST /api/privacy/consent
    {
      "opt_in": true/false
    }
    
    Returns:
    {
      "opt_in": true,
      "actor": "user@example.com",
      "created_at": "2025-10-17T12:00:00Z"
    }
    
    Default: opt_out (no training data collected)
    """
    tenant_id = get_tenant_id(request)
    actor = getattr(request.state, "user_email", None)  # Optional
    
    service = LabelsService(db)
    entry = service.set_consent(tenant_id, body.opt_in, actor)
    
    logger.info(f"Consent {entry.state} for tenant {tenant_id} by {actor}")
    
    return ConsentResponse(
        opt_in=(entry.state == 'opt_in'),
        actor=entry.actor,
        created_at=entry.created_at.isoformat()
    )


@router.get("/consent", response_model=ConsentResponse)
def get_consent(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get current training data consent status.
    
    GET /api/privacy/consent
    
    Returns:
    {
      "opt_in": false,
      "actor": null,
      "created_at": "2025-10-17T12:00:00Z"
    }
    """
    tenant_id = get_tenant_id(request)
    
    service = LabelsService(db)
    opt_in = service.get_consent(tenant_id)
    
    # Get latest consent log entry
    from app.db.models import ConsentLogDB
    from sqlalchemy import desc
    
    latest = db.query(ConsentLogDB).filter(
        ConsentLogDB.tenant_id == tenant_id
    ).order_by(desc(ConsentLogDB.created_at)).first()
    
    return ConsentResponse(
        opt_in=opt_in,
        actor=latest.actor if latest else None,
        created_at=latest.created_at.isoformat() if latest else datetime.utcnow().isoformat()
    )


@router.get("/labels/export")
def export_labels(
    request: Request,
    since: Optional[str] = None,
    until: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export redacted training labels for tenant.
    
    GET /api/privacy/labels/export?since=2025-10-01&until=2025-10-31
    
    Returns: JSONL stream of redacted label events
    
    Format:
    {"id": 1, "payload": {...redacted...}, "approved": true, "created_at": "..."}
    {"id": 2, "payload": {...redacted...}, "approved": false, "created_at": "..."}
    """
    tenant_id = get_tenant_id(request)
    
    # Parse dates
    since_dt = datetime.fromisoformat(since) if since else None
    until_dt = datetime.fromisoformat(until) if until else None
    
    service = LabelsService(db)
    events = service.export_labels(tenant_id, since_dt, until_dt)
    
    logger.info(f"Exporting {len(events)} labels for tenant {tenant_id}")
    
    # Stream JSONL
    def generate():
        for event in events:
            yield json.dumps(event) + "\n"
    
    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": f"attachment; filename=labels_{tenant_id}.jsonl"
        }
    )


@router.delete("/labels/purge", response_model=PurgeResponse)
def purge_labels(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Purge all training labels for tenant and rotate salt.
    
    DELETE /api/privacy/labels/purge
    
    Returns:
    {
      "deleted_count": 42,
      "salt_rotated": true
    }
    
    This operation:
    - Deletes all label_events for tenant
    - Rotates the redaction salt (invalidates old hashes)
    - Cannot be undone
    """
    tenant_id = get_tenant_id(request)
    
    service = LabelsService(db)
    count = service.purge_labels(tenant_id)
    
    logger.warning(f"Purged {count} labels for tenant {tenant_id} (salt rotated)")
    
    return PurgeResponse(
        deleted_count=count,
        salt_rotated=True
    )

