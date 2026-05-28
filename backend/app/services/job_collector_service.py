"""
Production job collector — fetch, normalize, tag, filter, dedupe, persist.

Sources: Greenhouse, Lever, RemoteOK (AI/Data roles)
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Callable

from sqlalchemy.orm import Session

from app.adapters.greenhouse import GreenhouseAdapter
from app.adapters.lever import LeverAdapter
from app.adapters.remoteok import RemoteOKAdapter
from app.config import get_settings
from app.domain.job_dto import FetchedJobDTO
from app.models.job_collector_log import JobCollectorLog
from app.repositories.job_repository import JobRepository
from app.services.job_filter import JobFilterStats, filter_board_jobs, filter_fetched_jobs, filter_remoteok_jobs
from app.services.job_normalizer import normalize_collected_job
from app.services.job_tag_extractor import CANONICAL_TAGS

logger = logging.getLogger(__name__)

DEFAULT_SOURCES = ["greenhouse", "lever", "remoteok"]

ADAPTER_REGISTRY: dict[str, type] = {
    "greenhouse": GreenhouseAdapter,
    "lever": LeverAdapter,
    "remoteok": RemoteOKAdapter,
}

FILTER_BY_SOURCE: dict[str, Callable[[list], tuple[list, JobFilterStats]]] = {
    "greenhouse": filter_board_jobs,
    "lever": filter_board_jobs,
    "remoteok": filter_remoteok_jobs,
}


@dataclass
class SourceCollectStats:
    name: str
    boards: list[str]
    fetched: int = 0
    matched: int = 0
    israel: int = 0
    excluded: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    tagged: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class CollectorResult:
    total_fetched: int
    total_israel: int
    total_excluded: int
    total_created: int
    total_updated: int
    total_skipped: int
    total_tagged: int
    sources: list[SourceCollectStats]
    duration_ms: int = 0
    success: bool = True
    partial: bool = False
    errors: list[str] = field(default_factory=list)
    log_id: int | None = None

    @property
    def total_matched(self) -> int:
        return self.total_israel


class JobCollectorService:
    """Collect real AI/Data jobs from public boards into the unified DB schema."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = JobRepository(db)
        self.settings = get_settings()

    async def collect(self, sources: list[str] | None = None) -> CollectorResult:
        """
        Full pipeline:
        1. Fetch from Greenhouse / Lever / RemoteOK
        2. Normalize + extract AI/Data tags
        3. Filter for AI/Data + Israel (or Israeli companies on RemoteOK)
        4. Dedupe by (source, external_id) and URL
        5. Upsert into database
        """
        started = time.perf_counter()
        enabled = self._resolve_sources(sources)
        log_row = self._start_log(enabled)

        source_stats: list[SourceCollectStats] = []
        totals = dict(fetched=0, israel=0, excluded=0, created=0, updated=0, skipped=0, tagged=0)
        all_errors: list[str] = []
        seen_urls: set[str] = set()
        seen_keys: set[tuple[str, str]] = set()

        logger.info("[collector] start sources=%s tags=%s", enabled, CANONICAL_TAGS)

        for source_name in enabled:
            stats = await self._collect_source(
                source_name,
                seen_urls=seen_urls,
                seen_keys=seen_keys,
            )
            source_stats.append(stats)
            totals["fetched"] += stats.fetched
            totals["israel"] += stats.israel
            totals["excluded"] += stats.excluded
            totals["created"] += stats.created
            totals["updated"] += stats.updated
            totals["skipped"] += stats.skipped
            totals["tagged"] += stats.tagged
            all_errors.extend(stats.errors)

        try:
            self.repo.deactivate_non_israel_fetched()
        except Exception as exc:
            msg = f"deactivate_non_israel: {exc}"
            logger.error("[collector] %s", msg)
            all_errors.append(msg)

        duration_ms = int((time.perf_counter() - started) * 1000)
        partial = bool(all_errors) and totals["created"] + totals["updated"] > 0
        success = totals["created"] + totals["updated"] > 0 or (totals["fetched"] > 0 and not all_errors)
        failed = not success and bool(all_errors)

        status = "failed" if failed else ("partial" if partial else "success")
        message = (
            f"Collected {totals['fetched']} jobs — {totals['israel']} matched, "
            f"{totals['excluded']} excluded, {totals['created']} new, "
            f"{totals['updated']} updated, {totals['tagged']} tagged ({duration_ms}ms)."
        )

        self._finish_log(
            log_row,
            status=status,
            totals=totals,
            errors=all_errors,
            duration_ms=duration_ms,
            message=message,
        )

        logger.info("[collector] done status=%s %s", status, message)

        return CollectorResult(
            total_fetched=totals["fetched"],
            total_israel=totals["israel"],
            total_excluded=totals["excluded"],
            total_created=totals["created"],
            total_updated=totals["updated"],
            total_skipped=totals["skipped"],
            total_tagged=totals["tagged"],
            sources=source_stats,
            duration_ms=duration_ms,
            success=not failed,
            partial=partial,
            errors=all_errors,
            log_id=log_row.id if log_row else None,
        )

    def _resolve_sources(self, sources: list[str] | None) -> list[str]:
        enabled = [s.lower() for s in (sources or DEFAULT_SOURCES) if s.lower() in ADAPTER_REGISTRY]
        return enabled or list(DEFAULT_SOURCES)

    async def _collect_source(
        self,
        source_name: str,
        *,
        seen_urls: set[str],
        seen_keys: set[tuple[str, str]],
    ) -> SourceCollectStats:
        adapter_cls = ADAPTER_REGISTRY[source_name]
        adapter = adapter_cls()
        stats = SourceCollectStats(name=adapter.name, boards=adapter.board_identifiers())
        timeout = self.settings.job_collector_timeout_sec

        try:
            if hasattr(adapter, "fetch_jobs_safe"):
                raw_jobs, errors = await asyncio.wait_for(
                    adapter.fetch_jobs_safe(),  # type: ignore[attr-defined]
                    timeout=timeout,
                )
                stats.errors = errors
            else:
                raw_jobs = await asyncio.wait_for(adapter.fetch_jobs(), timeout=timeout)
        except asyncio.TimeoutError:
            msg = f"{source_name}: timed out after {timeout}s"
            stats.errors.append(msg)
            logger.error("[collector] %s", msg)
            return stats
        except Exception as exc:
            msg = f"{source_name}: {exc}"
            stats.errors.append(msg)
            logger.exception("[collector] source failed: %s", source_name)
            return stats

        stats.fetched = len(raw_jobs)
        logger.info("[collector] %s fetched=%s boards=%s", source_name, stats.fetched, stats.boards)

        normalized = [normalize_collected_job(j) for j in raw_jobs]

        filter_fn = FILTER_BY_SOURCE.get(source_name, filter_fetched_jobs)
        matched, filter_stats = filter_fn(normalized)
        stats.matched = len(matched)
        stats.israel = filter_stats.total_israel
        stats.excluded = filter_stats.total_excluded

        logger.info(
            "[collector] %s matched=%s excluded=%s role_excluded=%s location_excluded=%s",
            source_name,
            stats.matched,
            stats.excluded,
            filter_stats.role_excluded,
            filter_stats.location_excluded,
        )

        for dto in matched:
            key = (dto.source, dto.external_id)
            if key in seen_keys:
                stats.skipped += 1
                continue
            if dto.url and dto.url in seen_urls:
                stats.skipped += 1
                continue

            seen_keys.add(key)
            if dto.url:
                seen_urls.add(dto.url)

            if dto.tags:
                stats.tagged += 1

            try:
                _, created = self.repo.upsert_fetched(dto, commit=False)
                if created:
                    stats.created += 1
                else:
                    stats.updated += 1
            except Exception as exc:
                msg = f"{source_name}/{dto.external_id}: save failed — {exc}"
                stats.errors.append(msg)
                logger.error("[collector] %s", msg)

        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            msg = f"{source_name}: batch commit failed — {exc}"
            stats.errors.append(msg)
            logger.error("[collector] %s", msg)

        return stats

    def _start_log(self, sources: list[str]) -> JobCollectorLog:
        row = JobCollectorLog(
            status="started",
            sources_json=json.dumps(sources),
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def _finish_log(
        self,
        row: JobCollectorLog,
        *,
        status: str,
        totals: dict,
        errors: list[str],
        duration_ms: int,
        message: str,
    ) -> None:
        row.status = status
        row.total_fetched = totals["fetched"]
        row.total_matched = totals["israel"]
        row.total_created = totals["created"]
        row.total_updated = totals["updated"]
        row.total_skipped = totals["skipped"]
        row.duration_ms = duration_ms
        row.errors_json = json.dumps(errors[:50])
        row.message = message
        self.db.commit()


# Backward-compatible aliases used by scheduler and legacy imports
SourceRefreshStats = SourceCollectStats
JobRefreshResult = CollectorResult


class JobFetchService(JobCollectorService):
    """Alias for backward compatibility."""

    async def refresh(self, sources: list[str] | None = None) -> CollectorResult:
        return await self.collect(sources)
