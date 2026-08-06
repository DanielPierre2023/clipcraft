# backend/app/routers/sse.py
import asyncio
import json
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
import redis.asyncio as aioredis
import os

router = APIRouter(prefix="/api/v1/jobs", tags=["Realtime"])
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

@router.get("/{job_id}/stream")
async def stream_job_progress(job_id: str, request: Request):
    """Server-Sent Events endpoint streaming progress to client without polling."""
    
    async def event_generator():
        r = aioredis.from_url(REDIS_URL)
        pubsub = r.pubsub()
        await pubsub.subscribe(f"job_updates:{job_id}")

        try:
            while True:
                if await request.is_disconnected():
                    break

                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    data = message["data"].decode("utf-8")
                    yield {"event": "update", "data": data}
                    
                    parsed = json.loads(data)
                    if parsed.get("progress") == 100 or parsed.get("stage") == "failed":
                        break

                await asyncio.sleep(0.2)
        finally:
            await pubsub.unsubscribe(f"job_updates:{job_id}")
            await r.close()

    return EventSourceResponse(event_generator())
