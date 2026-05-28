"""
Demo Mode API — instant portfolio demo without API keys or CV upload.

POST /api/demo/activate  → fake CV + Israeli jobs + curated match scores
POST /api/demo/deactivate
GET  /api/demo/status    → current demo state
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.cv_profile import CVProfile
from app.models.user_settings import UserSettings
from app.schemas.common import DemoActivateResponse
from app.services.demo_service import activate_full_demo
from app.seed.demo_data import DEMO_CV

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("/activate", response_model=DemoActivateResponse)
async def activate_demo(db: Session = Depends(get_db)):
    """
    **Full Demo Mode** — loads a demo AI/Data candidate profile and 10 Israeli tech jobs
    with curated match scores, reasons, and missing skills. No API keys required.
    """
    result = activate_full_demo(db)
    return DemoActivateResponse(
        cv_profile=result["cv_profile"],
        matches=result["matches"],
        stats=result["stats"],
        message=result["message"],
    )


@router.post("/deactivate")
def deactivate_demo(db: Session = Depends(get_db)):
    settings = db.query(UserSettings).first()
    if settings:
        settings.demo_mode = False
        db.commit()
    return {"message": "Demo mode deactivated.", "demo_mode": False}


@router.get("/status")
def demo_status(db: Session = Depends(get_db)):
    """Check whether demo mode is active and if demo CV exists."""
    settings = db.query(UserSettings).first()
    demo_cv = db.query(CVProfile).filter(CVProfile.is_demo == True).first()  # noqa: E712
    return {
        "demo_mode": settings.demo_mode if settings else False,
        "demo_cv_loaded": demo_cv is not None,
        "demo_profile_name": DEMO_CV["full_name"] if demo_cv else None,
        "requires_api_keys": False,
    }
