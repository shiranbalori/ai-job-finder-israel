"""
Job matching business logic — score CV against jobs and persist to SQLite.
"""

from sqlalchemy.orm import Session, joinedload

from app.models.cv_profile import CVProfile
from app.models.job import Job
from app.models.job_match import JobMatch
from app.services.job_matcher import DEFAULT_JOB_LIMIT, MatchBatchResult, match_cv_to_jobs
from app.services.mock_ai import mock_match_job


async def calculate_matches(
    db: Session,
    cv: CVProfile,
    *,
    min_score: float = 0,
    job_ids: list[int] | None = None,
    use_live_ai: bool = False,
    israel_only: bool = True,
    job_limit: int = DEFAULT_JOB_LIMIT,
    quiet: bool = True,
    fast: bool = True,
    use_embeddings: bool | None = None,
    match_timeout_sec: float | None = None,
) -> MatchBatchResult:
    """Calculate match scores for active jobs and save to job_matches table."""
    jobs: list[Job] | None = None
    if job_ids:
        q = db.query(Job).filter(Job.is_active == True, Job.id.in_(job_ids))  # noqa: E712
        if israel_only:
            q = q.filter(Job.is_israel == True)  # noqa: E712
        jobs = q.order_by(Job.is_demo.asc(), Job.posted_at.desc()).limit(job_limit).all()

    embed = use_embeddings if use_embeddings is not None else not fast

    kwargs: dict = {
        "jobs": jobs,
        "min_score": min_score,
        "israel_only": israel_only,
        "job_limit": job_limit,
        "quiet": quiet,
        "fast": fast and not use_live_ai,
        "use_embeddings": embed,
    }
    if match_timeout_sec is not None:
        kwargs["match_timeout_sec"] = match_timeout_sec

    return await match_cv_to_jobs(db, cv, **kwargs)


def preview_single_match(cv: CVProfile, job: Job) -> dict:
    """Score one job without saving — useful for debugging in /docs."""
    return mock_match_job(cv, job, quiet=False, fast=False)


def list_saved_matches(
    db: Session,
    cv_profile_id: int | None = None,
    min_score: float = 0,
    limit: int = 50,
    israel_only: bool = True,
    sort_by: str = "score",
) -> list[JobMatch]:
    q = (
        db.query(JobMatch)
        .options(joinedload(JobMatch.job))
        .filter(JobMatch.match_score >= min_score)
    )
    joined_job = False
    if israel_only:
        q = q.join(Job).filter(Job.is_israel == True)  # noqa: E712
        joined_job = True
    if cv_profile_id:
        q = q.filter(JobMatch.cv_profile_id == cv_profile_id)

    if sort_by == "newest":
        if not joined_job:
            q = q.join(Job)
        q = q.order_by(Job.posted_at.desc())
    elif sort_by == "semantic":
        q = q.order_by(JobMatch.semantic_overlap.desc(), JobMatch.match_score.desc())
    else:
        q = q.order_by(JobMatch.match_score.desc())

    return q.limit(limit).all()
