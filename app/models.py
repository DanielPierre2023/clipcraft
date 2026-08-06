"""Pydantic request/response models for ClipCraft API."""
from pydantic import BaseModel, Field
from typing import Optional, List


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=500)
    style: str = Field(default="cinematic")
    duration: int = Field(default=5, ge=2, le=15)
    resolution: str = Field(default="1280x720")
    webhook_url: Optional[str] = None


class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str
    poll_url: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    stage: str
    result_url: Optional[str] = None
    error: Optional[str] = None
    estimated_remaining_sec: Optional[int] = None


class UserStatsResponse(BaseModel):
    user_id: str
    tier: str
    videos_this_month: int
    monthly_limit: int
    max_resolution: str
    max_duration_sec: int
    total_cost: float
    watermark: bool


class QueueStatsResponse(BaseModel):
    queued: int
    active: int
    max_concurrent: int
    total_jobs: int
    completed: int
    failed: int


class HealthResponse(BaseModel):
    status: str
    provider: str
    demo_mode: bool
    queue: QueueStatsResponse
