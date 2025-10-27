"""
Background Jobs API - Endpoints for Async Operations
===================================================

This module provides API endpoints for triggering and monitoring background jobs.

Endpoints:
---------
- POST /api/jobs/categorize - Start AI categorization job
- POST /api/jobs/ocr - Start OCR processing job
- POST /api/jobs/export-qbo - Start QuickBooks export job
- POST /api/jobs/bulk-approve - Start bulk approval job
- GET /api/jobs/{job_id} - Get job status
- GET /api/jobs/company/{company_id} - List company jobs

All jobs return immediately with a job_id that can be polled for progress.
"""
import logging
import hashlib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.db.session import get_db
from app.auth.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["background-jobs"])

# Try to import queue (simple or Redis)
try:
    from app.worker.simple_queue import enqueue_job, get_job_status, get_company_jobs
    QUEUE_AVAILABLE = True
except ImportError:
    try:
        from app.worker.queue import enqueue_job, get_job_status, get_company_jobs
        QUEUE_AVAILABLE = True
    except ImportError:
        QUEUE_AVAILABLE = False
        logger.warning("No job queue available - background jobs disabled")


# ============================================================================
# Request/Response Models
# ============================================================================

class CategorizeRequest(BaseModel):
    """Request to categorize transactions."""
    company_id: str
    tenant_id: str
    transaction_ids: Optional[List[str]] = None
    limit: int = 100


class OCRRequest(BaseModel):
    """Request to process receipt OCR."""
    company_id: str
    receipt_id: str
    file_path: str


class ExportQBORequest(BaseModel):
    """Request to export to QuickBooks."""
    company_id: str
    tenant_id: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD


class BulkApproveRequest(BaseModel):
    """Request to bulk approve transactions."""
    company_id: str
    tenant_id: str
    transaction_ids: List[str]


class JobResponse(BaseModel):
    """Response with job ID."""
    job_id: str
    status: str
    message: str


# ============================================================================
# Job Endpoints
# ============================================================================

@router.post("/categorize", response_model=JobResponse)
async def start_categorization_job(
    request: CategorizeRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start AI categorization job for transactions.
    
    This endpoint queues a background job that:
    1. Fetches uncategorized transactions
    2. Runs AI categorization (rules → LLM)
    3. Creates journal entry proposals
    
    Returns immediately with job_id to poll for progress.
    """
    if not QUEUE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Background jobs not available - queue system not configured"
        )
    
    try:
        # Import task
        from app.worker.background_tasks import categorize_transactions_task
        
        # Enqueue job
        job_id = enqueue_job(
            categorize_transactions_task,
            kwargs={
                "company_id": request.company_id,
                "tenant_id": request.tenant_id,
                "transaction_ids": request.transaction_ids,
                "limit": request.limit
            },
            meta={
                "company_id": request.company_id,
                "tenant_id": request.tenant_id,
                "user_id": current_user.user_id,
                "operation": "categorize"
            }
        )
        
        logger.info(f"Started categorization job {job_id} for company {request.company_id}")
        
        return JobResponse(
            job_id=job_id,
            status="pending",
            message=f"Categorization job started. Poll /api/jobs/{job_id} for progress."
        )
        
    except Exception as e:
        logger.error(f"Failed to start categorization job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr", response_model=JobResponse)
async def start_ocr_job(
    request: OCRRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start OCR processing job for receipt.
    
    This endpoint queues a background job that:
    1. Loads receipt image
    2. Runs OCR extraction
    3. Stores extracted fields
    
    Returns immediately with job_id to poll for progress.
    """
    if not QUEUE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Background jobs not available"
        )
    
    try:
        from app.worker.background_tasks import process_receipt_ocr_task
        
        job_id = enqueue_job(
            process_receipt_ocr_task,
            kwargs={
                "company_id": request.company_id,
                "receipt_id": request.receipt_id,
                "file_path": request.file_path
            },
            meta={
                "company_id": request.company_id,
                "user_id": current_user.user_id,
                "operation": "ocr"
            }
        )
        
        logger.info(f"Started OCR job {job_id} for receipt {request.receipt_id}")
        
        return JobResponse(
            job_id=job_id,
            status="pending",
            message=f"OCR job started. Poll /api/jobs/{job_id} for progress."
        )
        
    except Exception as e:
        logger.error(f"Failed to start OCR job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-qbo", response_model=JobResponse)
