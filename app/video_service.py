"""Video generation service - wraps Runway ML / Replicate APIs."""
import asyncio
import httpx
import os
import json
import time
import uuid
import struct
import zlib
from pathlib import Path
from typing import Optional, Callable, Dict


class VideoService:
    """Generates videos via Runway ML or Replicate APIs with demo mode fallback."""

    def __init__(self, provider: str = "runway", api_key: str = "",
                 cache_dir: str = "./cache/videos"):
        self.provider = provider
        self.api_key = api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.AsyncClient(timeout=300.0)
        self.demo_mode = not api_key

    async def generate(self, prompt: str, duration_sec: int = 5,
                       resolution: str = "1280x720", style: str = "cinematic",
                       progress_callback: Optional[Callable] = None) -> Dict:
        """Generate a video from a text prompt.

        Returns dict with video_url, duration, resolution, cost.
        """
        if self.demo_mode:
            return await self._generate_demo(prompt, duration_sec,
                                             resolution, progress_callback)

        if self.provider == "runway":
            return await self._generate_runway(prompt, duration_sec,
                                               resolution, style,
                                               progress_callback)
        elif self.provider == "replicate":
            return await self._generate_replicate(prompt, duration_sec,
                                                  resolution, style,
                                                  progress_callback)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    async def _generate_demo(self, prompt, duration_sec, resolution,
                             progress_callback=None):
        """Create a demo animated SVG when no API key is set."""
        if progress_callback:
            progress_callback(10, "preparing", "Demo mode: creating animated preview")

        width, height = map(int, resolution.split("x"))

        # Simulate generation time with progress updates
        for pct in range(20, 90, 15):
            await asyncio.sleep(0.4)
            if progress_callback:
                progress_callback(pct, "generating", f"Demo rendering frame {pct}%")

        # Generate an animated SVG as demo output
        video_id = uuid.uuid4().hex[:8]
        svg_filename = f"demo_{video_id}.svg"
        svg_path = self.cache_dir / svg_filename

        # Hash prompt to get deterministic but varied colors
        prompt_hash = hash(prompt) & 0xFFFFFF
        color1 = f"#{(prompt_hash & 0xFFFFFF):06x}"
        color2 = f"#{((prompt_hash >> 4) & 0xFFFFFF):06x}"
        color3 = f"#{((prompt_hash >> 8) & 0xFFFFFF):06x}"

        # Truncate prompt for display
        display_prompt = prompt[:60] + "..." if len(prompt) > 60 else prompt

        svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0f0f23"/>
      <stop offset="50%" style="stop-color:#1a1a3e"/>
      <stop offset="100%" style="stop-color:#0f0f23"/>
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{color1}"/>
      <stop offset="50%" style="stop-color:{color2}"/>
      <stop offset="100%" style="stop-color:{color3}"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <rect width="{width}" height="{height}" fill="url(#bg)"/>

  <!-- Animated circles -->
  <circle cx="{width*0.3}" cy="{height*0.4}" r="60" fill="{color1}" opacity="0.3" filter="url(#glow)">
    <animate attributeName="r" values="60;90;60" dur="{duration_sec}s" repeatCount="indefinite"/>
    <animate attributeName="cx" values="{width*0.3};{width*0.5};{width*0.3}" dur="{duration_sec*1.5}s" repeatCount="indefinite"/>
  </circle>
  <circle cx="{width*0.7}" cy="{height*0.6}" r="45" fill="{color2}" opacity="0.3" filter="url(#glow)">
    <animate attributeName="r" values="45;75;45" dur="{duration_sec*0.8}s" repeatCount="indefinite"/>
    <animate attributeName="cy" values="{height*0.6};{height*0.3};{height*0.6}" dur="{duration_sec*1.2}s" repeatCount="indefinite"/>
  </circle>
  <circle cx="{width*0.5}" cy="{height*0.5}" r="30" fill="{color3}" opacity="0.25" filter="url(#glow)">
    <animate attributeName="r" values="30;55;30" dur="{duration_sec*1.1}s" repeatCount="indefinite"/>
  </circle>

  <!-- Animated lines -->
  <line x1="0" y1="{height*0.5}" x2="{width}" y2="{height*0.5}" stroke="url(#accent)" stroke-width="2" opacity="0.4">
    <animate attributeName="y1" values="{height*0.5};{height*0.3};{height*0.5}" dur="{duration_sec}s" repeatCount="indefinite"/>
    <animate attributeName="y2" values="{height*0.5};{height*0.7};{height*0.5}" dur="{duration_sec}s" repeatCount="indefinite"/>
  </line>

  <!-- Title text -->
  <text x="{width/2}" y="{height*0.35}" text-anchor="middle" fill="white" font-family="system-ui, sans-serif" font-size="28" font-weight="bold" opacity="0.9">
    ClipCraft Demo
    <animate attributeName="opacity" values="0.9;1;0.9" dur="2s" repeatCount="indefinite"/>
  </text>

  <!-- Prompt text -->
  <text x="{width/2}" y="{height*0.55}" text-anchor="middle" fill="#a78bfa" font-family="system-ui, sans-serif" font-size="16" opacity="0.8">
    {display_prompt}
  </text>

  <!-- Duration / resolution info -->
  <text x="{width/2}" y="{height*0.7}" text-anchor="middle" fill="#666" font-family="system-ui, sans-serif" font-size="13">
    {duration_sec}s | {resolution} | {style if 'style' in dir() else 'cinematic'}
  </text>

  <!-- Animated progress bar at bottom -->
  <rect x="{width*0.1}" y="{height*0.85}" width="{width*0.8}" height="4" rx="2" fill="#333"/>
  <rect x="{width*0.1}" y="{height*0.85}" width="0" height="4" rx="2" fill="url(#accent)">
    <animate attributeName="width" values="0;{width*0.8};0" dur="{duration_sec}s" repeatCount="indefinite"/>
  </rect>
