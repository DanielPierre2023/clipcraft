# backend/app/main.py
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from .database import engine, Base, get_db
from .models import User, VideoJob, JobStatus
from .auth import get_current_user
from .tasks import process_video_generation
from .services.multi_model_router import MultiModelRouter
from .routers import sse, stripe_webhooks

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB Schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(
    title="ClipCraft Production Engine",
    version="2.0.0",
    lifespan=lifespan
)

# Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Sub-Routers
app.include_router(sse.router)
app.include_router(stripe_webhooks.router)

class GenerateVideoPayload(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=1000)
    provider: str = Field(default="runway")
    duration: int = Field(default=5, ge=2, le=15)
    resolution: str = Field(default="1280x720")
    style: str = Field(default="cinematic")
    camera_pan: float = Field(default=0.0)
    camera_tilt: float = Field(default=0.0)
    camera_zoom: float = Field(default=0.0)

@app.post("/api/v1/generate")
async def generate_video(
    payload: GenerateVideoPayload,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    router = MultiModelRouter()
    required_credits = router.calculate_credit_cost(payload.provider, payload.duration, payload.resolution)

    if user.credits_balance < required_credits:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Required: {required_credits}, Available: {user.credits_balance}"
        )

    # Deduct credits atomically
    user.credits_balance -= required_credits

    job = VideoJob(
        user_id=user.id,
        prompt=payload.prompt,
        provider=payload.provider,
        duration_sec=payload.duration,
        resolution=payload.resolution,
        style=payload.style,
        camera_pan=payload.camera_pan,
        camera_tilt=payload.camera_tilt,
        camera_zoom=payload.camera_zoom,
        credits_cost=required_credits,
        status=JobStatus.PENDING
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Trigger Celery background task
    process_video_generation.delay(job.id)

    return {
        "job_id": job.id,
        "status": "queued",
        "credits_deducted": required_credits,
        "remaining_credits": user.credits_balance
    }

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "engine": "ClipCraft-v2.0"}
