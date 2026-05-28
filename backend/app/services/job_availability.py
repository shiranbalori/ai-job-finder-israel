"""Ensure jobs exist before CV matching."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.job import Job
from app.seed.seed_db import seed_jobs
from app.services.job_collector_service import JobCollectorService

logger = logging.getLogger(__name__)


def count_matchable_jobs(db: Session, *, israel_only: bool = True) -> int:
    q = db.query(Job).filter(Job.is_active == True)  # noqa: E712
    if israel_only:
        q = q.filter(Job.is_israel == True)  # noqa: E712
    return q.count()


async def ensure_jobs_for_matching(
    db: Session,
    *,
    min_jobs: int = 1,
    israel_only: bool = True,
) -> int:
    """
    Return count of active jobs suitable for matching.

    If none exist, run the job collector then seed demo jobs as a last resort.
    """
    count = count_matchable_jobs(db, israel_only=israel_only)
    if count >= min_jobs:
        logger.info("[jobs] matchable_jobs=%s (no refresh needed)", count)
        return count

    logger.warning("[jobs] matchable_jobs=%s — triggering automatic job refresh", count)
    try:
        result = await JobCollectorService(db).collect()
        count = count_matchable_jobs(db, israel_only=israel_only)
        logger.info(
            "[jobs] refresh complete fetched=%s created=%s matchable_jobs=%s",
            result.total_fetched,
            result.total_created,
            count,
        )
    except Exception:
        logger.exception("[jobs] automatic refresh failed")

    if count < min_jobs:
        logger.warning("[jobs] still no jobs — seeding demo jobs as fallback")
        seed_jobs(db)
        count = count_matchable_jobs(db, israel_only=israel_only)
        logger.info("[jobs] after demo seed matchable_jobs=%s", count)

    return count
