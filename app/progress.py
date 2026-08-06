"""Progress tracking for long-running video generation jobs."""
import time
from typing import Optional, Dict
from dataclasses import dataclass, field


@dataclass
class ProgressState:
    job_id: str
    percent: int = 0
    stage: str = "queued"
    message: str = ""
    started_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    webhook_url: Optional[str] = None


class ProgressTracker:
    """Tracks progress of video generation jobs for polling and webhooks."""

    def __init__(self):
        self.states: Dict[str, ProgressState] = {}

    def register_job(self, job_id: str, webhook_url: Optional[str] = None):
        """Register a new job for progress tracking."""
        self.states[job_id] = ProgressState(
            job_id=job_id,
            webhook_url=webhook_url
        )

    def update(self, job_id: str, percent: int, stage: str,
               message: str = ""):
        """Update the progress of a job."""
        state = self.states.get(job_id)
        if not state:
            state = ProgressState(job_id=job_id)
            self.states[job_id] = state
        state.percent = min(percent, 100)
        state.stage = stage
        state.message = message
        state.updated_at = time.time()

    def poll(self, job_id: str) -> Dict:
        """Get current progress for a job (used by polling clients)."""
        state = self.states.get(job_id)
        if not state:
            return {"job_id": job_id, "error": "Job not found"}

        elapsed = time.time() - state.started_at
        remaining = None
        if 0 < state.percent < 100:
            rate = state.percent / elapsed
            remaining = int((100 - state.percent) / rate) if rate > 0 else None

        return {
            "job_id": job_id,
            "percent": state.percent,
            "stage": state.stage,
            "message": state.message,
            "elapsed_sec": round(elapsed, 1),
            "estimated_remaining_sec": remaining,
            "progress": state.percent,
        }

    def get_webhook_url(self, job_id: str) -> Optional[str]:
        """Return the webhook URL for a job, if configured."""
        state = self.states.get(job_id)
        return state.webhook_url if state else None