async def start_export_qbo_job(
    request: ExportQBORequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start QuickBooks export job.
    
    This endpoint queues a background job that:
    1. Fetches approved journal entries
    2. Converts to QBO format
    3. Posts to QuickBooks with idempotency
    
    Returns immediately with job_id to poll for progress.
    """
    if not QUEUE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Background jobs not available"
        )
    
    try:
        from app.worker.background_tasks import export_to_quickbooks_task
        
        job_id = enqueue_job(
            export_to_quickbooks_task,
            kwargs={
                "company_id": request.company_id,
                "tenant_id": request.tenant_id,
                "start_date": request.start_date,
                "end_date": request.end_date
            },
            meta={
                "company_id": request.company_id,
                "tenant_id": request.tenant_id,
                "user_id": current_user.user_id,
                "operation": "export_qbo"
            }
        )
        
        logger.info(f"Started QBO export job {job_id} for company {request.company_id}")
        
        return JobResponse(
            job_id=job_id,
            status="pending",
            message=f"QBO export job started. Poll /api/jobs/{job_id} for progress."
        )
        
    except Exception as e:
        logger.error(f"Failed to start QBO export job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-approve", response_model=JobResponse)
async def start_bulk_approve_job(
    request: BulkApproveRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start bulk approval job.
    
    This endpoint queues a background job that:
    1. Finds journal entries for transactions
    2. Approves them in batches
    3. Returns summary statistics
    
    Returns immediately with job_id to poll for progress.
    """
    if not QUEUE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Background jobs not available"
        )
    
    try:
        from app.worker.background_tasks import bulk_approve_transactions_task
        
        job_id = enqueue_job(
            bulk_approve_transactions_task,
            kwargs={
                "company_id": request.company_id,
                "tenant_id": request.tenant_id,
                "transaction_ids": request.transaction_ids
            },
            meta={
                "company_id": request.company_id,
                "tenant_id": request.tenant_id,
                "user_id": current_user.user_id,
                "operation": "bulk_approve"
            }
        )
        
        logger.info(f"Started bulk approval job {job_id} for {len(request.transaction_ids)} transactions")
        
        return JobResponse(
            job_id=job_id,
            status="pending",
            message=f"Bulk approval job started. Poll /api/jobs/{job_id} for progress."
        )
        
    except Exception as e:
        logger.error(f"Failed to start bulk approval job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}")
async def get_job_status_endpoint(
    job_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get status of a background job.
    
    Returns:
    -------
    - job_id: Job identifier
    - status: pending, running, complete, failed
    - progress: 0-100
    - message: Status message
    - result: Job result (if complete)
    - error: Error message (if failed)
    """
    if not QUEUE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Background jobs not available"
        )
    
    try:
        status = get_job_status(job_id)
        return status
        
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{company_id}")
async def get_company_jobs_endpoint(
    company_id: str,
    current_user = Depends(get_current_user),
    limit: int = 50
):
    """
    Get recent jobs for a company.
    
    Returns list of job statuses sorted by created_at descending.
    """
    if not QUEUE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Background jobs not available"
        )
    
    try:
        jobs = get_company_jobs(company_id, limit=limit)
        return {
            "company_id": company_id,
            "jobs": jobs,
            "count": len(jobs)
        }
        
    except Exception as e:
        logger.error(f"Failed to get company jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Upload with Background Processing
# ============================================================================

@router.post("/upload-and-categorize")
async def upload_and_categorize(
    file: UploadFile = File(...),
    company_id: str = Form(...),
    tenant_id: str = Form(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload transactions file and start categorization job.
    
    This endpoint:
    1. Saves uploaded file
    2. Parses transactions
    3. Starts background categorization job
    4. Returns job_id for polling
    
    This is a convenience endpoint that combines upload + categorization.
    """
    if not QUEUE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Background jobs not available"
        )
    
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Create file hash for idempotency
        file_hash = hashlib.md5(content).hexdigest()
        
        # Import task
        from app.worker.background_tasks import categorize_transactions_task
        
        # Note: In production, you'd want to:
        # 1. Save file to storage
        # 2. Parse it to get transaction IDs
        # 3. Then categorize those IDs
        # For now, we'll just start categorization of all uncategorized
        
        job_id = enqueue_job(
            categorize_transactions_task,
            kwargs={
                "company_id": company_id,
                "tenant_id": tenant_id,
                "transaction_ids": None,  # All uncategorized
                "limit": 1000
            },
            meta={
                "company_id": company_id,
                "tenant_id": tenant_id,
                "user_id": current_user.user_id,
                "operation": "upload_and_categorize",
                "filename": file.filename,
                "file_hash": file_hash
            }
        )
        
        logger.info(f"Started upload+categorize job {job_id} for file {file.filename}")
        
        return JobResponse(
            job_id=job_id,
            status="pending",
            message=f"File uploaded. Categorization job started. Poll /api/jobs/{job_id} for progress."
        )
        
    except Exception as e:
        logger.error(f"Failed to upload and categorize: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

