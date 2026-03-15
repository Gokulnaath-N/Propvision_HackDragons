import os
import sys
import json
import time
import signal
import redis
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.pipeline.image_pipeline import PropertyPipeline
from src.utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()


class PipelineWorker:
    """
    Background Redis queue worker that picks up listing processing jobs 
    and runs the full pipeline. Runs as a separate process from the API server.
    Handles retries and error recovery.
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.queue_name = "propvision_jobs"
        self.max_retries = 3
        self.running = True
        
        self.redis_client = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379")
        )
        
        self.logger.info("Initializing pipeline...")
        self.pipeline = PropertyPipeline()
        self.logger.info("Worker ready, listening for jobs")
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        self.logger.info("Shutdown signal received, finishing current job...")
        self.running = False

    def run(self):
        """
        Main worker loop. 
        Continuously blocks on the Redis queue waiting for job packages to process.
        """
        self.logger.info(f"Worker started, polling queue: {self.queue_name}")
        
        while self.running:
            try:
                # Blocking pop from Redis (waits up to 5 seconds)
                result = self.redis_client.blpop(
                    self.queue_name,
                    timeout=5
                )
                
                if result is None:
                    continue  # Timeout reached, loop around to check self.running
                
                _, job_data_bytes = result
                job_data = json.loads(job_data_bytes)
                
                self.logger.info(f"Job received: {job_data.get('listing_id')}")
                self._process_job(job_data)
                
            except redis.ConnectionError:
                self.logger.error("Redis connection lost, retrying in 5s")
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                time.sleep(1)
        
        self.logger.info("Worker stopped cleanly")

    def _process_job(self, job_data: dict):
        """
        Executes the PropertyPipeline on the job dict, tracking exponential 
        backoff retries for transient infrastructure failures (like Qdrant).
        """
        listing_id = job_data.get("listing_id")
        image_paths = job_data.get("image_paths", [])
        metadata = job_data.get("metadata", {})
        retry_count = job_data.get("retry_count", 0)
        
        self.logger.info(f"Processing job {listing_id} (attempt {retry_count+1})")
        
        try:
            result = self.pipeline.run(
                listing_id=listing_id,
                raw_image_paths=image_paths,
                metadata=metadata
            )
            
            self.logger.info(f"Job {listing_id} completed successfully")
            self.logger.info(f"  Grade: {result.get('overall_grade')}")
            self.logger.info(f"  Indexed: {result.get('indexed_vectors')} vectors")
            self.logger.info(f"  Time: {result.get('processing_time_seconds')}s")
            
        except Exception as e:
            self.logger.error(f"Job {listing_id} failed: {e}")
            
            if retry_count < self.max_retries:
                # Exponential backoff (retry_count 0 -> 5s, 1 -> 10s, 2 -> 20s)
                retry_delay = (2 ** retry_count) * 5
                self.logger.info(
                    f"Retrying in {retry_delay}s (attempt {retry_count+2}/{self.max_retries+1})"
                )
                time.sleep(retry_delay)
                
                job_data["retry_count"] = retry_count + 1
                
                # Push back onto queue
                self.redis_client.lpush(
                    self.queue_name,
                    json.dumps(job_data)
                )
            else:
                self.logger.error(f"Job {listing_id} failed after {self.max_retries} retries")
                
                # Flag final failure status in Redis for the frontend callback
                failure_status = {
                    "job_id": listing_id,
                    "status": "failed",
                    "progress": 0,
                    "stage": "failed",
                    "error": str(e),
                    "timestamp": time.time()
                }
                self.redis_client.setex(
                    f"job_status:{listing_id}",
                    86400,
                    json.dumps(failure_status)
                )


if __name__ == "__main__":
    worker = PipelineWorker()
    worker.run()
