"""Job search over SQLite (demo + fetched)."""

from sqlalchemy.orm import Session

from app.models.job import Job
from app.repositories.job_repository import JobRepository


class JobSearchService:
    def __init__(self, db: Session):
        self.repo = JobRepository(db)

    def search(
        self,
        *,
        q: str | None = None,
        category: str | None = None,
        language: str | None = None,
        work_mode: str | None = None,
        source: str | None = None,
        tag: str | None = None,
        include_demo: bool = False,
        demo_only: bool = False,
        israel_only: bool = True,
        limit: int = 100,
    ) -> list[Job]:
        return self.repo.search(
            search=q,
            category=category,
            language=language,
            work_mode=work_mode,
            source=source,
            tag=tag,
            include_demo=include_demo,
            demo_only=demo_only,
            israel_only=israel_only,
            limit=limit,
        )
