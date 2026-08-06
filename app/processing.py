"""Video frame processing utilities for ClipCraft."""
import os
import uuid
from pathlib import Path
from typing import Optional, Dict, List


class VideoProcessor:
    """Handles post-processing of generated video frames and files."""

    def __init__(self, output_dir: str = "./videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def add_watermark(self, video_path: str, text: str = "ClipCraft") -> str:
        """Add a watermark overlay to a video file.

        In production, this would use FFmpeg. Returns the path to the
        watermarked file.
        """
        # Placeholder -- in production use subprocess + ffmpeg
        output_path = self.output_dir / f"wm_{Path(video_path).name}"
        # For demo, just copy the file
        if os.path.exists(video_path):
            import shutil
            shutil.copy2(video_path, str(output_path))
        return str(output_path)

    def resize_video(self, video_path: str, resolution: str) -> str:
        """Resize a video to the specified resolution.

        Args:
            video_path: Path to the source video.
            resolution: Target resolution as 'WIDTHxHEIGHT'.

        Returns:
            Path to the resized video file.
        """
        width, height = map(int, resolution.split("x"))
        output_path = self.output_dir / f"resized_{width}x{height}_{Path(video_path).name}"
        # Placeholder -- in production use FFmpeg
        if os.path.exists(video_path):
            import shutil
            shutil.copy2(video_path, str(output_path))
        return str(output_path)

    def extract_thumbnail(self, video_path: str, time_sec: float = 0.5) -> Optional[str]:
        """Extract a thumbnail frame from a video.

        Args:
            video_path: Path to the video file.
            time_sec: Timestamp in seconds to extract frame from.

        Returns:
            Path to the thumbnail image, or None on failure.
        """
        thumb_path = self.output_dir / f"thumb_{Path(video_path).stem}.jpg"
        # Placeholder -- in production use FFmpeg
        return str(thumb_path) if os.path.exists(video_path) else None

    def get_video_info(self, video_path: str) -> Dict:
        """Get metadata about a video file.

        Returns dict with duration, resolution, file_size, codec info.
        """
        if not os.path.exists(video_path):
            return {"error": "File not found"}
        file_size = os.path.getsize(video_path)
        return {
            "path": video_path,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
        }

    def cleanup_old_files(self, max_age_hours: int = 24) -> List[str]:
        """Remove generated video files older than the specified age.

        Returns list of removed file paths.
        """
        import time
        removed = []
        cutoff = time.time() - (max_age_hours * 3600)
        for f in self.output_dir.iterdir():
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink()
                removed.append(str(f))
        return removed
