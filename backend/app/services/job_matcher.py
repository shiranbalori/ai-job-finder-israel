"""Match CV profiles to job listings and persist scores in SQLite."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass

from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.models.cv_profile import CVProfile
from app.models.job import Job
from app.models.job_match import JobMatch
from app.services.embedding_service import (
    EmbeddingService,
    batch_job_embeddings,
    cosine_similarity,
    ensure_cv_embedding,
)
from app.services.job_skills_cache import clear_job_skills_dirty, get_job_skills_cached
from app.services.job_skill_parser import build_job_scan_text
from app.services.matching_engine import _extract_cv_skills
from app.services.mock_ai import mock_match_job
from app.utils.json_helpers import from_json_list, to_json_list

logger = logging.getLogger(__name__)

DEFAULT_JOB_LIMIT = 50
MATCH_TIMEOUT_SEC = 20.0
UPLOAD_MATCH_TIMEOUT_SEC = 60.0


@dataclass
class MatchBatchResult:
    matches: list[JobMatch]
    partial: bool = False
    warning: str | None = None
    jobs_scored: int = 0
    jobs_total: int = 0
    elapsed_ms: int = 0


def _load_jobs_for_matching(
    db: Session,
    *,
    israel_only: bool,
    job_limit: int,
    jobs: list[Job] | None,
) -> list[Job]:
    if jobs is not None:
        return jobs[:job_limit]
    q = (
        db.query(Job)
        .filter(Job.is_active == True)  # noqa: E712
        .order_by(Job.is_demo.asc(), Job.posted_at.desc())
    )
    if israel_only:
        q = q.filter(Job.is_israel == True)  # noqa: E712
    return q.limit(job_limit).all()


def _build_cv_blob(cv: CVProfile) -> str:
    return " ".join(
        [
            cv.summary or "",
            " ".join(from_json_list(cv.skills_json)),
            " ".join(from_json_list(cv.job_titles_json)),
            (cv.raw_text or "")[:2000],
        ]
    ).lower()


def _embedding_similarity(
    cv_vec: list[float] | None,
    job_vec: list[float] | None,
) -> float | None:
    if not cv_vec or not job_vec or len(cv_vec) != len(job_vec):
        return None
    return cosine_similarity(cv_vec, job_vec)


async def match_cv_to_jobs(
    db: Session,
    cv: CVProfile,
    jobs: list[Job] | None = None,
    ai: object | None = None,  # unused — kept for API compatibility
    min_score: float = 0,
    *,
    israel_only: bool = True,
    job_limit: int = DEFAULT_JOB_LIMIT,
    quiet: bool = True,
    fast: bool = True,
    match_timeout_sec: float = MATCH_TIMEOUT_SEC,
    use_embeddings: bool | None = None,
) -> MatchBatchResult:
    """
    Score jobs against the CV and persist matches.

    Uses skill-graph scoring plus optional embedding similarity (OpenAI/Gemini/local).
    """
    batch_t0 = time.perf_counter()
    jobs = _load_jobs_for_matching(
        db, israel_only=israel_only, job_limit=job_limit, jobs=jobs
    )

    logger.info("[MATCH_START] jobs_count=%s cv_id=%s israel_only=%s", len(jobs), cv.id, israel_only)

    settings = get_settings()
    embed_enabled = (
        not fast
        and (settings.use_embeddings if use_embeddings is None else use_embeddings)
    )

    cv_skills = _extract_cv_skills(cv, fast=fast)
    cv_titles = from_json_list(cv.job_titles_json)
    cv_blob = _build_cv_blob(cv)

    cv_vec: list[float] | None = None
    job_embeddings: dict[int, list[float]] = {}
    embed_method = "disabled"

    if embed_enabled and jobs:
        try:
            embedder = EmbeddingService()
            cv_vec, embed_method = await ensure_cv_embedding(cv, embedder=embedder)
            db.commit()

            job_skill_pairs: list[tuple[Job, list[str] | None]] = []
            for job in jobs:
                skills, _ = get_job_skills_cached(db, job, quiet=True)
                job_skill_pairs.append((job, skills))
            job_embeddings = await batch_job_embeddings(job_skill_pairs, embedder=embedder)
            db.commit()
            logger.info(
                "[MATCH_EMBED] cv_method=%s jobs_embedded=%s provider=%s",
                embed_method,
                len(job_embeddings),
                embedder.provider,
            )
        except Exception:
            logger.exception("[MATCH_EMBED] failed — falling back to skill-only scoring")
            cv_vec = None
            job_embeddings = {}

    db.query(JobMatch).filter(JobMatch.cv_profile_id == cv.id).delete()

    pending: list[JobMatch] = []
    scored = 0
    partial = False
    warning: str | None = None

    for job in jobs:
        elapsed = time.perf_counter() - batch_t0
        if elapsed >= match_timeout_sec:
            partial = True
            warning = (
                f"Matching timed out after {int(match_timeout_sec)}s — "
                f"returning {len(pending)} matches from {scored} jobs scored."
            )
            logger.warning("[MATCH_TIMEOUT] scored=%s pending=%s ms=%s", scored, len(pending), int(elapsed * 1000))
            break

        if not job.is_active:
            continue

        job_t0 = time.perf_counter()
        logger.info("[JOB_SCORE_START] job_id=%s", job.id)

        job_skills, _job_debug = get_job_skills_cached(db, job, quiet=quiet)
        job_scan = build_job_scan_text(
            job.title,
            job.description,
            from_json_list(job.requirements_json),
            job_skills,
        )

        embed_sim = _embedding_similarity(cv_vec, job_embeddings.get(job.id))

        payload = mock_match_job(
            cv,
            job,
            cv_skills=cv_skills,
            job_skills=job_skills,
            cv_blob=cv_blob,
            cv_titles=cv_titles,
            job_scan=job_scan,
            embedding_similarity=embed_sim,
            quiet=True,
            fast=fast,
        )

        job_ms = int((time.perf_counter() - job_t0) * 1000)
        logger.info(
            "[JOB_SCORE_DONE] job_id=%s ms=%s score=%s embed=%s",
            job.id,
            job_ms,
            payload.get("match_score"),
            round(embed_sim or 0, 3),
        )
        scored += 1

        score = float(payload.get("match_score", 0))
        if score < min_score:
            continue

        pending.append(
            JobMatch(
                cv_profile_id=cv.id,
                job_id=job.id,
                match_score=score,
                match_reason=str(payload.get("match_reason", "")),
                missing_skills_json=to_json_list(payload.get("missing_skills", [])),
                matched_skills_json=to_json_list(payload.get("matched_skills", [])),
                semantic_matches_json=to_json_list(payload.get("semantic_matches", [])),
                score_breakdown_json=json.dumps(payload.get("score_breakdown") or {}),
                job_skills_debug_json="{}",
                semantic_overlap=float(payload.get("semantic_overlap", 0) or 0),
            )
        )

    if pending:
        db.add_all(pending)
    db.commit()
    clear_job_skills_dirty()

    matches = (
        db.query(JobMatch)
        .options(joinedload(JobMatch.job))
        .filter(JobMatch.cv_profile_id == cv.id)
        .order_by(JobMatch.match_score.desc())
        .all()
    )

    total_ms = int((time.perf_counter() - batch_t0) * 1000)
    top_score = max((m.match_score for m in matches), default=0.0)
    logger.info(
        "[MATCH_DONE] cv_profile_id=%s jobs_count=%s jobs_scored=%s matches_created=%s "
        "top_score=%s total_ms=%s partial=%s embed=%s",
        cv.id,
        len(jobs),
        scored,
        len(matches),
        top_score,
        total_ms,
        partial,
        embed_method,
    )

    return MatchBatchResult(
        matches=matches,
        partial=partial,
        warning=warning,
        jobs_scored=scored,
        jobs_total=len(jobs),
        elapsed_ms=total_ms,
    )
