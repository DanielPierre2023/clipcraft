# backend/app/tasks.py
import os
import asyncio
import json
import redis
import boto3
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .services.multi_model_router import MultiModelRouter
from .services.prompt_expander import PromptExpander

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL_SYNC = os.getenv("DATABASE_URL_SYNC", "postgresql://postgres:postgres@localhost:5432/clipcraft")

celery_app = Celery("clipcraft", broker=REDIS_URL, backend=REDIS_URL)
redis_client = redis.Redis.from_url(REDIS_URL)

sync_engine = create_engine(DATABASE_URL_SYNC, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(bind=sync_engine)

# Cloudflare R2 / AWS S3 Storage Client
s3_client = boto3.client(
    "s3",
    endpoint_url=os.getenv("R2_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
    region_name="auto"
)
BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "clipcraft-outputs")

def publish_sse_progress(job_id: str, progress: int, stage: str, result_url: str = None, error: str = None):
    """Publish real-time task update to Redis Pub/Sub for Server-Sent Events."""
    payload = {
        "job_id": job_id,
        "progress": progress,
        "stage": stage,
        "result_url": result_url,
        "error": error
    }
    redis_client.publish(f"job_updates:{job_id}", json.dumps(payload))

@celery_app.task(bind=True, max_retries=2, default_retry_delay=5)
def process_video_generation(self, job_id: str):
    """Distributed background worker for processing video prompts."""
    loop = asyncio.get_event_loop()
    
    with SyncSessionLocal() as session:
        from .models import VideoJob, JobStatus, User, CreditTransaction
        
        job = session.query(VideoJob).filter(VideoJob.id == job_id).first()
        if not job:
            return

        try:
            job.status = JobStatus.PROCESSING
            session.commit()
            publish_sse_progress(job_id, 5, "enhancing_prompt")

            # 1. Enhance Prompt
            expander = PromptExpander()
            enhanced = loop.run_until_complete(expander.expand_prompt(job.prompt, job.style))
            job.enhanced_prompt = enhanced
            session.commit()

            # 2. Dispatch to Multi-Model Router
            router = MultiModelRouter()
            
            def progress_callback(pct: int, stage_str: str):
                job.progress = pct
                job.stage = stage_str
                session.commit()
                publish_sse_progress(job_id, pct, stage_str)

            raw_output_url = loop.run_until_complete(
                router.dispatch_generation(
                    provider=job.provider,
                    prompt=enhanced,
                    duration_sec=job.duration_sec,
                    resolution=job.resolution,
                    style=job.style,
                    camera_vectors={"pan": job.camera_pan, "tilt": job.camera_tilt, "zoom": job.camera_zoom},
                    progress_cb=progress_callback
                )
            )

            # 3. Finalize Job
            job.result_url = raw_output_url
            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.stage = "completed"
            session.commit()

            publish_sse_progress(job_id, 100, "completed", result_url=raw_output_url)

        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            session.commit()
            publish_sse_progress(job_id, 0, "failed", error=str(exc))
            raise self.retry(exc=exc)
