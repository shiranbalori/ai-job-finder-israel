"""
Job fetch service — backward-compatible alias for JobCollectorService.

Use job_collector_service.JobCollectorService for new code.
"""

from app.services.job_collector_service import (
    ADAPTER_REGISTRY,
    DEFAULT_SOURCES,
    CollectorResult,
    JobCollectorService,
    JobFetchService,
    JobRefreshResult,
    SourceCollectStats,
    SourceRefreshStats,
)

__all__ = [
    "ADAPTER_REGISTRY",
    "DEFAULT_SOURCES",
    "CollectorResult",
    "JobCollectorService",
    "JobFetchService",
    "JobRefreshResult",
    "SourceCollectStats",
    "SourceRefreshStats",
]
