"""
Text embeddings for CV ↔ job semantic matching.

Uses OpenAI or Gemini embedding APIs when configured; otherwise falls back to
local feature-hashing vectors (no extra dependencies).
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from typing import Any

import httpx

from app.config import get_settings
from app.models.cv_profile import CVProfile
from app.models.job import Job
from app.utils.json_helpers import from_json_list

logger = logging.getLogger(__name__)

LOCAL_DIM = 384
MAX_EMBED_CHARS = 8000
OPENAI_EMBED_MODEL = "text-embedding-3-small"
GEMINI_EMBED_MODEL = "text-embedding-004"


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9+#]{2,}", (text or "").lower())


def local_embed(text: str, dim: int = LOCAL_DIM) -> list[float]:
    """Deterministic bag-of-words embedding via feature hashing."""
    tokens = _tokenize(text[:MAX_EMBED_CHARS])
    vec = [0.0] * dim
    for i, token in enumerate(tokens):
        h = int(hashlib.md5(token.encode()).hexdigest(), 16) % dim
        vec[h] += 1.0
        if i > 0:
            bigram = f"{tokens[i - 1]}_{token}"
            hb = int(hashlib.md5(bigram.encode()).hexdigest(), 16) % dim
            vec[hb] += 0.5
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def vector_to_json(vec: list[float]) -> str:
    return json.dumps([round(v, 6) for v in vec])


def vector_from_json(raw: str | None) -> list[float] | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if isinstance(data, list) and data:
            return [float(x) for x in data]
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return None


def build_cv_match_text(cv: CVProfile) -> str:
    parts = [
        cv.summary or "",
        " ".join(from_json_list(cv.skills_json)),
        " ".join(from_json_list(cv.tools_json)),
        " ".join(from_json_list(cv.technologies_json)),
        " ".join(from_json_list(cv.job_titles_json)),
        f"{cv.years_experience or 0} years experience",
        (cv.raw_text or "")[:6000],
    ]
    return "\n".join(p for p in parts if p).strip()


def build_job_match_text(job: Job, job_skills: list[str] | None = None) -> str:
    skills = job_skills or from_json_list(job.skills_json) or from_json_list(job.parsed_skills_json)
    parts = [
        job.title,
        job.company,
        job.category or "",
        job.description or "",
        " ".join(from_json_list(job.requirements_json)),
        " ".join(skills),
    ]
    return "\n".join(p for p in parts if p).strip()


def content_hash(text: str) -> str:
    return hashlib.md5(text[:MAX_EMBED_CHARS].encode()).hexdigest()


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def provider(self) -> str:
        p = self.settings.ai_provider.lower()
        if p == "openai" and self._openai_ready():
            return "openai"
        if p == "gemini" and self._gemini_ready():
            return "gemini"
        if self._openai_ready():
            return "openai"
        if self._gemini_ready():
            return "gemini"
        return "local"

    def _openai_ready(self) -> bool:
        key = self.settings.openai_api_key
        return bool(key and key != "your-openai-key-here")

    def _gemini_ready(self) -> bool:
        key = self.settings.gemini_api_key
        return bool(key and key != "your-gemini-key-here")

    async def embed_text(self, text: str) -> tuple[list[float], str]:
        """Return (vector, method)."""
        clean = (text or "").strip()
        if not clean:
            return local_embed(""), "local_hash"

        provider = self.provider
        if provider == "openai":
            vec = await self._openai_embed(clean)
            if vec:
                return vec, "openai_embedding"
        elif provider == "gemini":
            vec = await self._gemini_embed(clean)
            if vec:
                return vec, "gemini_embedding"

        return local_embed(clean), "local_hash"

    async def embed_batch(self, texts: list[str]) -> list[tuple[list[float], str]]:
        clean = [(t or "").strip() for t in texts]
        if not clean:
            return []

        provider = self.provider
        if provider == "openai":
            vecs = await self._openai_embed_batch(clean)
            if vecs and len(vecs) == len(clean):
                return [(v, "openai_embedding") for v in vecs]

        if provider == "gemini":
            # Gemini batch is sequential — acceptable for small job batches
            out: list[tuple[list[float], str]] = []
            for text in clean:
                vec = await self._gemini_embed(text) if text else None
                out.append((vec or local_embed(text), "gemini_embedding" if vec else "local_hash"))
            return out

        return [(local_embed(t), "local_hash") for t in clean]

    async def _openai_embed(self, text: str) -> list[float] | None:
        batch = await self._openai_embed_batch([text])
        return batch[0] if batch else None

    async def _openai_embed_batch(self, texts: list[str]) -> list[list[float]] | None:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                    json={
                        "model": self.settings.openai_embedding_model or OPENAI_EMBED_MODEL,
                        "input": [t[:MAX_EMBED_CHARS] for t in texts],
                    },
                )
                resp.raise_for_status()
                data = resp.json()["data"]
                ordered = sorted(data, key=lambda x: x["index"])
                return [item["embedding"] for item in ordered]
        except Exception as exc:
            logger.warning("[embed] OpenAI batch failed: %s", exc)
            return None

    async def _gemini_embed(self, text: str) -> list[float] | None:
        model = self.settings.gemini_embedding_model or GEMINI_EMBED_MODEL
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:embedContent?key={self.settings.gemini_api_key}"
        )
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(
                    url,
                    json={"content": {"parts": [{"text": text[:MAX_EMBED_CHARS]}]}},
                )
                resp.raise_for_status()
                values = resp.json()["embedding"]["values"]
                return [float(v) for v in values]
        except Exception as exc:
            logger.warning("[embed] Gemini failed: %s", exc)
            return None


async def ensure_cv_embedding(
    cv: CVProfile,
    *,
    embedder: EmbeddingService | None = None,
) -> tuple[list[float], str]:
    """Load cached CV embedding or compute and return."""
    text = build_cv_match_text(cv)
    h = content_hash(text)
    cached = vector_from_json(getattr(cv, "embedding_json", None))
    cached_hash = getattr(cv, "embedding_hash", None)
    if cached and cached_hash == h:
        return cached, getattr(cv, "embedding_method", None) or "cached"

    service = embedder or EmbeddingService()
    vec, method = await service.embed_text(text)
    cv.embedding_json = vector_to_json(vec)
    cv.embedding_hash = h
    cv.embedding_method = method
    return vec, method


async def ensure_job_embedding(
    job: Job,
    job_skills: list[str] | None = None,
    *,
    embedder: EmbeddingService | None = None,
) -> tuple[list[float], str]:
    text = build_job_match_text(job, job_skills)
    h = content_hash(text)
    cached = vector_from_json(getattr(job, "embedding_json", None))
    cached_hash = getattr(job, "embedding_hash", None)
    if cached and cached_hash == h:
        return cached, getattr(job, "embedding_method", None) or "cached"

    service = embedder or EmbeddingService()
    vec, method = await service.embed_text(text)
    job.embedding_json = vector_to_json(vec)
    job.embedding_hash = h
    job.embedding_method = method
    return vec, method


async def batch_job_embeddings(
    jobs: list[tuple[Job, list[str] | None]],
    *,
    embedder: EmbeddingService | None = None,
) -> dict[int, list[float]]:
    """
    Return job_id → vector, using DB cache where valid.
    Uncached jobs are embedded in one batch when possible.
    """
    service = embedder or EmbeddingService()
    result: dict[int, list[float]] = {}
    pending: list[tuple[int, Job, str, str]] = []

    for job, skills in jobs:
        text = build_job_match_text(job, skills)
        h = content_hash(text)
        cached = vector_from_json(getattr(job, "embedding_json", None))
        if cached and getattr(job, "embedding_hash", None) == h:
            result[job.id] = cached
            continue
        pending.append((job.id, job, text, h))

    if pending:
        texts = [p[2] for p in pending]
        embedded = await service.embed_batch(texts)
        for (job_id, job, _text, h), (vec, method) in zip(pending, embedded):
            job.embedding_json = vector_to_json(vec)
            job.embedding_hash = h
            job.embedding_method = method
            result[job_id] = vec

    return result
