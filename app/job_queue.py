"""Job queue for managing asynchronous video generation jobs."""
import sqlite3
import time
import uuid
import os
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


def _get_db_path() -> str:
    """Return the SQLite database path, using /tmp/ on Vercel."""
    if os.environ.get("VERCEL"):
        return "/tmp/jobs.db"
    return "jobs.db"


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    id: str
    user_id: str
    prompt: str
    style: str
    duration_sec: int
    resolution: str
    status: JobStatus = JobStatus.PENDING
    result_url: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    webhook_url: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "prompt": self.prompt,
            "style": self.style,
            "duration_sec": self.duration_sec,
            "resolution": self.resolution,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "result_url": self.result_url,
            "error": self.error,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


class JobQueue:
    """Manages video generation jobs with in-memory queue and SQLite persistence."""

    def __init__(self, max_concurrent: int = 3, db_path: Optional[str] = None):
        self.max_concurrent = max_concurrent
        self.jobs: Dict[str, Job] = {}
        self.queue: List[str] = []
        self.active: List[str] = []
        self.db_path = db_path or _get_db_path()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        """Create SQLite table for job persistence."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                prompt TEXT NOT NULL,
                style TEXT,
                duration_sec INTEGER,
                resolution TEXT,
                status TEXT NOT NULL,
                result_url TEXT,
                error TEXT,
                created_at REAL NOT NULL,
                completed_at REAL,
                webhook_url TEXT
            )
        """)
        self.conn.commit()

    def submit(self, prompt: str, style: str = "cinematic",
               duration_sec: int = 5, resolution: str = "1280x720",
               user_id: str = "", webhook_url: Optional[str] = None) -> str:
        """Submit a new job to the queue. Returns the job ID."""
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            user_id=user_id,
            prompt=prompt,
            style=style,
            duration_sec=duration_sec,
            resolution=resolution,
            webhook_url=webhook_url,
        )
        self.jobs[job_id] = job
        self.queue.append(job_id)
        self._persist_job(job)
        return job_id

    def process_next(self) -> Optional[Job]:
        """Move the next queued job to active processing.

        Returns the Job if one was available, None otherwise.
        """
        if len(self.active) >= self.max_concurrent:
            return None
        if not self.queue:
            return None

        job_id = self.queue.pop(0)
        job = self.jobs[job_id]
        job.status = JobStatus.PROCESSING
        self.active.append(job_id)
        self._persist_job(job)
        return job

    def complete_job(self, job_id: str, result_url: str) -> str:
        """Mark a job as completed with its result URL."""
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        job.status = JobStatus.COMPLETED
        job.result_url = result_url
        job.completed_at = time.time()
        if job_id in self.active:
            self.active.remove(job_id)
        self._persist_job(job)
        return f"Job {job_id} completed"

    def fail_job(self, job_id: str, error: str) -> str:
        """Mark a job as failed with an error message."""
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        job.status = JobStatus.FAILED
        job.error = error
        job.completed_at = time.time()
        if job_id in self.active:
            self.active.remove(job_id)
        self._persist_job(job)
        return f"Job {job_id} failed: {error}"

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or active job. Returns True if cancelled."""
        job = self.jobs.get(job_id)
        if not job:
            return False
        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
            return False
        job.status = JobStatus.CANCELLED
        job.completed_at = time.time()
        if job_id in self.queue:
            self.queue.remove(job_id)
        if job_id in self.active:
            self.active.remove(job_id)
        self._persist_job(job)
        return True

    def get_status(self, job_id: str) -> Optional[Dict]:
        """Get current status of a job."""
        job = self.jobs.get(job_id)
        if not job:
            # Try loading from SQLite
            job = self._load_job(job_id)
        if not job:
            return None
        return {
            "job_id": job.id,
            "status": job.status.value if isinstance(job.status, JobStatus) else job.status,
            "progress": 0,
            "result_url": job.result_url,
            "error": job.error,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
        }

    def get_queue_stats(self) -> Dict:
        """Return queue statistics."""
        return {
            "queued": len(self.queue),
            "active": len(self.active),
            "max_concurrent": self.max_concurrent,
            "total_jobs": len(self.jobs),
            "completed": sum(1 for j in self.jobs.values()
                             if j.status == JobStatus.COMPLETED),
            "failed": sum(1 for j in self.jobs.values()
                          if j.status == JobStatus.FAILED),
        }

    def _persist_job(self, job: Job):
        """Save job state to SQLite."""
        status_val = job.status.value if isinstance(job.status, JobStatus) else job.status
        self.conn.execute("""
            INSERT OR REPLACE INTO jobs
            (id, user_id, prompt, style, duration_sec, resolution,
             status, result_url, error, created_at, completed_at, webhook_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (job.id, job.user_id, job.prompt, job.style, job.duration_sec,
              job.resolution, status_val, job.result_url, job.error,
              job.created_at, job.completed_at, job.webhook_url))
        self.conn.commit()

    def _load_job(self, job_id: str) -> Optional[Job]:
        """Load a job from SQLite."""
        row = self.conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            return None
        job = Job(
            id=row["id"], user_id=row["user_id"], prompt=row["prompt"],
            style=row["style"], duration_sec=row["duration_sec"],
            resolution=row["resolution"],
            status=JobStatus(row["status"]),
            result_url=row["result_url"], error=row["error"],
            created_at=row["created_at"], completed_at=row["completed_at"],
            webhook_url=row["webhook_url"],
        )
        self.jobs[job_id] = job
        return job
