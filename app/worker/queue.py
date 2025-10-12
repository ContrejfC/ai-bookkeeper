"""Job queue management using RQ (Redis Queue)."""
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import redis
from rq import Queue
from rq.job import Job
import json
import hashlib

logger = logging.getLogger(__name__)

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_conn = redis.from_url(REDIS_URL)

# Job queues by priority
high_queue = Queue('high', connection=redis_conn)
default_queue = Queue('default', connection=redis_conn)
low_queue = Queue('low', connection=redis_conn)


def enqueue_job(
    func,
    args: tuple = (),
    kwargs: dict = None,
    job_id: Optional[str] = None,
    priority: str = 'default',
    timeout: int = 600,
    ttl: int = 3600,
    meta: Optional[Dict[str, Any]] = None
) -> str:
    """
    Enqueue a job for background processing.
    
    Args:
        func: Function to execute
        args: Positional arguments
        kwargs: Keyword arguments
        job_id: Optional job ID (for idempotency)
        priority: 'high', 'default', or 'low'
        timeout: Job execution timeout in seconds
        ttl: Time to live for job results in seconds
        meta: Additional metadata to store with job
        
    Returns:
        job_id: Unique job identifier
    """
    kwargs = kwargs or {}
    
    # Select queue by priority
    if priority == 'high':
        queue = high_queue
    elif priority == 'low':
        queue = low_queue
    else:
        queue = default_queue
    
    # Enqueue job
    job = queue.enqueue(
        func,
        args=args,
        kwargs=kwargs,
        job_id=job_id,
        job_timeout=timeout,
        result_ttl=ttl,
        meta=meta or {}
    )
    
    logger.info(f"Enqueued job {job.id} ({priority} priority)")
    return job.id


def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get status of a job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Dict with status information
    """
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        
        result = {
            "job_id": job_id,
            "status": job.get_status(),
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "progress": job.meta.get('progress', 0),
            "message": job.meta.get('message', ''),
            "result": None,
            "error": None
        }
        
        if job.is_finished:
            result['result'] = job.result
            result['progress'] = 100
        elif job.is_failed:
            result['error'] = str(job.exc_info) if job.exc_info else 'Unknown error'
            
        return result
        
    except Exception as e:
        logger.error(f"Error fetching job {job_id}: {e}")
        return {
            "job_id": job_id,
            "status": "not_found",
            "error": str(e)
        }


def get_company_jobs(company_id: str, limit: int = 50) -> list:
    """
    Get recent jobs for a company.
    
    Args:
        company_id: Company identifier
        limit: Maximum number of jobs to return
        
    Returns:
        List of job status dicts
    """
    jobs = []
    
    # Search all queues
    for queue in [high_queue, default_queue, low_queue]:
        for job in queue.jobs[:limit]:
            if job.meta.get('company_id') == company_id:
                jobs.append(get_job_status(job.id))
    
    # Sort by created_at descending
    jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jobs[:limit]


def check_idempotency(idempotency_key: str, ttl_hours: int = 24) -> Optional[str]:
    """
    Check if a job with this idempotency key already exists.
    
    Args:
        idempotency_key: Unique key for deduplication
        ttl_hours: How long to remember this key
        
    Returns:
        Existing job_id if found, None otherwise
    """
    key = f"idempotency:{idempotency_key}"
    existing_job_id = redis_conn.get(key)
    
    if existing_job_id:
        return existing_job_id.decode('utf-8')
    
    return None


def set_idempotency(idempotency_key: str, job_id: str, ttl_hours: int = 24):
    """
    Store idempotency key mapping.
    
    Args:
        idempotency_key: Unique key for deduplication
        job_id: Job identifier to store
        ttl_hours: How long to remember this key
    """
    key = f"idempotency:{idempotency_key}"
    redis_conn.setex(key, timedelta(hours=ttl_hours), job_id)


def generate_idempotency_key(company_id: str, operation: str, data_hash: str) -> str:
    """
    Generate an idempotency key.
    
    Args:
        company_id: Company identifier
        operation: Operation name (e.g., 'ingest_csv')
        data_hash: Hash of the data
        
    Returns:
        Idempotency key
    """
    combined = f"{company_id}:{operation}:{data_hash}"
    return hashlib.sha256(combined.encode()).hexdigest()


def update_job_progress(job_id: str, progress: int, message: str = ''):
    """
    Update job progress.
    
    Args:
        job_id: Job identifier
        progress: Progress percentage (0-100)
        message: Optional status message
    """
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        job.meta['progress'] = progress
        job.meta['message'] = message
        job.save_meta()
    except Exception as e:
        logger.error(f"Error updating job progress: {e}")


def cancel_job(job_id: str) -> bool:
    """
    Cancel a job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        True if cancelled, False otherwise
    """
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        job.cancel()
        return True
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        return False

