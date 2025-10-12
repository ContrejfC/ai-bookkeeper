"""Worker entry point for running background jobs."""
import sys
import logging
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rq import Worker
from app.worker.queue import high_queue, default_queue, low_queue, redis_conn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run the RQ worker."""
    logger.info("Starting AI Bookkeeper worker...")
    
    # Create worker for all queues (high priority first)
    worker = Worker(
        [high_queue, default_queue, low_queue],
        connection=redis_conn
    )
    
    logger.info(f"Worker listening on queues: {[q.name for q in worker.queues]}")
    
    # Start working
    worker.work()


if __name__ == '__main__':
    main()

