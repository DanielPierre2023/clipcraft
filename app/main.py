"""ClipCraft API Server - Video Generation SaaS."""
from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
import os

from .config import settings
from .models import GenerateRequest, JobResponse, JobStatusResponse
from .video_service import VideoService
from .job_queue import JobQueue, JobStatus
from .progress import ProgressTracker
from .billing import BillingSystem

app = FastAPI(title="ClipCraft API", version="1.0.0")

IS_VERCEL = bool(os.environ.get("VERCEL"))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = "/tmp/cache/videos" if IS_VERCEL else os.path.join(BASE_DIR, "cache", "videos")
os.makedirs(CACHE_DIR, exist_ok=True)

video_service = VideoService(
    provider=settings.VIDEO_PROVIDER,
    api_key=settings.VIDEO_API_KEY,
    cache_dir=CACHE_DIR,
)
job_queue = JobQueue(max_concurrent=settings.MAX_CONCURRENT_JOBS)
progress_tracker = ProgressTracker()
billing = BillingSystem()


async def get_user(x_api_key: str = Header(default="demo")):
    user = billing.get_user_by_key(x_api_key)
    if not user and video_service.demo_mode:
        user = billing.get_user_by_key("demo")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user


async def process_video_job(job_id: str):
    job = job_queue.jobs.get(job_id)
    if not job:
        return

    try:
        progress_tracker.update(job_id, 10, "initializing", "Preparing generation")

        result = await video_service.generate(
            prompt=job.prompt,
            style=job.style,
            duration_sec=job.duration_sec,
            resolution=job.resolution,
            progress_callback=lambda p, s, m: progress_tracker.update(job_id, p, s, m)
        )

        job_queue.complete_job(job_id, result["video_url"])
        progress_tracker.update(job_id, 100, "completed", "Video ready")
        billing.record_generation(job.user_id, job.prompt, result["cost"], job.resolution)

    except Exception as e:
        job_queue.fail_job(job_id, str(e))
        progress_tracker.update(job_id, 0, "failed", str(e))


@app.post("/api/generate", response_model=JobResponse)
async def generate_video(req: GenerateRequest, background_tasks: BackgroundTasks, user=Depends(get_user)):
    can, reason = billing.can_generate(user["id"])
    if not can:
        raise HTTPException(status_code=429, detail=reason)

    job_id = job_queue.submit(
        prompt=req.prompt,
        style=req.style,
        duration_sec=req.duration,
        resolution=req.resolution,
        user_id=user["id"]
    )
    progress_tracker.register_job(job_id, webhook_url=req.webhook_url)

    job = job_queue.process_next()
    if job:
        if IS_VERCEL or video_service.demo_mode:
            # On Vercel serverless, execute task inline before worker freezes
            await process_video_job(job.id)
        else:
            background_tasks.add_task(process_video_job, job.id)

    return JobResponse(
        job_id=job_id,
        status="pending",
        message="Video generation job submitted",
        poll_url=f"/api/jobs/{job_id}"
    )


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, user=Depends(get_user)):
    status = job_queue.get_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")

    poll_data = progress_tracker.poll(job_id)
    progress = poll_data.get("progress", 0) if poll_data and "error" not in poll_data else 0
    stage = poll_data.get("stage", "unknown") if poll_data and "error" not in poll_data else "unknown"

    return JobStatusResponse(
        job_id=job_id,
        status=status["status"],
        progress=progress,
        stage=stage,
        result_url=status.get("result_url"),
        error=status.get("error")
    )


@app.get("/api/health")
async def health():
    return {"status": "ok", "demo_mode": video_service.demo_mode}


@app.get("/cache/videos/{filename}")
async def serve_cache_video(filename: str):
    file_path = os.path.join(CACHE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    media_type = "image/svg+xml" if filename.endswith(".svg") else "video/mp4"
    return FileResponse(file_path, media_type=media_type)
