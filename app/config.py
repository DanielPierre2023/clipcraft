"""Configuration loaded from environment variables."""
import os
from pydantic_settings import BaseSettings


IS_VERCEL = bool(os.environ.get("VERCEL"))


class Settings(BaseSettings):
    VIDEO_PROVIDER: str = "runway"  # "runway", "pika", or "stability"
    VIDEO_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///tmp/clipcraft.db" if IS_VERCEL else "sqlite:///./clipcraft.db"
    MAX_CONCURRENT_JOBS: int = 3
    MAX_VIDEO_DURATION: int = 15  # seconds
    STORAGE_BUCKET: str = "clipcraft-videos"
    WEBHOOK_SECRET: str = ""
    DEMO_API_KEY: str = "demo"
    CACHE_DIR: str = "/tmp/cache" if IS_VERCEL else "./cache"

    class Config:
        env_file = ".env"


settings = Settings()
