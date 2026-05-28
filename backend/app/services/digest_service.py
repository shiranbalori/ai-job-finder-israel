"""
Daily digest pipeline — fetch jobs, score matches, build & send email.
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.models.cv_profile import CVProfile
from app.models.email_log import EmailLog
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.saved_job import SavedJob
from app.models.user_settings import UserSettings
from app.utils.json_helpers import from_json_list, to_json_list

logger = logging.getLogger(__name__)


def _preferred_keywords(settings: UserSettings) -> list[str]:
    return [k.strip() for k in from_json_list(settings.preferred_job_keywords_json) if k.strip()]


def _match_keywords(match: JobMatch, keywords: list[str]) -> bool:
    if not keywords:
        return True
    job = match.job
    if not job:
        return True
    blob = f"{job.title} {job.description} {job.category}".lower()
    return any(kw.lower() in blob for kw in keywords)


async def refresh_jobs_for_digest(db: Session, *, timeout_sec: float = 45.0) -> dict[str, int]:
    """Fetch latest jobs from external boards (best-effort, time-bounded)."""
    import asyncio

    async def _do_refresh() -> dict[str, int]:
        from app.services.job_fetch_service import JobFetchService

        result = await JobFetchService(db).refresh(["greenhouse", "lever", "remoteok"])
        logger.info(
            "[digest] job refresh fetched=%s israel=%s created=%s updated=%s",
            result.total_fetched,
            result.total_israel,
            result.total_created,
            result.total_updated,
        )
        return {
            "fetched": result.total_fetched,
            "israel": result.total_israel,
            "created": result.total_created,
            "updated": result.total_updated,
        }

    try:
        return await asyncio.wait_for(_do_refresh(), timeout=timeout_sec)
    except asyncio.TimeoutError:
        logger.warning("[digest] job refresh timed out after %ss — using existing jobs", timeout_sec)
        return {"fetched": 0, "israel": 0, "created": 0, "updated": 0}
    except Exception:
        logger.exception("[digest] job refresh failed — continuing with existing jobs")
        return {"fetched": 0, "israel": 0, "created": 0, "updated": 0}


def _latest_cv(db: Session, *, real_only: bool = False, user_id: int | None = None) -> CVProfile | None:
    """Return latest CV for user (or global fallback for scheduler legacy)."""
    q = db.query(CVProfile)
    if user_id is not None:
        q = q.filter(CVProfile.user_id == user_id)
    if real_only:
        q = q.filter(CVProfile.is_demo == False)  # noqa: E712
        return q.order_by(CVProfile.created_at.desc()).first()
    cv = q.filter(CVProfile.is_demo == False).order_by(CVProfile.created_at.desc()).first()  # noqa: E712
    if cv:
        return cv
    return q.order_by(CVProfile.created_at.desc()).first()


def _merge_saved_job_matches(
    db: Session,
    cv: CVProfile,
    matches: list[JobMatch],
    *,
    user_id: int | None,
    real_jobs_only: bool,
    include_emailed: bool,
) -> list[JobMatch]:
    """Add bookmarked jobs to digest (saved jobs bypass min-score filter)."""
    q = db.query(SavedJob)
    if user_id is not None:
        q = q.filter(SavedJob.user_id == user_id)
    saved_rows = q.all()
    if not saved_rows:
        return matches

    by_job_id = {m.job_id: m for m in matches}
    for row in saved_rows:
        if row.job_id in by_job_id:
            continue
        q = (
            db.query(JobMatch)
            .options(joinedload(JobMatch.job))
            .filter(JobMatch.cv_profile_id == cv.id, JobMatch.job_id == row.job_id)
            .join(Job)
            .filter(Job.is_israel == True)  # noqa: E712
        )
        if real_jobs_only:
            q = q.filter(Job.is_demo == False)  # noqa: E712
        if not include_emailed:
            q = q.filter(JobMatch.emailed_at.is_(None))
        extra = q.first()
        if extra and extra.job:
            by_job_id[extra.job_id] = extra

    merged = list(by_job_id.values())
    merged.sort(key=lambda m: m.match_score, reverse=True)
    return merged


async def prepare_digest_matches(
    db: Session,
    settings: UserSettings,
    *,
    include_emailed: bool = False,
    recalculate: bool = True,
    refresh_jobs: bool = True,
) -> tuple[list[JobMatch], CVProfile | None]:
    """Refresh jobs, score CV, return qualifying matches for digest."""
    real_mode = not settings.demo_mode
    user_id = settings.user_id
    cv = _latest_cv(db, real_only=real_mode, user_id=user_id)
    if not cv:
        logger.warning("[digest] no CV profile — skipping match calculation")
        return [], None
    if real_mode and cv.is_demo:
        logger.warning("[digest] real mode but only demo CV available")
        return [], None

    if refresh_jobs and real_mode:
        await refresh_jobs_for_digest(db)

    emailed_before: dict[int, datetime] = {}
    if recalculate:
        for row in (
            db.query(JobMatch)
            .filter(
                JobMatch.cv_profile_id == cv.id,
                JobMatch.emailed_at.isnot(None),
            )
            .all()
        ):
            emailed_before[row.job_id] = row.emailed_at

        from app.services.job_matcher import match_cv_to_jobs

        jobs_q = db.query(Job).filter(Job.is_active == True, Job.is_israel == True)  # noqa: E712
        if real_mode:
            jobs_q = jobs_q.filter(Job.is_demo == False)  # noqa: E712
        jobs = jobs_q.order_by(Job.posted_at.desc()).limit(120).all()
        logger.info("[digest] scoring cv=%s against %s active jobs (real=%s)", cv.id, len(jobs), real_mode)
        await match_cv_to_jobs(db, cv, jobs, min_score=0, fast=True, quiet=True)

        if emailed_before:
            restored = 0
            for m in db.query(JobMatch).filter(JobMatch.cv_profile_id == cv.id).all():
                ts = emailed_before.get(m.job_id)
                if ts:
                    m.emailed_at = ts
                    restored += 1
            db.commit()
            logger.info("[digest] restored emailed_at on %s previously sent jobs", restored)

    q = (
        db.query(JobMatch)
        .options(joinedload(JobMatch.job))
        .filter(
            JobMatch.cv_profile_id == cv.id,
            JobMatch.match_score >= settings.min_match_score,
        )
        .join(Job)
        .filter(Job.is_israel == True)  # noqa: E712
    )
    if real_mode:
        q = q.filter(Job.is_demo == False)  # noqa: E712
    if not include_emailed:
        q = q.filter(JobMatch.emailed_at.is_(None))

    matches = q.order_by(JobMatch.match_score.desc()).limit(30).all()
    keywords = _preferred_keywords(settings)
    if keywords:
        matches = [m for m in matches if _match_keywords(m, keywords)]

    if settings.include_saved_jobs:
        matches = _merge_saved_job_matches(
            db,
            cv,
            matches,
            user_id=user_id,
            real_jobs_only=real_mode,
            include_emailed=include_emailed,
        )

    return matches[:10], cv


def _log_email(
    db: Session,
    *,
    recipient: str,
    subject: str,
    match_count: int,
    sent: bool,
    preview_only: bool,
    error: str | None,
    job_ids: list[int],
    user_id: int | None = None,
) -> EmailLog:
    row = EmailLog(
        user_id=user_id,
        recipient=recipient,
        subject=subject,
        match_count=match_count,
        sent=sent,
        preview_only=preview_only,
        error_message=error,
        job_ids_json=to_json_list([str(i) for i in job_ids]),
    )
    db.add(row)
    return row


def _israel_now() -> datetime:
    from zoneinfo import ZoneInfo

    return datetime.now(ZoneInfo("Asia/Jerusalem"))


def _already_sent_today(settings: UserSettings, now_il: datetime) -> bool:
    """True when this user already received a scheduled digest today (Israel date)."""
    last = settings.last_digest_sent_at
    if not last:
        return False
    from zoneinfo import ZoneInfo

    utc = ZoneInfo("UTC")
    if last.tzinfo is None:
        last_il = last.replace(tzinfo=utc).astimezone(ZoneInfo("Asia/Jerusalem"))
    else:
        last_il = last.astimezone(ZoneInfo("Asia/Jerusalem"))
    return last_il.date() == now_il.date()


def users_due_for_digest(db: Session, hour: int) -> list[UserSettings]:
    """Users with digest enabled at the given Israel local hour."""
    return (
        db.query(UserSettings)
        .filter(
            UserSettings.daily_digest_enabled == True,  # noqa: E712
            UserSettings.digest_hour == hour,
            UserSettings.user_id.isnot(None),
        )
        .all()
    )
