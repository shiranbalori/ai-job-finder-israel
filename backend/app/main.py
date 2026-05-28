"""
AI Job Finder Israel — FastAPI backend entry point.

Run from the `backend/` folder:
    python run.py
    # or
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Interactive docs: http://127.0.0.1:8000/docs
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, log_db_startup, log_smtp_startup
from app.database import DATABASE_URL, init_db
from app.db_utils import database_label
from app.routers import auth, cv, demo, health, jobs, matches, saved_jobs, settings as settings_router
from app.scheduler import start_scheduler, stop_scheduler
from app.seed.seed_db import seed_jobs, seed_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: create SQLite tables, seed demo jobs, optional external job fetch.
    """
    settings = get_settings()
    log_db_startup()
    log_smtp_startup()
    init_db()
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        seed_jobs(db)
        seed_settings(db)
        from app.models.job import Job

        demo_count = db.query(Job).filter(Job.is_demo == True).count()  # noqa: E712
        db_label = database_label(DATABASE_URL)
        logger.info("Database ready (%s) — %s demo jobs seeded.", db_label, demo_count)

        if settings.job_fetch_on_startup:
            from app.services.job_collector_service import JobCollectorService

            result = await JobCollectorService(db).collect()
            logger.info(
                "Startup job fetch: fetched=%s israel=%s excluded=%s created=%s updated=%s",
                result.total_fetched,
                result.total_israel,
                result.total_excluded,
                result.total_created,
                result.total_updated,
            )
        else:
            real_count = db.query(Job).filter(Job.is_demo == False).count()  # noqa: E712
            logger.info(
                "Real jobs in DB: %s (POST /api/jobs/refresh to fetch from Greenhouse/Lever)",
                real_count,
            )
    finally:
        db.close()

    start_scheduler()
    yield
    stop_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="""
## AI Job Finder Israel API

Portfolio backend for CV upload, mock AI extraction, job matching, and daily email digest.

| Feature | Endpoint |
|---------|----------|
| Health | `GET /health` |
| Upload CV | `POST /api/cv/upload` |
| Extract CV | `POST /api/cv/extract` |
| Mock jobs | `GET /api/jobs/mock` |
| Job details | `GET /api/jobs/{id}` |
| Calculate match | `POST /api/matches/calculate` |
| Preferences | `PUT /api/preferences` |
| Daily email | `POST /api/email/daily` |

**AI mode:** set `AI_PROVIDER=mock` in `.env` (default) — no API keys required.
        """,
        version="1.0.0",
        lifespan=lifespan,
    )
    cors_kwargs: dict = {
        "allow_origins": settings.cors_origin_list,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
    if settings.cors_origin_regex.strip():
        cors_kwargs["allow_origin_regex"] = settings.cors_origin_regex.strip()
    app.add_middleware(CORSMiddleware, **cors_kwargs)

    # Register routers (order does not matter — paths are unique)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(cv.router)
    app.include_router(jobs.router)
    app.include_router(matches.router)
    app.include_router(saved_jobs.router)
    app.include_router(settings_router.router)
    app.include_router(demo.router)

    return app


app = create_app()
