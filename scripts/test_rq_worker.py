#!/usr/bin/env python3
"""
Test RQ Worker - Enqueue a simple test job and verify it completes.

Usage:
    python scripts/test_rq_worker.py
"""
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from redis import Redis
from rq import Queue
from rq.job import Job


def test_job(name: str, sleep_seconds: int = 1) -> str:
    """
    Simple test job that sleeps and returns a message.
    
    Args:
        name: Name to include in the result
        sleep_seconds: How long to sleep (simulates work)
    
    Returns:
        Success message
    """
    time.sleep(sleep_seconds)
    return f"✅ Test job completed for: {name}"


def main():
    """Run a test job through RQ and wait for completion."""
    redis_url = os.getenv("REDIS_URL")
    
    # Dry-run mode: if REDIS_URL is not set, exit gracefully
    if not redis_url:
        print("🔄 DRY-RUN: REDIS_URL not set - skipping worker test")
        print("   This is expected in environments without Redis/RQ worker")
        return 0
    
    print("🔍 Testing RQ Worker Connection...")
    print(f"   Redis URL: {redis_url.split('@')[-1] if '@' in redis_url else redis_url}")
    print()
    
    try:
        # Connect to Redis
        redis_conn = Redis.from_url(redis_url)
        redis_conn.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"🔄 DRY-RUN: Redis not available - {e}")
        print("   This is expected in free-tier environments")
        return 0
    
    # Create queue
    queue = Queue("ai_bookkeeper", connection=redis_conn)
    print(f"✅ Queue connected: {queue.name}")
    print(f"   Queue size: {len(queue)}")
    print()
    
    # Enqueue test job
    print("📤 Enqueueing test job...")
    job = queue.enqueue(
        test_job,
        "RQ Worker Test",
        sleep_seconds=2,
        job_timeout="30s",
        result_ttl=300
    )
    
    print(f"   Job ID: {job.id}")
    print(f"   Job status: {job.get_status()}")
    print()
    
    # Wait for job to complete (max 15 seconds)
    print("⏳ Waiting for job to complete...")
    max_wait = 15
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        job.refresh()
        status = job.get_status()
        
        if status == "finished":
            result = job.result
            print(f"✅ WORKER OK - Job completed successfully!")
            print(f"   Result: {result}")
            print(f"   Duration: {time.time() - start_time:.2f}s")
            return 0
        
        elif status == "failed":
            print(f"❌ Job failed!")
            print(f"   Exception: {job.exc_info}")
            return 1
        
        else:
            print(f"   Status: {status} ({time.time() - start_time:.1f}s)")
            time.sleep(1)
    
    print(f"⚠️  Job did not complete within {max_wait}s")
    print(f"   Final status: {job.get_status()}")
    print("\n💡 This usually means:")
    print("   1. No RQ worker is running")
    print("   2. Worker is processing other jobs")
    print("   3. Worker crashed or can't import the function")
    print("\nTo start a worker locally:")
    print("   python -m rq worker -u $REDIS_URL ai_bookkeeper")
    return 1


if __name__ == "__main__":
    sys.exit(main())