</svg>'''

        svg_path.write_text(svg_content)

        if progress_callback:
            progress_callback(95, "finalizing", "Demo video ready")

        return {
            "video_url": f"/cache/videos/{svg_filename}",
            "video_path": str(svg_path),
            "duration": duration_sec,
            "resolution": resolution,
            "cost": 0.0,
            "demo": True,
        }

    async def _generate_runway(self, prompt, duration_sec, resolution,
                               style, progress_callback=None):
        """Generate video using Runway ML Gen-3 API."""
        if progress_callback:
            progress_callback(10, "submitting", "Sending to Runway ML API")

        response = await self.client.post(
            "https://api.runwayml.com/v1/generations",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "prompt": prompt,
                "duration": duration_sec,
                "resolution": resolution,
                "style": style,
            }
        )
        response.raise_for_status()
        job = response.json()
        job_id = job["id"]

        # Poll for completion
        result = await self._poll_job(
            f"https://api.runwayml.com/v1/generations/{job_id}",
            {"Authorization": f"Bearer {self.api_key}"},
            progress_callback
        )
        return result

    async def _generate_replicate(self, prompt, duration_sec, resolution,
                                  style, progress_callback=None):
        """Generate video using Replicate API."""
        if progress_callback:
            progress_callback(10, "submitting", "Sending to Replicate API")

        response = await self.client.post(
            "https://api.replicate.com/v1/predictions",
            headers={
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "version": "latest",
                "input": {
                    "prompt": f"{style}: {prompt}",
                    "num_frames": duration_sec * 24,
                    "width": int(resolution.split("x")[0]),
                    "height": int(resolution.split("x")[1]),
                }
            }
        )
        response.raise_for_status()
        prediction = response.json()

        result = await self._poll_job(
            prediction["urls"]["get"],
            {"Authorization": f"Token {self.api_key}"},
            progress_callback
        )
        return result

    async def _poll_job(self, url, headers, progress_callback=None,
                        timeout: int = 600):
        """Poll a generation job until completion."""
        start = time.time()
        while time.time() - start < timeout:
            resp = await self.client.get(url, headers=headers)
            resp.raise_for_status()
            status = resp.json()

            if status.get("status") == "succeeded":
                output = status.get("output", {})
                return {
                    "video_url": output.get("url", output.get("video")),
                    "duration": status.get("duration", 5),
                    "resolution": status.get("resolution", "1280x720"),
                    "cost": status.get("cost", 0.05),
                }
            elif status.get("status") == "failed":
                raise RuntimeError(f"Generation failed: {status.get('error')}")

            pct = status.get("progress", 0)
            if progress_callback and pct:
                progress_callback(int(pct * 100), "generating",
                                  "Rendering video frames")

            await asyncio.sleep(5)

        raise TimeoutError("Video generation timed out")

    def get_status(self, job_id: str) -> Dict:
        """Get the status of a generation job (sync wrapper)."""
        return {"job_id": job_id, "status": "unknown",
                "message": "Use async polling for real-time status"}
