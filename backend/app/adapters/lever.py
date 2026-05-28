"""
Lever public Postings API adapter.

GET https://api.lever.co/v0/postings/{company}?mode=json
"""

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from app.adapters.base import JobBoardAdapter
from app.config import get_settings
from app.domain.job_dto import FetchedJobDTO
from app.services.job_filter import detect_category, detect_work_mode
from app.utils.text_helpers import strip_html

logger = logging.getLogger(__name__)

LEVER_API = "https://api.lever.co/v0/postings"

DEFAULT_COMPANIES: list[tuple[str, str]] = [
    ("walkme", "WalkMe"),
]


class LeverAdapter(JobBoardAdapter):
    name = "lever"

    def __init__(self, companies: list[tuple[str, str]] | None = None):
        settings = get_settings()
        if companies is not None:
            self._companies = companies
        elif settings.lever_company_slugs:
            self._companies = [
                (slug.strip(), slug.strip())
                for slug in settings.lever_company_slugs.split(",")
                if slug.strip()
            ]
        else:
            self._companies = DEFAULT_COMPANIES

    def board_identifiers(self) -> list[str]:
        return [c[0] for c in self._companies]

    async def fetch_jobs(self) -> list[FetchedJobDTO]:
        results, _ = await self.fetch_jobs_safe()
        return results

    async def fetch_jobs_safe(self) -> tuple[list[FetchedJobDTO], list[str]]:
        results: list[FetchedJobDTO] = []
        errors: list[str] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            async def _fetch_one(slug: str, company_name: str) -> None:
                try:
                    batch = await asyncio.wait_for(
                        self._fetch_company(client, slug, company_name),
                        timeout=45.0,
                    )
                    results.extend(batch)
                    logger.info("[lever] %s: fetched %s jobs", slug, len(batch))
                except asyncio.TimeoutError:
                    msg = f"{slug}: timed out after 45s"
                    errors.append(msg)
                    logger.error("[lever] %s", msg)
                except Exception as exc:
                    msg = f"{slug}: {exc}"
                    errors.append(msg)
                    logger.error("[lever] %s", msg)

            await asyncio.gather(
                *[_fetch_one(slug, name) for slug, name in self._companies]
            )

        return results, errors

    async def _fetch_company(
        self,
        client: httpx.AsyncClient,
        slug: str,
        company_name: str,
    ) -> list[FetchedJobDTO]:
        url = f"{LEVER_API}/{slug}"
        resp = await client.get(url, params={"mode": "json"})
        resp.raise_for_status()
        items = resp.json()
        if not isinstance(items, list):
            return []

        dtos: list[FetchedJobDTO] = []
        for item in items:
            dto = self._normalize(item, company_name, slug)
            if dto:
                dtos.append(dto)
        return dtos

    def _normalize(self, item: dict, company_name: str, slug: str) -> FetchedJobDTO | None:
        title = (item.get("text") or "").strip()
        if not title:
            return None

        categories = item.get("categories") or {}
        location = categories.get("location") or categories.get("allLocations") or "Remote"
        if isinstance(location, list):
            location = ", ".join(location)

        plain = item.get("descriptionPlain") or ""
        html = item.get("description") or ""
        description = plain or strip_html(html) or title
        work_mode = detect_work_mode(str(location), description)
        category = detect_category(title, description)
        skills: list[str] = []  # filled by normalize_collected_job tag extraction

        created = item.get("createdAt")
        posted_at = None
        if created:
            try:
                posted_at = datetime.fromtimestamp(created / 1000, tz=timezone.utc)
            except (TypeError, ValueError, OSError):
                posted_at = datetime.now(timezone.utc)

        job_id = str(item.get("id", ""))
        return FetchedJobDTO(
            external_id=f"{slug}:{job_id}",
            source="lever",
            title=title,
            company=company_name,
            location=str(location),
            description=description[:8000],
            category=category,
            work_mode=work_mode,
            url=item.get("hostedUrl") or item.get("applyUrl"),
            requirements=[description[:300]] if description else [],
            skills=skills,
            employment_type="Full-time",
            language="en",
            posted_at=posted_at,
        )
