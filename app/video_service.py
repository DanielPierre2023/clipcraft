"""Video generation service - wraps Runway ML / Replicate APIs."""
import asyncio
import httpx
import time
import uuid
from pathlib import Path
from typing import Optional, Callable, Dict


class VideoService:
    """Generates videos via Runway ML or Replicate APIs with demo mode fallback."""

    def __init__(self, provider: str = "runway", api_key: str = "",
                 cache_dir: str = "/tmp/cache/videos"):
        self.provider = provider
        self.api_key = api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.demo_mode = not api_key

    async def generate(self, prompt: str, duration_sec: int = 5,
                       resolution: str = "1280x720", style: str = "cinematic",
                       progress_callback: Optional[Callable] = None) -> Dict:
        """Generate a video from a text prompt."""
        if self.demo_mode:
            return await self._generate_demo(prompt, duration_sec, resolution, progress_callback)

        async with httpx.AsyncClient(timeout=300.0) as client:
            if self.provider == "runway":
                return await self._generate_runway(client, prompt, duration_sec, resolution, style, progress_callback)
            elif self.provider == "replicate":
                return await self._generate_replicate(client, prompt, duration_sec, resolution, style, progress_callback)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")

    async def _generate_demo(self, prompt, duration_sec, resolution, progress_callback=None):
        if progress_callback:
            progress_callback(10, "preparing", "Demo mode: creating animated preview")

        width, height = map(int, resolution.split("x"))

        for pct in range(20, 90, 25):
            await asyncio.sleep(0.2)
            if progress_callback:
                progress_callback(pct, "generating", f"Demo rendering frame {pct}%")

        video_id = uuid.uuid4().hex[:8]
        svg_filename = f"demo_{video_id}.svg"
        svg_path = self.cache_dir / svg_filename

        prompt_hash = hash(prompt) & 0xFFFFFF
        color1 = f"#{(prompt_hash & 0xFFFFFF):06x}"
        color2 = f"#{((prompt_hash >> 4) & 0xFFFFFF):06x}"
        display_prompt = prompt[:60] + "..." if len(prompt) > 60 else prompt

        svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <rect width="{width}" height="{height}" fill="#0f0f23"/>
  <circle cx="{width*0.3}" cy="{height*0.4}" r="80" fill="{color1}" opacity="0.4"/>
  <circle cx="{width*0.7}" cy="{height*0.6}" r="60" fill="{color2}" opacity="0.4"/>
  <text x="{width/2}" y="{height*0.4}" text-anchor="middle" fill="white" font-family="system-ui" font-size="24" font-weight="bold">ClipCraft Demo</text>
  <text x="{width/2}" y="{height*0.55}" text-anchor="middle" fill="#a78bfa" font-family="system-ui" font-size="16">{display_prompt}</text>
</svg>'''

        svg_path.write_text(svg_content)

        if progress_callback:
            progress_callback(100, "finalizing", "Demo video ready")

        return {
            "video_url": f"/cache/videos/{svg_filename}",
            "video_path": str(svg_path),
            "duration": duration_sec,
            "resolution": resolution,
            "cost": 0.0,
            "demo": True,
        }

    async def _generate_runway(self, client: httpx.AsyncClient, prompt, duration_sec, resolution, style, progress_callback=None):
        if progress_callback:
            progress_callback(10, "submitting", "Sending to Runway ML API")

        response = await client.post(
            "https://api.runwayml.com/v1/generations",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"prompt": prompt, "duration": duration_sec, "resolution": resolution, "style": style}
        )
        response.raise_for_status()
        job = response.json()
        
        return await self._poll_job(client, f"https://api.runwayml.com/v1/generations/{job['id']}", {"Authorization": f"Bearer {self.api_key}"}, progress_callback)

    async def _generate_replicate(self, client: httpx.AsyncClient, prompt, duration_sec, resolution, style, progress_callback=None):
        if progress_callback:
            progress_callback(10, "submitting", "Sending to Replicate API")

        response = await client.post(
            "https://api.replicate.com/v1/predictions",
            headers={"Authorization": f"Token {self.api_key}", "Content-Type": "application/json"},
            json={"version": "latest", "input": {"prompt": f"{style}: {prompt}", "num_frames": duration_sec * 24}}
        )
        response.raise_for_status()
        prediction = response.json()

        return await self._poll_job(client, prediction["urls"]["get"], {"Authorization": f"Token {self.api_key}"}, progress_callback)

    async def _poll_job(self, client: httpx.AsyncClient, url, headers, progress_callback=None, timeout: int = 600):
        start = time.time()
        while time.time() - start < timeout:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            status = resp.json()

            if status.get("status") in ("succeeded", "SUCCEEDED"):
                output = status.get("output", {})
                video_url = output[0] if isinstance(output, list) else output.get("url", output.get("video"))
                return {"video_url": video_url, "duration": 5, "resolution": "1280x720", "cost": 0.05}
            elif status.get("status") in ("failed", "FAILED"):
                raise RuntimeError(f"Generation failed: {status.get('error')}")

            await asyncio.sleep(4)

        raise TimeoutError("Video generation timed out")
