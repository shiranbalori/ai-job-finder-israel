"""Database persistence for jobs with deduplication."""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.job_dto import FetchedJobDTO
from app.models.job import Job
from app.utils.json_helpers import to_json_list

logger = logging.getLogger(__name__)


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_source_id(self, source: str, external_id: str) -> Job | None:
        return (
            self.db.query(Job)
            .filter(Job.source == source, Job.external_id == external_id)
            .first()
        )

    def find_by_url(self, url: str | None) -> Job | None:
        if not url:
            return None
        return self.db.query(Job).filter(Job.url == url).first()

    def upsert_fetched(self, dto: FetchedJobDTO, *, commit: bool = True) -> tuple[Job, bool]:
        """
        Insert or update a fetched job. Returns (job, created).
        Dedup: (source, external_id) primary; url secondary.
        """
        existing = self.find_by_source_id(dto.source, dto.external_id)
        if not existing and dto.url:
            existing = self.find_by_url(dto.url)

        if existing:
            self._apply_dto(existing, dto)
            existing.is_active = True
            existing.is_demo = False
            if commit:
                self.db.commit()
                self.db.refresh(existing)
            else:
                self.db.flush()
            return existing, False

        job = Job(
            title=dto.title,
            company=dto.company,
            location=dto.location,
            description=dto.description,
            requirements_json=to_json_list(dto.requirements),
            skills_json=to_json_list(dto.skills),
            tags_json=to_json_list(dto.tags),
            category=dto.category,
            employment_type=dto.employment_type,
            url=dto.url,
            language=dto.language,
            work_mode=dto.work_mode,
            is_israel=dto.is_israel,
            location_tag=dto.location_tag,
            source=dto.source,
            external_id=dto.external_id,
            is_demo=False,
            is_active=True,
            posted_at=dto.posted_at or datetime.utcnow(),
        )
        self.db.add(job)
        if commit:
            self.db.commit()
            self.db.refresh(job)
        else:
            self.db.flush()
        logger.debug("Created job %s from %s", job.id, dto.source)
        return job, True

    def _apply_dto(self, job: Job, dto: FetchedJobDTO) -> None:
        job.title = dto.title
        job.company = dto.company
        job.location = dto.location
        job.description = dto.description
        job.requirements_json = to_json_list(dto.requirements)
        job.skills_json = to_json_list(dto.skills)
        job.tags_json = to_json_list(dto.tags)
        job.category = dto.category
        job.work_mode = dto.work_mode
        job.is_israel = dto.is_israel
        job.location_tag = dto.location_tag
        job.url = dto.url
        job.source = dto.source
        job.external_id = dto.external_id
        job.is_demo = False
        if dto.posted_at:
            job.posted_at = dto.posted_at

    def search(
        self,
        *,
        search: str | None = None,
        category: str | None = None,
        language: str | None = None,
        work_mode: str | None = None,
        source: str | None = None,
        tag: str | None = None,
        include_demo: bool = False,
        demo_only: bool = False,
        israel_only: bool = False,
        limit: int = 100,
    ) -> list[Job]:
        q = self.db.query(Job).filter(Job.is_active == True)  # noqa: E712

        if demo_only:
            q = q.filter(Job.is_demo == True)  # noqa: E712
        elif not include_demo:
            q = q.filter(Job.is_demo == False)  # noqa: E712

        if israel_only:
            q = q.filter(Job.is_israel == True)  # noqa: E712

        if source:
            q = q.filter(Job.source == source)
        if category:
            q = q.filter(Job.category.ilike(f"%{category}%"))
        if language:
            q = q.filter(Job.language == language)
        if work_mode:
            q = q.filter(Job.work_mode == work_mode)
        if tag:
            q = q.filter(Job.tags_json.ilike(f"%{tag}%"))
        if search:
            term = f"%{search}%"
            q = q.filter(
                (Job.title.ilike(term))
                | (Job.company.ilike(term))
                | (Job.description.ilike(term))
                | (Job.location.ilike(term))
            )

        return q.order_by(Job.posted_at.desc()).limit(limit).all()

    def deactivate_non_israel_fetched(self) -> int:
        """Hide previously saved fetched jobs that fail Israel location rules."""
        updated = (
            self.db.query(Job)
            .filter(Job.is_demo == False, Job.is_israel == False)  # noqa: E712
            .update({Job.is_active: False}, synchronize_session=False)
        )
        self.db.commit()
        if updated:
            logger.info("Deactivated %s non-Israel fetched jobs.", updated)
        return updated

    def count_by_source(self) -> dict[str, int]:
        rows = self.db.query(Job.source, Job.id).filter(Job.is_active == True).all()  # noqa: E712
        counts: dict[str, int] = {}
        for source, _ in rows:
            counts[source] = counts.get(source, 0) + 1
        return counts
