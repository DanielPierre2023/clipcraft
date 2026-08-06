"""Job queue with database persistence for ClipCraft."""
import sqlite3
import time
import uuid
import os
from enum import Enum
from typing import Optional, Dict, List
from dataclasses import dataclass


def get_db_connection() -> sqlite3.Connection:
    """Create a thread-safe connection with WAL mode enabled."""
    db_path = "/tmp/jobs.db" if os.environ.get("VERCEL") else "jobs.db"
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


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
    progress: int = 0
    stage: str = "queued"
    result_url: Optional[str] = None
    error: Optional[str] = None
    created_at: float = 0.0
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
            "progress": self.progress,
            "stage": self.stage,
            "result_url": self.result_url,
            "error": self.error,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


class JobQueue:
    """Manages persistent video generation jobs."""

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self._init_db()

    def _init_db(self):
        with get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    style TEXT,
                    duration_sec INTEGER,
                    resolution TEXT,
                    status TEXT NOT NULL,
                    progress INTEGER DEFAULT 0,
                    stage TEXT DEFAULT 'queued',
                    result_url TEXT,
                    error TEXT,
                    created_at REAL NOT NULL,
                    completed_at REAL,
                    webhook_url TEXT
                )
            """)
            conn.commit()

    def submit(self, prompt: str, style: str = "cinematic",
               duration_sec: int = 5, resolution: str = "1280x720",
               user_id: str = "", webhook_url: Optional[str] = None) -> str:
        job_id = str(uuid.uuid4())
        created_at = time.time()
        
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO jobs (id, user_id, prompt, style, duration_sec, resolution,
                                 status, progress, stage, created_at, webhook_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (job_id, user_id, prompt, style, duration_sec, resolution,
                  JobStatus.PENDING.value, 0, "queued", created_at, webhook_url))
            conn.commit()

        return job_id

    def update_progress(self, job_id: str, progress: int, stage: str, status: Optional[JobStatus] = None):
        with get_db_connection() as conn:
            if status:
                conn.execute("""
                    UPDATE jobs SET progress = ?, stage = ?, status = ? WHERE id = ?
                """, (min(progress, 100), stage, status.value, job_id))
            else:
                conn.execute("""
                    UPDATE jobs SET progress = ?, stage = ? WHERE id = ?
                """, (min(progress, 100), stage, job_id))
            conn.commit()

    def complete_job(self, job_id: str, result_url: str):
        with get_db_connection() as conn:
            conn.execute("""
                UPDATE jobs SET status = ?, progress = 100, stage = 'completed',
                                result_url = ?, completed_at = ? WHERE id = ?
            """, (JobStatus.COMPLETED.value, result_url, time.time(), job_id))
            conn.commit()

    def fail_job(self, job_id: str, error: str):
        with get_db_connection() as conn:
            conn.execute("""
                UPDATE jobs SET status = ?, error = ?, stage = 'failed',
                                completed_at = ? WHERE id = ?
            """, (JobStatus.FAILED.value, error, time.time(), job_id))
            conn.commit()

    def get_job(self, job_id: str) -> Optional[Job]:
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return None
            return Job(
                id=row["id"], user_id=row["user_id"], prompt=row["prompt"],
                style=row["style"], duration_sec=row["duration_sec"],
                resolution=row["resolution"], status=JobStatus(row["status"]),
                progress=row["progress"], stage=row["stage"],
                result_url=row["result_url"], error=row["error"],
                created_at=row["created_at"], completed_at=row["completed_at"],
                webhook_url=row["webhook_url"]
            )

    def list_user_jobs(self, user_id: str) -> List[Dict]:
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    def cancel_job(self, job_id: str) -> bool:
        with get_db_connection() as conn:
            cursor = conn.execute("""
                UPDATE jobs SET status = ?, completed_at = ?
                WHERE id = ? AND status IN ('pending', 'processing')
            """, (JobStatus.CANCELLED.value, time.time(), job_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_queue_stats(self) -> Dict:
        with get_db_connection() as conn:
            queued = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'pending'").fetchone()[0]
            active = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'processing'").fetchone()[0]
            completed = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'completed'").fetchone()[0]
            failed = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'failed'").fetchone()[0]
            total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            return {
                "queued": queued,
                "active": active,
                "max_concurrent": self.max_concurrent,
                "total_jobs": total,
                "completed": completed,
                "failed": failed,
            }
