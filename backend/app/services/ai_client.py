"""
AI client abstraction — supports OpenAI, Gemini, or mock mode.

When API keys are missing or AI_PROVIDER=mock, returns None and callers
fall back to deterministic heuristics (demo-ready without real APIs).
"""

import json
import re
from typing import Any

import httpx

from app.config import get_settings


class AIClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.provider = self.settings.ai_provider.lower()

    @property
    def is_live(self) -> bool:
        return self.provider in {"openai", "gemini"} and self._has_credentials()

    def _has_credentials(self) -> bool:
        if self.provider == "openai":
            return bool(self.settings.openai_api_key and self.settings.openai_api_key != "your-openai-key-here")
        if self.provider == "gemini":
            return bool(self.settings.gemini_api_key and self.settings.gemini_api_key != "your-gemini-key-here")
        return False

    async def extract_cv_profile(self, cv_text: str) -> dict[str, Any] | None:
        if not self.is_live:
            return None
        prompt = (
            "Extract from this CV as JSON with keys: full_name, email, summary, "
            "years_experience (int), job_titles (array), skills (array), tools (array), "
            "technologies (array), language (en or he). CV:\n\n"
            f"{cv_text[:8000]}"
        )
        raw = await self._complete(prompt)
        return self._parse_json(raw) if raw else None

    async def match_job(self, cv: dict, job: dict) -> dict[str, Any] | None:
        if not self.is_live:
            return None
        prompt = (
            "Score job fit 0-100. Return JSON: match_score (number), match_reason (string), "
            "missing_skills (array), matched_skills (array).\n\n"
            f"CV: {json.dumps(cv, ensure_ascii=False)}\n\n"
            f"Job: {json.dumps(job, ensure_ascii=False)}"
        )
        raw = await self._complete(prompt)
        return self._parse_json(raw) if raw else None

    async def _complete(self, prompt: str) -> str | None:
        try:
            if self.provider == "openai":
                return await self._openai_complete(prompt)
            if self.provider == "gemini":
                return await self._gemini_complete(prompt)
        except Exception:
            return None
        return None

    async def _openai_complete(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                json={
                    "model": self.settings.openai_model,
                    "messages": [
                        {"role": "system", "content": "You are a career AI assistant. Reply with valid JSON only."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _gemini_complete(self, prompt: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.gemini_model}:generateContent"
            f"?key={self.settings.gemini_api_key}"
        )
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            resp.raise_for_status()
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any] | None:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    return None
        return None
