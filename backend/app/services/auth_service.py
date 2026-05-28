"""Password hashing and JWT token helpers."""

import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.user import User
from app.models.user_settings import UserSettings

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed or not hashed.startswith("$2"):
        logger.warning("Password verify skipped: invalid hash format")
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        logger.warning("Password verify failed: %s", exc)
        return False


def create_access_token(*, user_id: int, email: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": int(expire.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)
    logger.debug("JWT created user_id=%s exp=%s", user_id, payload["exp"])
    return token


def decode_access_token(token: str) -> dict | None:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as exc:
        logger.info("JWT decode failed: %s", exc)
        return None


def get_user_by_email(db: Session, email: str) -> User | None:
    normalized = normalize_email(email)
    return db.query(User).filter(User.email == normalized).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()  # noqa: E712


def create_user_with_settings(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str | None = None,
) -> User:
    normalized = normalize_email(email)
    if get_user_by_email(db, normalized):
        raise ValueError("Email already registered.")

    user = User(
        email=normalized,
        hashed_password=hash_password(password),
        full_name=full_name.strip() if full_name else None,
    )
    db.add(user)
    db.flush()

    settings = UserSettings(
        user_id=user.id,
        email=normalized,
        ui_language="en",
    )
    db.add(settings)
    db.commit()
    db.refresh(user)
    db.refresh(settings)
    logger.info(
        "User saved id=%s email=%s settings_id=%s hash_len=%s",
        user.id,
        user.email,
        settings.id,
        len(user.hashed_password),
    )
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    normalized = normalize_email(email)
    user = get_user_by_email(db, normalized)
    if not user:
        logger.info("Auth failed: no user for email=%s", normalized)
        return None
    if not user.is_active:
        logger.info("Auth failed: inactive user id=%s email=%s", user.id, user.email)
        return None
    if not verify_password(password, user.hashed_password):
        logger.info("Auth failed: bad password for user id=%s email=%s", user.id, user.email)
        return None
    logger.info("Auth success user id=%s email=%s", user.id, user.email)
    return user
