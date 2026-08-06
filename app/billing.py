"""Billing system for ClipCraft video generation SaaS."""
import sqlite3
import uuid
import time
import os
from typing import Optional, Tuple, Dict


def _get_db_path() -> str:
    """Return the SQLite database path, using /tmp/ on Vercel."""
    if os.environ.get("VERCEL"):
        return "/tmp/billing.db"
    return "billing.db"


class BillingSystem:
    """Manages user accounts, API keys, usage tracking, and video tier limits."""

    TIERS = {
        "free": {
            "monthly_videos": 3,
            "max_resolution": "720p",
            "max_duration_sec": 5,
            "price_per_month": 0.00,
            "watermark": True,
            "max_resolution_px": 720,
        },
        "starter": {
            "monthly_videos": 30,
            "max_resolution": "1080p",
            "max_duration_sec": 10,
            "price_per_month": 19.99,
            "watermark": False,
            "max_resolution_px": 1080,
        },
        "pro": {
            "monthly_videos": 200,
            "max_resolution": "4K",
            "max_duration_sec": 15,
            "price_per_month": 49.99,
            "watermark": False,
            "max_resolution_px": 2160,
        },
        "enterprise": {
            "monthly_videos": -1,  # unlimited
            "max_resolution": "4K",
            "max_duration_sec": 30,
            "price_per_month": 149.99,
            "watermark": False,
            "max_resolution_px": 2160,
        }
    }

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _get_db_path()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        self._ensure_demo_user()

    def _init_db(self):
        """Create tables if they do not exist."""
        self.conn.executescript("""
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
        self.conn.commit()

    def _ensure_demo_user(self):
        """Create a demo user for testing without API keys.

        On Vercel, /tmp/ is ephemeral so this runs on every cold start,
        ensuring the demo user always exists.
        """
        row = self.conn.execute(
            "SELECT * FROM users WHERE api_key = ?", ("demo",)
        ).fetchone()
        if not row:
            self.conn.execute(
                "INSERT INTO users (id, email, api_key, tier, created_at) VALUES (?, ?, ?, ?, ?)",
                ("demo-user", "demo@clipcraft.ai", "demo", "pro", time.time())
            )
            self.conn.commit()

    def register_user(self, email: str, tier: str = "free") -> Dict:
        """Register a new user and return their account details."""
        if tier not in self.TIERS:
            raise ValueError(f"Unknown tier: {tier}")
        user_id = str(uuid.uuid4())
        api_key = f"ck_{uuid.uuid4().hex}"
        self.conn.execute(
            "INSERT INTO users (id, email, api_key, tier, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, email, api_key, tier, time.time())
        )
        self.conn.commit()
        return {"id": user_id, "email": email, "api_key": api_key, "tier": tier}

    def get_user_by_key(self, api_key: str) -> Optional[Dict]:
        """Look up a user by API key."""
        row = self.conn.execute(
            "SELECT * FROM users WHERE api_key = ?", (api_key,)
        ).fetchone()
        return dict(row) if row else None

    def can_generate(self, user_id: str) -> Tuple[bool, str]:
        """Check whether the user can generate another video this month."""
        user = self.conn.execute(
            "SELECT tier FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            return False, "User not found"
        tier = self.TIERS[user["tier"]]
        if tier["monthly_videos"] == -1:
            return True, "Unlimited"
        month_start = time.time() - 30 * 86400
        count = self.conn.execute(
            "SELECT COUNT(*) FROM generations WHERE user_id = ? AND created_at > ?",
            (user_id, month_start)
        ).fetchone()[0]
        if count >= tier["monthly_videos"]:
            return False, f"Monthly limit reached ({tier['monthly_videos']} videos)"
        return True, f"{tier['monthly_videos'] - count} videos remaining"

    def record_generation(self, user_id: str, prompt: str,
                          cost: float, resolution: str,
                          duration_sec: int = 5):
        """Record a video generation event."""
        self.conn.execute(
            "INSERT INTO generations (id, user_id, prompt, cost, resolution, duration_sec, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, prompt, cost, resolution, duration_sec, time.time())
        )
        self.conn.commit()

    def get_user_stats(self, user_id: str) -> Dict:
        """Return usage statistics for the user."""
        user = self.conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            return {}
        tier = self.TIERS[user["tier"]]
        month_start = time.time() - 30 * 86400
        row = self.conn.execute(
            "SELECT COUNT(*) as count, COALESCE(SUM(cost), 0) as total_cost "
            "FROM generations WHERE user_id = ? AND created_at > ?",
            (user_id, month_start)
        ).fetchone()
        return {
            "user_id": user_id,
            "tier": user["tier"],
            "videos_this_month": row["count"],
            "monthly_limit": tier["monthly_videos"],
            "max_resolution": tier["max_resolution"],
            "max_duration_sec": tier["max_duration_sec"],
            "total_cost": round(row["total_cost"], 2),
            "watermark": tier["watermark"],
        }
