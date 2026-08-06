import os
import httpx
from celery import Celery
from .billing import get_billing_db

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("clipcraft", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_video_generation_task(self, job_id: str, prompt: str, provider: str, user_id: str):
    """Distributed task for running multi-model AI video generation."""
    try:
        # 1. Update task state in Redis
        self.update_state(state="PROCESSING", meta={"progress": 20, "stage": "submitting_to_ai"})
        
        # 2. Model Dispatch (e.g., Kling, Runway, Luma, Wan)
        # Call external provider via Async-to-Sync HTTP client
        with httpx.Client(timeout=300.0) as client:
            # Perform generation & polling here...
            result_url = "https://cdn.clipcraft.ai/outputs/sample.mp4"

        # 3. Upload output asset to Cloudflare R2 / S3 Storage
        
        # 4. Finalize DB state & record credit deduction
        return {"status": "SUCCESS", "result_url": result_url, "job_id": job_id}

    except Exception as exc:
        self.retry(exc=exc)
