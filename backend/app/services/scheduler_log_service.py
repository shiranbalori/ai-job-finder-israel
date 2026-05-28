"""Persist scheduler run outcomes for the Settings audit panel."""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Iterator

from sqlalchemy.orm import Session

from app.models.scheduler_log import SchedulerLog

logger = logging.getLogger(__name__)


def _resolve_scheduler_status(result: dict[str, Any]) -> str:
    """Map digest result to success | failed | preview | skipped."""
    if result.get("sent"):
        return "success"
    message = str(result.get("message", ""))
    if message.startswith("Failed") or result.get("error"):
        return "failed"
    if result.get("preview_only"):
        return "preview"
    if int(result.get("count", 0)) == 0:
        return "skipped"
    return "preview"


@contextmanager
def log_scheduler_run(
    db: Session,
    job_name: str = "daily_digest",
    *,
    user_id: int | None = None,
    recipient: str | None = None,
) -> Iterator[dict[str, Any]]:
    """Record scheduler start/finish in DB and Python logs."""
    started = time.perf_counter()
    ctx: dict[str, Any] = {"row": None, "job_name": job_name}
    start_msg = f"Digest started for {recipient}" if recipient else "Digest job started"
    row = SchedulerLog(
        job_name=job_name,
        user_id=user_id,
        status="started",
        message=start_msg[:500],
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    ctx["row"] = row
    logger.info(
        "[scheduler] %s started user_id=%s (log_id=%s)",
        job_name,
        user_id,
        row.id,
    )

    try:
        yield ctx
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        row.status = "failed"
        row.message = str(exc)[:500]
        row.duration_ms = duration_ms
        db.commit()
        logger.exception(
            "[scheduler] %s failed user_id=%s after %sms",
            job_name,
            user_id,
            duration_ms,
        )
        raise
    else:
        result = ctx.get("result") or {}
        duration_ms = int((time.perf_counter() - started) * 1000)
        row.status = _resolve_scheduler_status(result)
        row.message = str(result.get("message", "Complete"))[:500]
        row.match_count = int(result.get("count", 0))
        row.sent = bool(result.get("sent"))
        row.preview_only = bool(result.get("preview_only", False))
        row.duration_ms = duration_ms
        db.commit()
        logger.info(
            "[scheduler] %s finished user_id=%s status=%s sent=%s count=%s duration=%sms",
            job_name,
            user_id,
            row.status,
            row.sent,
            row.match_count,
            duration_ms,
        )


def log_scheduler_skip(
    db: Session,
    message: str,
    *,
    job_name: str = "daily_digest",
    user_id: int | None = None,
) -> None:
    row = SchedulerLog(
        job_name=job_name,
        user_id=user_id,
        status="skipped",
        message=message[:500],
    )
    db.add(row)
    db.commit()
    logger.info(
        "[scheduler] %s skipped user_id=%s — %s",
        job_name,
        user_id,
        message,
    )
