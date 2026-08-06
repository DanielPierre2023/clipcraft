"""Vercel serverless entry point for ClipCraft API."""
import sys
import os

# Add parent directory to path so the app package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set VERCEL env var if not already set (Vercel sets this automatically,
# but this ensures the app detects the serverless environment)
os.environ.setdefault("VERCEL", "1")

from app.main import app

# Vercel expects a variable named `app` or `handler`
handler = app
