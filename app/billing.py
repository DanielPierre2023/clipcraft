"""Thread-safe SQLite billing system."""
import sqlite3
import uuid
import time
import os
from typing import Optional, Tuple, Dict


def get_billing_db() -> sqlite3.Connection:
    db_path = "/tmp/billing.db" if os.environ.get("VERCEL") else "billing.db"
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


class BillingSystem:

    TIERS = {
        "free": {"monthly_videos": 3, "max_resolution": "720p", "max_duration_sec": 5, "price_per_month": 0.00, "watermark": True},
        "starter": {"monthly_videos": 30, "max_resolution": "1080p", "max_duration_sec": 10, "price_per_month": 19.99, "watermark": False},
        "pro": {"monthly_videos": 200, "max_resolution": "4K", "max_duration_sec": 15, "price_per_month": 49.99, "watermark": False},
        "enterprise": {"monthly_videos": -1, "max_resolution": "4K", "max_duration_sec": 30, "price_per_month": 149.99, "watermark": False}
    }

    def __init__(self):
        self._init_db()
        self._ensure_demo_user()

    def _init_db(self):
        with get_billing_db() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    api_key TEXT UNIQUE NOT NULL,
                    tier TEXT NOT NULL DEFAULT 'free',
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS generations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    prompt TEXT,
                    cost REAL DEFAULT 0.0,
                    resolution TEXT,
                    duration_sec INTEGER,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
            """)
            conn.commit()

    def _ensure_demo_user(self):
        with get_billing_db() as conn:
            row = conn.execute("SELECT * FROM users WHERE api_key = ?", ("demo",)).fetchone()
            if not row:
                conn.execute(
                    "INSERT INTO users (id, email, api_key, tier, created_at) VALUES (?, ?, ?, ?, ?)",
                    ("demo-user", "demo@clipcraft.ai", "demo", "pro", time.time())
                )
                conn.commit()

    def get_user_by_key(self, api_key: str) -> Optional[Dict]:
        with get_billing_db() as conn:
            row = conn.execute("SELECT * FROM users WHERE api_key = ?", (api_key,)).fetchone()
            return dict(row) if row else None

    def can_generate(self, user_id: str) -> Tuple[bool, str]:
        with get_billing_db() as conn:
            user = conn.execute("SELECT tier FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user:
                return False, "User not found"
            tier = self.TIERS[user["tier"]]
            if tier["monthly_videos"] == -1:
                return True, "Unlimited"
            
            month_start = time.time() - 30 * 86400
            count = conn.execute(
                "SELECT COUNT(*) FROM generations WHERE user_id = ? AND created_at > ?",
                (user_id, month_start)
            ).fetchone()[0]

            if count >= tier["monthly_videos"]:
                return False, f"Monthly limit reached ({tier['monthly_videos']} videos)"
            return True, f"{tier['monthly_videos'] - count} videos remaining"

    def record_generation(self, user_id: str, prompt: str, cost: float, resolution: str, duration_sec: int = 5):
        with get_billing_db() as conn:
            conn.execute(
                "INSERT INTO generations (id, user_id, prompt, cost, resolution, duration_sec, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), user_id, prompt, cost, resolution, duration_sec, time.time())
            )
            conn.commit()
