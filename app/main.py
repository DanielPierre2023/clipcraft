"""FastAPI Application Server for ClipCraft."""
from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
import os

from .config import settings
from .models import GenerateRequest, JobResponse, JobStatusResponse
from .video_service import VideoService
from .job_queue import JobQueue, JobStatus
from .billing import BillingSystem

app = FastAPI(title="ClipCraft API", version="1.0.0")

IS_VERCEL = bool(os.environ.get("VERCEL"))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = "/tmp/cache/videos" if IS_VERCEL else os.path.join(BASE_DIR, "cache", "videos")
os.makedirs(CACHE_DIR, exist_ok=True)

video_service = VideoService(
    provider=settings.VIDEO_PROVIDER,
    api_key=settings.VIDEO_API_KEY,
    cache_dir=CACHE_DIR
)
job_queue = JobQueue(max_concurrent=settings.MAX_CONCURRENT_JOBS)
billing = BillingSystem()

if not IS_VERCEL:
    from fastapi.staticfiles import StaticFiles
    public_dir = os.path.join(BASE_DIR, "public")
    if os.path.isdir(public_dir):
        app.mount("/static", StaticFiles(directory=public_dir), name="static")


async def get_user(x_api_key: str = Header(default="demo")):
    user = billing.get_user_by_key(x_api_key)
    if not user and video_service.demo_mode:
        user = billing.get_user_by_key("demo")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user


async def process_video_job(job_id: str):
    job = job_queue.get_job(job_id)
    if not job:
        return

    try:
        job_queue.update_progress(job_id, 10, "initializing", JobStatus.PROCESSING)

        result = await video_service.generate(
            prompt=job.prompt,
            style=job.style,
            duration_sec=job.duration_sec,
            resolution=job.resolution,
            progress_callback=lambda p, s, m: job_queue.update_progress(job_id, p, s)
        )

        job_queue.complete_job(job_id, result["video_url"])
        billing.record_generation(job.user_id, job.prompt, result["cost"], job.resolution, job.duration_sec)

    except Exception as e:
        job_queue.fail_job(job_id, str(e))


if not IS_VERCEL:
    @app.get("/")
    async def serve_index():
        index_path = os.path.join(BASE_DIR, "public", "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path, media_type="text/html")
        return JSONResponse({"message": "ClipCraft API running"})


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
        user_id=user["id"],
        webhook_url=req.webhook_url
    )

    background_tasks.add_task(process_video_job, job_id)

    return JobResponse(
        job_id=job_id,
        status="pending",
        message="Job queued successfully",
        poll_url=f"/api/jobs/{job_id}"
    )


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, user=Depends(get_user)):
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.id,
        status=job.status.value,
        progress=job.progress,
        stage=job.stage,
        result_url=job.result_url,
        error=job.error,
        estimated_remaining_sec=int((100 - job.progress) * 1.2) if 0 < job.progress < 100 else None
    )


@app.get("/api/jobs")
async def list_jobs(user=Depends(get_user)):
    jobs = job_queue.list_user_jobs(user["id"])
    return {"jobs": jobs, "total": len(jobs)}


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "provider": settings.VIDEO_PROVIDER,
        "demo_mode": video_service.demo_mode,
        "queue": job_queue.get_queue_stats()
    }


@app.get("/cache/videos/{filename}")
async def serve_cache_video(filename: str):
    file_path = os.path.join(CACHE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    media_type = "image/svg+xml" if filename.endswith(".svg") else "video/mp4"
    return FileResponse(file_path, media_type=media_type)
