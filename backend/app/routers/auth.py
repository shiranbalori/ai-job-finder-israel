"""User registration, login, and profile."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import TokenResponse, UserRegister, UserResponse
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_user_with_settings,
    normalize_email,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """Create a new user account with default email settings."""
    email = normalize_email(payload.email)
    logger.info("Register attempt email=%s", email)
    try:
        user = create_user_with_settings(
            db,
            email=email,
            password=payload.password,
            full_name=payload.full_name,
        )
    except ValueError as exc:
        logger.warning("Register rejected email=%s reason=%s", email, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    token = create_access_token(user_id=user.id, email=user.email)
    logger.info("Register success user_id=%s email=%s", user.id, user.email)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with email (username field) and password."""
    email = normalize_email(form.username)
    logger.info("Login attempt email=%s", email)
    user = authenticate_user(db, email, form.password)
    if not user:
        logger.warning("Login failed email=%s", email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user_id=user.id, email=user.email)
    logger.info("Login success user_id=%s email=%s", user.id, user.email)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user profile."""
    logger.debug("Profile fetch user_id=%s email=%s", current_user.id, current_user.email)
    return UserResponse.model_validate(current_user)


@router.post("/logout")
def logout():
    """Client should discard JWT — stateless logout."""
    logger.info("Logout requested (client-side token discard)")
    return {"message": "Logged out successfully."}
