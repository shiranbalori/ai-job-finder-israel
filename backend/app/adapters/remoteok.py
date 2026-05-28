"""
RemoteOK public API adapter.

GET https://remoteok.com/api — returns JSON array (first item is metadata).
"""

import logging
from datetime import datetime, timezone

import httpx

from app.adapters.base import JobBoardAdapter
from app.domain.job_dto import FetchedJobDTO
from app.services.job_filter import detect_category, detect_work_mode
from app.utils.text_helpers import strip_html

logger = logging.getLogger(__name__)

REMOTEOK_API = "https://remoteok.com/api"
USER_AGENT = "AI-Job-Finder-Israel/1.0 (portfolio; job aggregator)"


class RemoteOKAdapter(JobBoardAdapter):
    name = "remoteok"

    def board_identifiers(self) -> list[str]:
        return ["remoteok.com"]

    async def fetch_jobs(self) -> list[FetchedJobDTO]:
        results, _ = await self.fetch_jobs_safe()
        return results

    async def fetch_jobs_safe(self) -> tuple[list[FetchedJobDTO], list[str]]:
        errors: list[str] = []
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.get(
                    REMOTEOK_API,
                    headers={"User-Agent": USER_AGENT},
                )
                resp.raise_for_status()
                payload = resp.json()
        except Exception as exc:
            msg = f"remoteok: {exc}"
            logger.error("[remoteok] %s", msg)
            return [], [msg]

        if not isinstance(payload, list):
            return [], ["remoteok: unexpected response format"]

        dtos: list[FetchedJobDTO] = []
        for item in payload:
            if not isinstance(item, dict) or "id" not in item:
                continue
            dto = self._normalize(item)
            if dto:
                dtos.append(dto)

        logger.info("[remoteok] fetched %s jobs", len(dtos))
        return dtos, errors

    def _normalize(self, item: dict) -> FetchedJobDTO | None:
        title = (item.get("position") or item.get("title") or "").strip()
        company = (item.get("company") or "").strip()
        if not title or not company:
            return None

        location = (item.get("location") or "Remote").strip()
        tags = item.get("tags") or []
        if isinstance(tags, list):
            tag_str = " ".join(str(t) for t in tags)
            if "israel" in tag_str.lower() and "israel" not in location.lower():
                location = f"Remote Israel — {location}".strip(" —")

        description = strip_html(item.get("description") or "") or title
        if tags:
            description = f"{description}\nTags: {', '.join(str(t) for t in tags[:12])}"

        work_mode = detect_work_mode(location, description)
        category = detect_category(title, description)
        skills: list[str] = []
        if isinstance(tags, list):
            skills = [str(t) for t in tags if len(str(t)) > 1][:8]

        posted_at = None
        raw_date = item.get("date") or item.get("epoch")
        if raw_date:
            try:
                if isinstance(raw_date, (int, float)):
                    posted_at = datetime.fromtimestamp(int(raw_date), tz=timezone.utc)
                else:
                    posted_at = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00"))
            except (ValueError, OSError):
                posted_at = datetime.now(timezone.utc)

        job_id = str(item.get("id", ""))
        url = item.get("url") or item.get("apply_url")
        if url and not str(url).startswith("http"):
            url = f"https://remoteok.com/remote-jobs/{job_id}"

        return FetchedJobDTO(
            external_id=f"remoteok:{job_id}",
            source="remoteok",
            title=title,
            company=company,
            location=location,
            description=description[:8000],
            category=category,
            work_mode=work_mode or "remote",
            url=url,
            requirements=[description[:300]] if description else [],
            skills=skills,
            employment_type="Full-time",
            language="en",
            posted_at=posted_at,
        )
