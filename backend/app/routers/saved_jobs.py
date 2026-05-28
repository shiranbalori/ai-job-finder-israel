"""Saved job bookmarks — scoped to authenticated user."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.job import Job
from app.models.saved_job import SavedJob
from app.models.user import User
from app.schemas.common import SavedJobResponse
from app.utils.serializers import job_to_response

router = APIRouter(prefix="/api/saved-jobs", tags=["saved-jobs"])


@router.get("", response_model=list[SavedJobResponse])
def list_saved_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(SavedJob)
        .filter(SavedJob.user_id == current_user.id)
        .options(joinedload(SavedJob.job))
        .order_by(SavedJob.created_at.desc())
        .all()
    )
    return [
        SavedJobResponse(
            id=r.id,
            job_id=r.job_id,
            created_at=r.created_at,
            job=job_to_response(r.job) if r.job else None,
        )
        for r in rows
    ]


@router.post("/{job_id}", response_model=SavedJobResponse)
def save_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    existing = (
        db.query(SavedJob)
        .filter(SavedJob.user_id == current_user.id, SavedJob.job_id == job_id)
        .first()
    )
    if existing:
        return SavedJobResponse(
            id=existing.id,
            job_id=existing.job_id,
            created_at=existing.created_at,
            job=job_to_response(job),
        )

    row = SavedJob(user_id=current_user.id, job_id=job_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return SavedJobResponse(
        id=row.id,
        job_id=row.job_id,
        created_at=row.created_at,
        job=job_to_response(job),
    )


@router.delete("/{job_id}")
def unsave_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(SavedJob)
        .filter(SavedJob.user_id == current_user.id, SavedJob.job_id == job_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Saved job not found.")
    db.delete(row)
    db.commit()
    return {"message": "Job removed from saved list."}
