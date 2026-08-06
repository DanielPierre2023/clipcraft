"""ClipCraft API Server - Video Generation SaaS."""
from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
import uuid
import asyncio
import time
import os

from .config import settings
from .models import (
    GenerateRequest, JobResponse, JobStatusResponse,
    HealthResponse, QueueStatsResponse,
)
from .video_service import VideoService
from .job_queue import JobQueue, JobStatus
from .progress import ProgressTracker
from .billing import BillingSystem

app = FastAPI(title="ClipCraft API", version="1.0.0")

IS_VERCEL = bool(os.environ.get("VERCEL"))

# Determine base directory (handle both local and containerised layouts)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if IS_VERCEL:
    CACHE_DIR = "/tmp/cache/videos"
    VIDEOS_DIR = "/tmp/videos"
else:
    CACHE_DIR = os.path.join(BASE_DIR, "cache", "videos")
    VIDEOS_DIR = os.path.join(BASE_DIR, "videos")

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

# Initialize services
video_service = VideoService(
    provider=settings.VIDEO_PROVIDER,
    api_key=settings.VIDEO_API_KEY,
    cache_dir=CACHE_DIR,
)
job_queue = JobQueue(max_concurrent=settings.MAX_CONCURRENT_JOBS)
progress_tracker = ProgressTracker()
billing = BillingSystem()

# Only mount static files and serve index.html when running locally (not on Vercel).
# Vercel serves static files from public/ automatically via its routing config.
if not IS_VERCEL:
    from fastapi.staticfiles import StaticFiles

    _static_dir = os.path.join(BASE_DIR, "public")
    # Fall back to legacy static/ path for backwards compat
    if not os.path.isdir(_static_dir):
        _static_dir = os.path.join(BASE_DIR, "static")

    if os.path.isdir(_static_dir):
        app.mount("/static", StaticFiles(directory=_static_dir), name="static")


# --- API key authentication ---
async def get_user(x_api_key: str = Header(default="demo")):
    """Authenticate user by API key. Falls back to demo user."""
    user = billing.get_user_by_key(x_api_key)
    if not user:
        # In demo mode, accept any key and return demo user
        if video_service.demo_mode:
            user = billing.get_user_by_key("demo")
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return user


# --- Background video generation task ---
async def process_video_job(job_id: str):
    """Background task that processes a video generation job."""
    job = job_queue.jobs.get(job_id)
    if not job:
        return

    try:
        progress_tracker.update(job_id, 5, "initializing",
                                "Loading model and preparing generation")

        # Call the video generation API
        result = await video_service.generate(
            prompt=job.prompt,
            style=job.style,
            duration_sec=job.duration_sec,
            resolution=job.resolution,
            progress_callback=lambda p, s, m:
                progress_tracker.update(job_id, p, s, m)
        )

        progress_tracker.update(job_id, 95, "uploading",
                                "Uploading to CDN")

        video_url = result["video_url"]
        job_queue.complete_job(job_id, video_url)

        progress_tracker.update(job_id, 100, "completed",
                                "Video ready for download")

        billing.record_generation(
            job.user_id, job.prompt,
            result["cost"], job.resolution
        )

    except Exception as e:
        job_queue.fail_job(job_id, str(e))
        progress_tracker.update(job_id, 0, "failed", str(e))


# --- Endpoints ---
if not IS_VERCEL:
    @app.get("/")
    async def serve_index():
        """Serve the main frontend page (local dev only; Vercel handles this via routing)."""
        for folder in ("public", "static"):
            index_path = os.path.join(BASE_DIR, folder, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path, media_type="text/html")
        return JSONResponse({"message": "ClipCraft API is running. Visit /docs for API documentation."})


@app.post("/api/generate", response_model=JobResponse)
async def generate_video(req: GenerateRequest,
                         background_tasks: BackgroundTasks,
                         user=Depends(get_user)):
    """Submit a video generation job. Returns immediately with a job ID."""
    # Check billing limits
    can, reason = billing.can_generate(user["id"])
    if not can:
        raise HTTPException(status_code=429, detail=reason)

    # Submit to job queue
    job_id = job_queue.submit(
        prompt=req.prompt,
        style=req.style,
        duration_sec=req.duration,
        resolution=req.resolution,
        user_id=user["id"]
    )

    # Register progress tracking
    progress_tracker.register_job(job_id, webhook_url=req.webhook_url)

    # Start processing in the background
    job = job_queue.process_next()
    if job:
        background_tasks.add_task(process_video_job, job.id)

    return JobResponse(
        job_id=job_id,
        status="pending",
        message="Video generation job submitted",
        poll_url=f"/api/jobs/{job_id}"
    )


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, user=Depends(get_user)):
    """Poll for job status and progress."""
    status = job_queue.get_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")

    poll_data = progress_tracker.poll(job_id)
    progress = 0
    stage = "unknown"
    estimated = None

    if poll_data and "error" not in poll_data:
        progress = poll_data.get("progress", poll_data.get("percent", 0))
        stage = poll_data.get("stage", "unknown")
        if 0 < progress < 100:
            estimated = int((100 - progress) * 1.5)

    return JobStatusResponse(
        job_id=job_id,
        status=status["status"],
        progress=progress,
        stage=stage,
        result_url=status.get("result_url"),
        error=status.get("error"),
        estimated_remaining_sec=estimated
    )


@app.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: str, user=Depends(get_user)):
    """Cancel a pending or active job."""
    success = job_queue.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or already finished")
    return {"message": "Job cancelled", "job_id": job_id}


@app.get("/api/jobs")
async def list_jobs(user=Depends(get_user)):
    """List all jobs for the authenticated user."""
    user_jobs = [
        job.to_dict() for job in job_queue.jobs.values()
        if job.user_id == user["id"]
    ]
    # Sort by created_at descending
    user_jobs.sort(key=lambda j: j.get("created_at", 0), reverse=True)
    return {"jobs": user_jobs, "total": len(user_jobs)}


@app.get("/api/queue/stats")
async def queue_stats():
    """Get queue statistics."""
    return job_queue.get_queue_stats()


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "provider": settings.VIDEO_PROVIDER,
        "demo_mode": video_service.demo_mode,
        "queue": job_queue.get_queue_stats()
    }


# --- Serve generated demo files ---
@app.get("/cache/videos/{filename}")
async def serve_cache_video(filename: str):
    """Serve generated demo video / SVG files."""
    file_path = os.path.join(CACHE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    # Determine media type
    if filename.endswith(".svg"):
        media_type = "image/svg+xml"
    elif filename.endswith(".mp4"):
        media_type = "video/mp4"
    else:
        media_type = "application/octet-stream"
    return FileResponse(file_path, media_type=media_type)
