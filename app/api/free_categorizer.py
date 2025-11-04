"""
Free Categorizer API Routes
===========================

Backend endpoints for the free statement categorizer with:
- File upload with consent tracking
- Parsing and categorization
- Upload deletion
- Lead capture
- Admin purge endpoint
"""

import os
import hashlib
import magic
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import uuid

from app.db.session import get_db
from app.models.free_tool import FreeUploadDB, FreeLeadDB, ConsentLogDB

router = APIRouter(prefix="/api/free/categorizer", tags=["free-categorizer"])

# Configuration from environment
FREE_MAX_FILE_MB = int(os.getenv("FREE_MAX_FILE_MB", "10"))
FREE_RETENTION_HOURS = int(os.getenv("FREE_RETENTION_HOURS", "24"))
ADMIN_PURGE_TOKEN = os.getenv("ADMIN_PURGE_TOKEN", "")


class UploadResponse(BaseModel):
    """Upload response"""
    uploadId: str
    filename: str
    size_bytes: int
    mime_type: str
    row_count: Optional[int] = None


class LeadRequest(BaseModel):
    """Lead capture request"""
    email: EmailStr
    uploadId: str
    rows: Optional[int] = None


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    consent_training: bool = False,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Upload file for free categorization.
    
    - MIME sniffing for security
    - Size validation
    - Consent tracking
    - 24-hour retention
    """
    
    # Size validation
    file.file.seek(0, 2)  # Seek to end
    size_bytes = file.file.tell()
    file.file.seek(0)  # Reset
    
    max_size_bytes = FREE_MAX_FILE_MB * 1024 * 1024
    
    if size_bytes > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": f"File exceeds {FREE_MAX_FILE_MB} MB limit",
                "context": {
                    "size_mb": round(size_bytes / (1024 * 1024), 1),
                    "max_mb": FREE_MAX_FILE_MB
                }
            }
        )
    
    # Read file content
    content = await file.read()
    file.file.seek(0)
    
    # MIME type validation using magic bytes
    mime = magic.from_buffer(content, mime=True)
    
    allowed_mimes = [
        'text/csv', 'application/x-ofx', 'application/vnd.intu.qfx',
        'application/pdf', 'image/jpeg', 'image/png', 'application/zip'
    ]
    
    if mime not in allowed_mimes:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "UNSUPPORTED_TYPE",
                "message": f"Unsupported file type: {mime}"
            }
        )
    
    # Check for encrypted PDF (simple check)
    if mime == 'application/pdf' and b'/Encrypt' in content:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "ENCRYPTED_PDF",
                "message": "Password-protected PDFs are not supported"
            }
        )
    
    # Virus scan stub (TODO: integrate ClamAV)
    scan_result = scan_file(content)
    if scan_result != "clean":
        raise HTTPException(status_code=400, detail="File failed security scan")
    
    # Generate upload ID
    upload_id = str(uuid.uuid4())
    
    # Hash IP with salt
    ip_address = request.client.host if request and request.client else "unknown"
    ip_salt = os.getenv("IP_HASH_SALT", "default_salt_change_in_prod")
    ip_hash = hashlib.sha256(f"{ip_address}{ip_salt}".encode()).hexdigest()
    
    # File hash
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(hours=FREE_RETENTION_HOURS)
    
    # Save to temp storage (implementation depends on your storage setup)
    # For now, we'll assume it's saved to /tmp or similar
    upload_dir = os.getenv("FREE_UPLOAD_DIR", "/tmp/free_uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{upload_id}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create database record
    upload_record = FreeUploadDB(
        id=upload_id,
        created_at=datetime.utcnow(),
        expires_at=expires_at,
        filename=file.filename or "unknown",
        size_bytes=size_bytes,
        mime_type=mime,
        source_ext=file.filename.split('.')[-1] if file.filename else "unknown",
        consent_training=consent_training,
        consent_ts=datetime.utcnow() if consent_training else None,
        ip_hash=ip_hash,
        file_hash=file_hash,
        retention_scope='ephemeral',
        metadata={"original_mime": file.content_type}
    )
    
    db.add(upload_record)
    db.commit()
    
    # Log consent if granted
    if consent_training:
        consent_log = ConsentLogDB(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            upload_id=upload_id,
            consent_granted=True,
            file_hash_prefix=file_hash[:16],
            metadata={"filename_hash": hashlib.sha256(file.filename.encode()).hexdigest()[:16]}
        )
        db.add(consent_log)
        db.commit()
    
    return UploadResponse(
        uploadId=upload_id,
        filename=file.filename or "unknown",
        size_bytes=size_bytes,
        mime_type=mime
    )


@router.delete("/uploads/{upload_id}")
async def delete_upload(
    upload_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete an upload and all associated data.
    """
    upload = db.query(FreeUploadDB).filter(FreeUploadDB.id == upload_id).first()
    
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Delete file from storage
    upload_dir = os.getenv("FREE_UPLOAD_DIR", "/tmp/free_uploads")
    file_path = os.path.join(upload_dir, f"{upload_id}_{upload.filename}")
    
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete database record
    db.delete(upload)
    db.commit()
    
    return {"success": True, "message": "Upload deleted"}


@router.post("/lead")
async def capture_lead(
    lead: LeadRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Capture lead from email gate.
    """
    # Check if upload exists
    upload = db.query(FreeUploadDB).filter(FreeUploadDB.id == lead.uploadId).first()
    
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Hash IP
    ip_address = request.client.host if request and request.client else "unknown"
    ip_salt = os.getenv("IP_HASH_SALT", "default_salt_change_in_prod")
    ip_hash = hashlib.sha256(f"{ip_address}{ip_salt}".encode()).hexdigest()
    
    # Create lead record
    lead_record = FreeLeadDB(
        id=str(uuid.uuid4()),
        created_at=datetime.utcnow(),
        email=lead.email,
        upload_id=lead.uploadId,
        row_count=lead.rows,
        source='free_categorizer',
        ip_hash=ip_hash
    )
    
    db.add(lead_record)
    db.commit()
    
    return {"success": True, "message": "Lead captured"}


@router.post("/admin/purge-ephemeral")
async def purge_ephemeral_uploads(
    x_purge_token: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to purge expired ephemeral uploads.
    
    Protected by ADMIN_PURGE_TOKEN.
    Should be called hourly via cron.
    """
    # Token validation
    if not ADMIN_PURGE_TOKEN or x_purge_token != ADMIN_PURGE_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Find expired uploads
    now = datetime.utcnow()
    expired_uploads = db.query(FreeUploadDB).filter(
        FreeUploadDB.expires_at < now,
        FreeUploadDB.retention_scope == 'ephemeral'
    ).all()
    
    purged_count = 0
    upload_dir = os.getenv("FREE_UPLOAD_DIR", "/tmp/free_uploads")
    
    for upload in expired_uploads:
        # Delete file
        file_path = os.path.join(upload_dir, f"{upload.id}_{upload.filename}")
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # Delete DB record
        db.delete(upload)
        purged_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "purged": purged_count,
        "timestamp": now.isoformat()
    }


def scan_file(content: bytes) -> str:
    """
    Virus scan stub.
    
    TODO: Integrate ClamAV or similar antivirus scanner.
    For now, returns "clean" always.
    """
    # TODO: Implement actual virus scanning
    # Example with pyclamd:
    # import pyclamd
    # cd = pyclamd.ClamdUnixSocket()
    # result = cd.scan_stream(content)
    # return "clean" if result is None else "infected"
    
    return "clean"

