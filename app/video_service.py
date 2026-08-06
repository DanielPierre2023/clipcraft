"""Video service integrating Runway ML and Replicate APIs."""
import asyncio
import httpx
import time
import uuid
from pathlib import Path
from typing import Optional, Callable, Dict


class VideoService:

    def __init__(self, provider: str = "runway", api_key: str = "", cache_dir: str = "./cache/videos"):
        self.provider = provider
        self.api_key = api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.demo_mode = not api_key

    async def generate(self, prompt: str, duration_sec: int = 5,
                       resolution: str = "1280x720", style: str = "cinematic",
                       progress_callback: Optional[Callable] = None) -> Dict:
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

        for pct in range(20, 90, 20):
            await asyncio.sleep(0.3)
            if progress_callback:
                progress_callback(pct, "generating", f"Demo rendering frame {pct}%")

        video_id = uuid.uuid4().hex[:8]
        svg_filename = f"demo_{video_id}.svg"
        svg_path = self.cache_dir / svg_filename

        prompt_hash = hash(prompt) & 0xFFFFFF
        color1 = f"#{(prompt_hash & 0xFFFFFF):06x}"
        color2 = f"#{((prompt_hash >> 4) & 0xFFFFFF):06x}"
        display_prompt = prompt[:60] + "..." if len(prompt) > 60 else prompt

        svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">
            <rect width="{width}" height="{height}" fill="#0f0f23"/>
            <circle cx="{width*0.5}" cy="{height*0.4}" r="80" fill="{color1}" opacity="0.4"/>
            <text x="{width/2}" y="{height*0.4}" text-anchor="middle" fill="white" font-size="24">ClipCraft Demo</text>
            <text x="{width/2}" y="{height*0.55}" text-anchor="middle" fill="#a78bfa" font-size="16">{display_prompt}</text>
        </svg>'''

        svg_path.write_text(svg_content)

        if progress_callback:
            progress_callback(100, "completed", "Demo video ready")

        return {
            "video_url": f"/cache/videos/{svg_filename}",
            "video_path": str(svg_path),
            "duration": duration_sec,
            "resolution": resolution,
            "cost": 0.0,
            "demo": True,
        }

    async def _generate_replicate(self, client: httpx.AsyncClient, prompt, duration_sec, resolution, style, progress_callback=None):
        if progress_callback:
            progress_callback(10, "submitting", "Sending to Replicate API")

        # Stable Video Diffusion model standard API payload
        width, height = map(int, resolution.split("x"))
        response = await client.post(
            "https://api.replicate.com/v1/models/stability-ai/stable-video-diffusion/predictions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "input": {
                    "cond_augmented_prompt": f"{style}: {prompt}",
                    "video_length": f"{duration_sec}s",
                    "width": width,
                    "height": height
                }
            }
        )
        response.raise_for_status()
        prediction = response.json()
        poll_url = prediction["urls"]["get"]

        return await self._poll_replicate_job(client, poll_url, progress_callback)

    async def _poll_replicate_job(self, client: httpx.AsyncClient, poll_url: str, progress_callback=None, timeout: int = 600):
        start = time.time()
        headers = {"Authorization": f"Bearer {self.api_key}"}

        while time.time() - start < timeout:
            resp = await client.get(poll_url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")

            if status == "succeeded":
                output = data.get("output")
                # Handle Replicate list vs string output formats
                video_url = output[0] if isinstance(output, list) else output
                return {
                    "video_url": video_url,
                    "duration": 5,
                    "resolution": "1280x720",
                    "cost": 0.05,
                }
            elif status == "failed":
                raise RuntimeError(f"Replicate generation failed: {data.get('error')}")

            if progress_callback:
                progress_callback(50, "generating", "Rendering video frames")

            await asyncio.sleep(4)

        raise TimeoutError("Replicate generation timed out")

    async def _generate_runway(self, client: httpx.AsyncClient, prompt, duration_sec, resolution, style, progress_callback=None):
        if progress_callback:
            progress_callback(10, "submitting", "Sending to Runway ML API")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Runway-Version": "2024-11-06",
            "Content-Type": "application/json",
        }
        response = await client.post(
            "https://api.dev.runwayml.com/v1/tasks",
            headers=headers,
            json={
                "taskType": "gen3a_turbo",
                "promptText": f"{style}: {prompt}",
                "duration": duration_sec,
                "ratio": "16:9"
            }
        )
        response.raise_for_status()
        task_id = response.json()["id"]

        return await self._poll_runway_job(client, task_id, headers, progress_callback)

    async def _poll_runway_job(self, client: httpx.AsyncClient, task_id: str, headers: Dict, progress_callback=None, timeout: int = 600):
        start = time.time()
        url = f"https://api.dev.runwayml.com/v1/tasks/{task_id}"

        while time.time() - start < timeout:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")

            if status == "SUCCEEDED":
                output = data.get("output", [])
                video_url = output[0] if isinstance(output, list) and output else None
                return {
                    "video_url": video_url,
                    "duration": 5,
                    "resolution": "1280x720",
                    "cost": 0.08,
                }
            elif status == "FAILED":
                raise RuntimeError(f"Runway task failed: {data.get('failure')}")

            progress = int(data.get("progress", 0.5) * 100)
            if progress_callback:
                progress_callback(progress, "generating", "Rendering video frames")

            await asyncio.sleep(4)

        raise TimeoutError("Runway generation timed out")
