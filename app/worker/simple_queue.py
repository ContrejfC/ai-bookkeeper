"""
Simple In-Memory Job Queue (No Redis Required)
==============================================

This is a fallback job queue that works without Redis. It stores jobs in memory
and processes them in background threads.

For production with Redis, use queue.py instead.

Features:
--------
- No external dependencies (no Redis needed)
- Thread-safe job storage
- Progress tracking
- Job status updates
- Automatic cleanup of old jobs

Limitations:
-----------
- Jobs lost on restart (no persistence)
- Single-server only (no distributed workers)
- Limited to thread-based concurrency

Usage:
------
```python
from app.worker.simple_queue import enqueue_job, get_job_status

# Enqueue a job
job_id = enqueue_job(my_function, args=(arg1, arg2), kwargs={'key': 'value'})

# Check status
status = get_job_status(job_id)
print(status['progress'])  # 0-100
```
"""
import uuid
import threading
import time
import logging
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import traceback

logger = logging.getLogger(__name__)

# Global job storage (in-memory)
_jobs: Dict[str, Dict[str, Any]] = {}
_jobs_lock = threading.Lock()

# Thread pool for executing jobs
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="worker")

# Cleanup thread
_cleanup_thread: Optional[threading.Thread] = None


class JobStatus:
    """Job status constants."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


def enqueue_job(
    func: Callable,
    args: tuple = (),
    kwargs: Optional[Dict[str, Any]] = None,
    job_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None
) -> str:
    """
    Enqueue a job for background processing.
    
    Args:
        func: Function to execute
        args: Positional arguments
        kwargs: Keyword arguments
        job_id: Optional custom job ID
        meta: Additional metadata
        
    Returns:
        job_id: Unique job identifier
    """
    if kwargs is None:
        kwargs = {}
    if meta is None:
        meta = {}
    
    # Generate job ID
    if job_id is None:
        job_id = f"job_{uuid.uuid4().hex[:16]}"
    
    # Create job record
    job_data = {
        "id": job_id,
        "status": JobStatus.PENDING,
        "progress": 0,
        "message": "Job queued",
        "result": None,
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "finished_at": None,
        "meta": meta
    }
    
    # Store job
    with _jobs_lock:
        _jobs[job_id] = job_data
    
    # Submit to thread pool
    def job_wrapper():
        """Wrapper that tracks job execution."""
        try:
            # Update to running
            _update_job(job_id, {
                "status": JobStatus.RUNNING,
                "started_at": datetime.utcnow().isoformat(),
                "message": "Job started"
            })
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Update to complete
            _update_job(job_id, {
                "status": JobStatus.COMPLETE,
                "progress": 100,
                "message": "Job completed successfully",
                "result": result,
                "finished_at": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            # Update to failed
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            
            logger.error(f"Job {job_id} failed: {error_msg}\n{stack_trace}")
            
            _update_job(job_id, {
                "status": JobStatus.FAILED,
                "message": "Job failed",
                "error": error_msg,
                "finished_at": datetime.utcnow().isoformat()
            })
    
    # Submit to executor
    _executor.submit(job_wrapper)
    
    logger.info(f"Enqueued job {job_id}")
    return job_id


def _update_job(job_id: str, updates: Dict[str, Any]):
    """Update job data (internal use)."""
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id].update(updates)


def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get status of a job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Dict with job status information
    """
    with _jobs_lock:
        job = _jobs.get(job_id)
    
    if job:
        return dict(job)  # Return copy
    else:
        return {
            "id": job_id,
            "status": "not_found",
            "error": "Job not found"
        }


def update_job_progress(job_id: str, progress: int, message: str = ""):
    """
    Update job progress (called from within job function).
    
    Args:
        job_id: Job identifier
        progress: Progress percentage (0-100)
        message: Status message
    """
    _update_job(job_id, {
        "progress": min(max(progress, 0), 100),  # Clamp to 0-100
        "message": message
    })


def cancel_job(job_id: str) -> bool:
    """
    Cancel a job (best effort).
    
    Note: This only marks the job as cancelled. The actual execution
    cannot be stopped if it's already running.
    
    Args:
        job_id: Job identifier
        
    Returns:
        True if job was found and marked as cancelled
    """
    with _jobs_lock:
        if job_id in _jobs:
            job = _jobs[job_id]
            if job["status"] in [JobStatus.PENDING, JobStatus.RUNNING]:
                job["status"] = JobStatus.CANCELLED
                job["message"] = "Job cancelled"
                job["finished_at"] = datetime.utcnow().isoformat()
                return True
    
    return False


def get_recent_jobs(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get recent jobs.
    
    Args:
        limit: Maximum number of jobs to return
        
    Returns:
        List of job status dicts
    """
    with _jobs_lock:
        jobs = list(_jobs.values())
    
    # Sort by created_at descending
    jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return jobs[:limit]


def get_company_jobs(company_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get recent jobs for a company.
    
    Args:
        company_id: Company identifier
        limit: Maximum number of jobs to return
        
    Returns:
        List of job status dicts
    """
    with _jobs_lock:
        jobs = [
            job for job in _jobs.values()
            if job.get("meta", {}).get("company_id") == company_id
        ]
    
    # Sort by created_at descending
    jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return jobs[:limit]


def cleanup_old_jobs(max_age_hours: int = 24):
    """
    Remove old completed/failed jobs from memory.
    
    Args:
        max_age_hours: Remove jobs older than this many hours
    """
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
    cutoff_str = cutoff.isoformat()
    
    with _jobs_lock:
        to_remove = []
        for job_id, job in _jobs.items():
            # Remove if finished and old
            if job["status"] in [JobStatus.COMPLETE, JobStatus.FAILED, JobStatus.CANCELLED]:
                finished_at = job.get("finished_at")
                if finished_at and finished_at < cutoff_str:
                    to_remove.append(job_id)
        
        for job_id in to_remove:
            del _jobs[job_id]
    
    if to_remove:
        logger.info(f"Cleaned up {len(to_remove)} old jobs")


def _cleanup_worker():
    """Background thread that cleans up old jobs periodically."""
    while True:
        try:
            time.sleep(3600)  # Run every hour
            cleanup_old_jobs(max_age_hours=24)
        except Exception as e:
            logger.error(f"Cleanup worker error: {e}")


def start_cleanup_worker():
    """Start the background cleanup worker."""
    global _cleanup_thread
    
    if _cleanup_thread is None or not _cleanup_thread.is_alive():
        _cleanup_thread = threading.Thread(
            target=_cleanup_worker,
            daemon=True,
            name="job-cleanup"
        )
        _cleanup_thread.start()
        logger.info("Started job cleanup worker")


# Auto-start cleanup worker on import
start_cleanup_worker()

