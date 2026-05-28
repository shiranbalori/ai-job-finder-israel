"""Cache parsed job skills in memory + SQLite — never re-parse unchanged jobs."""

from __future__ import annotations

import hashlib
import logging

from sqlalchemy.orm import Session

from app.models.job import Job
from app.services.job_skill_parser import extract_job_skills
from app.utils.json_helpers import from_json_list, to_json_list

logger = logging.getLogger(__name__)

_mem: dict[int, tuple[str, list[str]]] = {}
_dirty_job_ids: set[int] = set()


def job_content_hash(job: Job) -> str:
    blob = f"{job.title}\0{job.description or ''}\0{job.requirements_json or '[]'}"
    return hashlib.sha256(blob.encode("utf-8", errors="ignore")).hexdigest()[:20]


def get_job_skills_cached(db: Session, job: Job, *, quiet: bool = True) -> tuple[list[str], dict]:
    """
    Return (skills, debug).

    Priority: RAM → SQLite parsed_skills_json → existing skills_json → full parse (once).
    """
    h = job_content_hash(job)
    cached = _mem.get(job.id)
    if cached and cached[0] == h:
        return cached[1], {}

    if job.skills_content_hash == h and job.parsed_skills_json:
        skills = from_json_list(job.parsed_skills_json)
        if skills:
            _mem[job.id] = (h, skills)
            if not quiet:
                logger.debug("[JOB_SKILLS_CACHE] hit=db job_id=%s skills=%s", job.id, len(skills))
            return skills, {}

    existing = from_json_list(job.skills_json)
    if len(existing) >= 2:
        _persist_job_skills(job, h, existing)
        _dirty_job_ids.add(job.id)
        _mem[job.id] = (h, existing)
        if not quiet:
            logger.debug("[JOB_SKILLS_CACHE] hit=skills_json job_id=%s", job.id)
        return existing, {}

    requirements = from_json_list(job.requirements_json)
    skills, debug = extract_job_skills(
        job.title,
        job.description,
        requirements=requirements,
        existing_skills=existing,
        limit=16,
        quiet=True,
    )
    _persist_job_skills(job, h, skills)
    _dirty_job_ids.add(job.id)
    _mem[job.id] = (h, skills)
    if not quiet:
        logger.info("[JOB_SKILLS_CACHE] miss=parse job_id=%s skills=%s", job.id, len(skills))
    return skills, debug


def _persist_job_skills(job: Job, content_hash: str, skills: list[str]) -> None:
    job.parsed_skills_json = to_json_list(skills)
    job.skills_content_hash = content_hash


def flush_job_skills_cache(db: Session) -> int:
    """Return count of jobs with pending skill cache writes (committed by caller)."""
    return len(_dirty_job_ids)


def clear_job_skills_dirty() -> None:
    _dirty_job_ids.clear()


def invalidate_job_skills_cache(job_id: int | None = None) -> None:
    if job_id is None:
        _mem.clear()
        _dirty_job_ids.clear()
    else:
        _mem.pop(job_id, None)
        _dirty_job_ids.discard(job_id)
