"""
Greenhouse Job Board API adapter.

Public API docs: https://developers.greenhouse.io/job-board.html
GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
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

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards"

# Israeli / global-tech boards on Greenhouse (override via env)
DEFAULT_BOARDS: list[tuple[str, str]] = [
    ("riskified", "Riskified"),
    ("taboola", "Taboola"),
    ("similarweb", "Similarweb"),
    ("jfrog", "JFrog"),
    ("fireblocks", "Fireblocks"),
]


class GreenhouseAdapter(JobBoardAdapter):
    name = "greenhouse"

    def __init__(self, boards: list[tuple[str, str]] | None = None):
        settings = get_settings()
        if boards is not None:
            self._boards = boards
        elif settings.greenhouse_board_tokens:
            self._boards = [
                (token.strip(), token.strip())
                for token in settings.greenhouse_board_tokens.split(",")
                if token.strip()
            ]
        else:
            self._boards = DEFAULT_BOARDS

    def board_identifiers(self) -> list[str]:
        return [b[0] for b in self._boards]

    async def fetch_jobs(self) -> list[FetchedJobDTO]:
        results: list[FetchedJobDTO] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for board_token, company_name in self._boards:
                try:
                    batch = await self._fetch_board(client, board_token, company_name)
                    results.extend(batch)
                    logger.info("[greenhouse] %s: fetched %s jobs", board_token, len(batch))
                except Exception as exc:
                    logger.error("[greenhouse] %s failed: %s", board_token, exc)
                    raise
        return results

    async def fetch_jobs_safe(self) -> tuple[list[FetchedJobDTO], list[str]]:
        """Fetch all boards concurrently; collect errors without aborting."""
        results: list[FetchedJobDTO] = []
        errors: list[str] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            async def _fetch_one(board_token: str, company_name: str) -> None:
                try:
                    batch = await asyncio.wait_for(
                        self._fetch_board(client, board_token, company_name),
                        timeout=45.0,
                    )
                    results.extend(batch)
                    logger.info("[greenhouse] %s: fetched %s jobs", board_token, len(batch))
                except asyncio.TimeoutError:
                    msg = f"{board_token}: timed out after 45s"
                    errors.append(msg)
                    logger.error("[greenhouse] %s", msg)
                except Exception as exc:
                    msg = f"{board_token}: {exc}"
                    errors.append(msg)
                    logger.error("[greenhouse] %s", msg)

            await asyncio.gather(
                *[_fetch_one(token, name) for token, name in self._boards]
            )

        return results, errors

    async def _fetch_board(
        self,
        client: httpx.AsyncClient,
        board_token: str,
        company_name: str,
    ) -> list[FetchedJobDTO]:
        url = f"{GREENHOUSE_API}/{board_token}/jobs"
        resp = await client.get(url, params={"content": "true"})
        resp.raise_for_status()
        payload = resp.json()
        jobs_raw = payload.get("jobs", [])

        dtos: list[FetchedJobDTO] = []
        for item in jobs_raw:
            dto = self._normalize(item, company_name, board_token)
            if dto:
                dtos.append(dto)
        return dtos

    def _normalize(self, item: dict, company_name: str, board_token: str) -> FetchedJobDTO | None:
        title = (item.get("title") or "").strip()
        if not title:
            return None

        location_obj = item.get("location") or {}
        location = location_obj.get("name") if isinstance(location_obj, dict) else str(location_obj or "")
        location = location or "Remote"

        html_content = item.get("content") or ""
        description = strip_html(html_content) or title
        work_mode = detect_work_mode(location, description)
        category = detect_category(title, description)
        skills: list[str] = []  # filled by normalize_collected_job tag extraction

        updated = item.get("updated_at")
        posted_at = None
        if updated:
            try:
                posted_at = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            except ValueError:
                posted_at = datetime.now(timezone.utc)

        job_id = str(item.get("id", ""))
        return FetchedJobDTO(
            external_id=f"{board_token}:{job_id}",
            source="greenhouse",
            title=title,
            company=company_name,
            location=location,
            description=description[:8000],
            category=category,
            work_mode=work_mode,
            url=item.get("absolute_url"),
            requirements=[description[:300]] if description else [],
            skills=skills,
            employment_type="Full-time",
            language="en",
            posted_at=posted_at,
        )
