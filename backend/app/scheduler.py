"""Background scheduler — job refresh + per-user daily digest (Israel local time)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.database import SessionLocal
from app.services.digest_service import (
    _already_sent_today,
    _israel_now,
    refresh_jobs_for_digest,
    users_due_for_digest,
)
from app.services.email_service import send_digest_email
from app.services.job_collector_service import JobCollectorService
from app.services.scheduler_log_service import log_scheduler_run, log_scheduler_skip

logger = logging.getLogger(__name__)
ISRAEL_TZ = ZoneInfo("Asia/Jerusalem")
scheduler = BackgroundScheduler(timezone=ISRAEL_TZ)


def _run_job_refresh() -> None:
    """Periodic fetch from Greenhouse, Lever, and RemoteOK."""
    env = get_settings()
    if not env.job_refresh_enabled:
        logger.info("[scheduler] job refresh skipped — JOB_REFRESH_ENABLED=false")
        return

    db = SessionLocal()
    try:
        logger.info("[scheduler] starting periodic job refresh")
        result = asyncio.run(JobCollectorService(db).collect())
        logger.info(
            "[scheduler] job collect done: fetched=%s matched=%s tagged=%s created=%s updated=%s ms=%s",
            result.total_fetched,
            result.total_israel,
            result.total_tagged,
            result.total_created,
            result.total_updated,
            result.duration_ms,
        )
    except Exception:
        logger.exception("[scheduler] job refresh failed")
    finally:
        db.close()


async def _send_user_digest(db, settings) -> dict:
    """Send scheduled digest for one user with scheduler audit logging."""
    with log_scheduler_run(
        db,
        user_id=settings.user_id,
        recipient=settings.email,
    ) as ctx:
        result = await send_digest_email(
            db,
            settings,
            force=False,
            refresh_jobs=False,
        )
        ctx["result"] = result
    return result


def _run_daily_digest() -> None:
    """
    Hourly check (Israel time): send digest to each user whose digest_hour matches
    and who has not already received today's email.
    """
    env = get_settings()
    db = SessionLocal()
    try:
        if not env.daily_email_enabled:
            log_scheduler_skip(db, "DAILY_EMAIL_ENABLED=false in .env")
            return

        now_il = _israel_now()
        hour = now_il.hour
        candidates = users_due_for_digest(db, hour)
        due = [s for s in candidates if not _already_sent_today(s, now_il)]

        if not due:
            logger.debug("[scheduler] no users due for digest at %s:00 Israel", hour)
            return

        logger.info(
            "[scheduler] daily digest hour=%s Israel — %s user(s) due",
            hour,
            len(due),
        )

        # Refresh live jobs once per hour before scoring all due users.
        asyncio.run(refresh_jobs_for_digest(db, timeout_sec=60.0))

        sent = preview = failed = skipped = 0
        for settings in due:
            if not settings.email or "@" not in settings.email:
                log_scheduler_skip(
                    db,
                    f"Invalid email for user_id={settings.user_id}",
                    user_id=settings.user_id,
                )
                skipped += 1
                continue

            try:
                result = asyncio.run(_send_user_digest(db, settings))
                status = result.get("message", "")
                if result.get("sent"):
                    sent += 1
                elif status.startswith("Failed"):
                    failed += 1
                elif result.get("preview_only"):
                    preview += 1
                else:
                    skipped += 1
            except Exception:
                logger.exception(
                    "[scheduler] digest failed user_id=%s email=%s",
                    settings.user_id,
                    settings.email,
                )
                failed += 1

        logger.info(
            "[scheduler] digest batch hour=%s done sent=%s preview=%s failed=%s skipped=%s",
            hour,
            sent,
            preview,
            failed,
            skipped,
        )
    except Exception:
        logger.exception("[scheduler] daily digest batch failed")
    finally:
        db.close()


def start_scheduler() -> None:
    if scheduler.running:
        return

    env = get_settings()

    if env.job_refresh_enabled:
        interval = max(1, env.job_refresh_interval_hours)
        scheduler.add_job(
            _run_job_refresh,
            trigger=IntervalTrigger(hours=interval),
            id="job_refresh",
            replace_existing=True,
            misfire_grace_time=3600,
            next_run_time=None,
        )
        logger.info("[scheduler] job refresh every %s hours", interval)

    # Check every hour; each user's digest_hour setting controls when they receive mail.
    trigger = CronTrigger(minute=0, timezone=ISRAEL_TZ)
    scheduler.add_job(
        _run_daily_digest,
        trigger=trigger,
        id="daily_digest",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info("[scheduler] started — per-user daily digest checked hourly (Asia/Jerusalem)")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[scheduler] stopped")


def reschedule_digest(hour: int | None = None) -> None:
    """User digest_hour is read at send time; hourly cron covers all hours."""
    if hour is not None:
        logger.info(
            "[scheduler] user digest_hour=%s saved — next send when hourly job matches",
            hour,
        )
