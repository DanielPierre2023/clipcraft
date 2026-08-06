# backend/app/services/prompt_expander.py
import os
import httpx
from typing import Optional

class PromptExpander:
    """Uses LLM models to enrich raw prompts with camera directions, aesthetics, and lighting."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    async def expand_prompt(self, raw_prompt: str, style: str = "cinematic") -> str:
        if not self.api_key:
            return raw_prompt  # Fallback if no LLM key configured

        system_instruction = (
            "You are an expert Hollywood cinematographer and AI video prompt engineer. "
            "Expand the user's basic prompt into a vivid, visually compelling AI video generation prompt. "
            "Specify lighting, camera motion, atmosphere, visual textures, and depth of field. "
            "Keep the output concise, under 75 words. Do not wrap in quotes or add conversational preamble."
        )

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Style: {style}. Prompt: {raw_prompt}"}
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    self.endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            except Exception:
                return raw_prompt
