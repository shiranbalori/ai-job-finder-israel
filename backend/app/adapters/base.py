"""Base protocol for job board adapters."""

from abc import ABC, abstractmethod

from app.domain.job_dto import FetchedJobDTO


class JobBoardAdapter(ABC):
    """Fetch normalized jobs from a public job board API."""

    name: str

    @abstractmethod
    async def fetch_jobs(self) -> list[FetchedJobDTO]:
        """Return all raw-normalized jobs before filtering."""

    @abstractmethod
    def board_identifiers(self) -> list[str]:
        """Configured company/board slugs for logging."""
