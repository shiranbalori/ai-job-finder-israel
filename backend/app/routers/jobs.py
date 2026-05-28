"""
Job listing endpoints — demo seed jobs + collected Greenhouse/Lever/RemoteOK jobs.

| Method | Path                      | Description                         |
|--------|---------------------------|-------------------------------------|
| GET    | /api/jobs/mock            | Demo seed jobs only (Demo Mode)     |
| POST   | /api/jobs/refresh         | Collect from Greenhouse/Lever/RemoteOK |
| GET    | /api/jobs/collector/logs  | Recent collector run audit logs     |
| GET    | /api/jobs/search          | Search with filters                 |
| GET    | /api/jobs                 | List jobs (real by default)         |
| GET    | /api/jobs/categories      | Distinct categories                 |
| GET    | /api/jobs/{job_id}        | Job details                         |
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.models.job_collector_log import JobCollectorLog
from app.models.job_match import JobMatch
from app.repositories.job_repository import JobRepository
from app.schemas.common import JobCollectorLogResponse, JobRefreshResponse, JobResponse, JobSearchResponse, JobSourceStats
from app.seed.seed_db import seed_jobs
from app.services.job_collector_service import JobCollectorService
from app.services.job_search_service import JobSearchService
from app.utils.serializers import job_to_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/mock", response_model=list[JobResponse])
def get_mock_jobs(
    db: Session = Depends(get_db),
    category: str | None = None,
    language: str | None = None,
    search: str | None = None,
    reseed: bool = Query(False, description="Force re-insert demo jobs if empty"),
):
    """Demo Mode — seeded Israeli AI/Data jobs (source=seed, is_demo=true)."""
    count = db.query(Job).filter(Job.is_demo == True).count()  # noqa: E712
    if count == 0 or reseed:
        seed_jobs(db, force=reseed)

    repo = JobRepository(db)
    jobs = repo.search(
        search=search,
        category=category,
        language=language,
        demo_only=True,
        include_demo=True,
    )
    return [job_to_response(j) for j in jobs]


@router.post("/refresh", response_model=JobRefreshResponse)
async def refresh_jobs(
    db: Session = Depends(get_db),
    sources: str = Query(
        "greenhouse,lever,remoteok",
        description="Comma-separated sources: greenhouse, lever, remoteok",
    ),
):
    """
    **Collect real AI/Data jobs** from Greenhouse, Lever, and RemoteOK.

    Pipeline: fetch → normalize → tag extraction → filter → dedupe → save.
    Tags extracted: Python, LLM, RAG, NLP, SQL, LangChain, GenAI.
    """
    source_list = [s.strip() for s in sources.split(",") if s.strip()]
    collector = JobCollectorService(db)

    try:
        result = await collector.collect(source_list)
    except Exception as exc:
        logger.exception("[jobs/refresh] collector failed")
        raise HTTPException(
            status_code=503,
            detail=f"Job collection failed: {exc}",
        ) from exc

    if not result.success and result.total_fetched == 0:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "All job sources failed",
                "errors": result.errors,
            },
        )

    response = JobRefreshResponse(
        total_fetched=result.total_fetched,
        total_israel=result.total_israel,
        total_excluded=result.total_excluded,
        total_matched=result.total_matched,
        total_created=result.total_created,
        total_updated=result.total_updated,
        total_skipped=result.total_skipped,
        total_tagged=result.total_tagged,
        duration_ms=result.duration_ms,
        success=result.success,
        partial=result.partial,
        log_id=result.log_id,
        errors=result.errors,
        sources=[
            JobSourceStats(
                name=s.name,
                boards=s.boards,
                fetched=s.fetched,
                matched=s.matched,
                israel=s.israel,
                excluded=s.excluded,
                created=s.created,
                updated=s.updated,
                skipped=s.skipped,
                tagged=s.tagged,
                errors=s.errors,
            )
            for s in result.sources
        ],
        message=(
            f"Collected {result.total_fetched} jobs — {result.total_israel} matched, "
            f"{result.total_excluded} excluded, {result.total_tagged} tagged "
            f"({result.total_created} new, {result.total_updated} updated) "
            f"in {result.duration_ms}ms."
        ),
    )

    logger.info("[jobs/refresh] %s", response.message)
    return response


@router.get("/collector/logs", response_model=list[JobCollectorLogResponse])
def list_collector_logs(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    """Recent job collector runs (production audit trail)."""
    rows = (
        db.query(JobCollectorLog)
        .order_by(JobCollectorLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        JobCollectorLogResponse(
            id=r.id,
            status=r.status,
            sources=json.loads(r.sources_json or "[]"),
            total_fetched=r.total_fetched,
            total_matched=r.total_matched,
            total_created=r.total_created,
            total_updated=r.total_updated,
            total_skipped=r.total_skipped,
            duration_ms=r.duration_ms,
            errors=json.loads(r.errors_json or "[]"),
            message=r.message,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/search", response_model=JobSearchResponse)
def search_jobs(
    db: Session = Depends(get_db),
    q: str | None = Query(None, description="Search title, company, description, location"),
    category: str | None = None,
    language: str | None = None,
    work_mode: str | None = Query(None, description="remote | hybrid | onsite"),
    source: str | None = Query(None, description="greenhouse | lever | remoteok | seed"),
    tag: str | None = Query(None, description="AI/Data tag: Python, LLM, RAG, NLP, SQL, LangChain, GenAI"),
    include_demo: bool = Query(False),
    demo_only: bool = Query(False),
    israel_only: bool = Query(True, description="Israeli jobs only"),
    limit: int = Query(100, ge=1, le=500),
):
    """Search jobs with filters including AI/Data tags."""
    service = JobSearchService(db)
    jobs = service.search(
        q=q,
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
    return JobSearchResponse(items=[job_to_response(j) for j in jobs], total=len(jobs), query=q)


@router.get("/categories", response_model=list[str])
def list_categories(db: Session = Depends(get_db)):
    rows = db.query(Job.category).filter(Job.is_active == True).distinct().all()  # noqa: E712
    return sorted({r[0] for r in rows if r[0]})


@router.get("", response_model=list[JobResponse])
def list_jobs(
    db: Session = Depends(get_db),
    category: str | None = None,
    language: str | None = None,
    search: str | None = None,
    work_mode: str | None = None,
    source: str | None = None,
    tag: str | None = Query(None, description="Filter by AI/Data tag"),
    include_demo: bool = Query(False, description="Include demo seed jobs"),
    israel_only: bool = Query(True, description="Israeli jobs only"),
    min_score: float | None = None,
    cv_profile_id: int | None = None,
):
    """List active jobs. Real Mode defaults to collected Israeli jobs (excludes demo seed)."""
    repo = JobRepository(db)
    jobs = repo.search(
        search=search,
        category=category,
        language=language,
        work_mode=work_mode,
        source=source,
        tag=tag,
        include_demo=include_demo,
        demo_only=False,
        israel_only=israel_only,
    )

    if cv_profile_id is not None and min_score is not None:
        match_map = {
            m.job_id: m.match_score
            for m in db.query(JobMatch).filter(JobMatch.cv_profile_id == cv_profile_id).all()
        }
        jobs = [j for j in jobs if match_map.get(j.id, 0) >= min_score]

    return [job_to_response(j) for j in jobs]


@router.get("/{job_id}", response_model=JobResponse)
def get_job_details(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job_to_response(job)
